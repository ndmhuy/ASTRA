"""Export a verified, explicitly reviewed mini draft to student and teacher files."""

import argparse
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Cm, Pt
from pydantic import Field, model_validator
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

from .core.hashing import digest
from .core.models import Model, QuestionType
from .draft.artifacts import private_artifact_path
from .draft.models import ExamDraft
from .draft.validation import verify_handoff


class ReviewedAnswer(Model):
    answer: str = Field(min_length=1)
    solution: str | None = Field(default=None, min_length=1)


class ExportReview(Model):
    schema_version: str = "export-review-v1"
    draft_id: str
    revision: int = Field(ge=1)
    student_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer: str = Field(min_length=1)
    approved: bool = Field(strict=True)
    answers: dict[str, ReviewedAnswer]

    @model_validator(mode="after")
    def approved_review(self):
        if self.schema_version != "export-review-v1" or not self.approved:
            raise ValueError("Explicit export review approval is required")
        return self


def validate_export(draft: ExamDraft, root: Path, review: ExportReview) -> None:
    errors = verify_handoff(draft, root)
    if errors:
        raise ValueError("Invalid handoff: " + ", ".join(e.code for e in errors))
    student_bytes = (root / "student_view.json").read_bytes()
    if (
        review.draft_id != draft.draft_id
        or review.revision != draft.revision
        or review.student_sha256 != digest(student_bytes)
    ):
        raise ValueError("Review does not match this exact student exam revision")
    ids = {q.id for q in draft.exam.questions}
    if len(ids) != len(draft.exam.questions) or ids != {q.id for q in draft.questions}:
        raise ValueError("Question metadata does not match student exam")
    if abs(sum(q.points for q in draft.exam.questions) - draft.exam.total_points) > 1e-6:
        raise ValueError("Question points do not sum to exam total")
    if set(review.answers) != ids:
        raise ValueError("Reviewed answers must match question IDs exactly")
    available_figures = {figure.visual_id for figure in draft.figures}
    if any(
        ref not in available_figures for metadata in draft.questions for ref in metadata.figure_refs
    ):
        raise ValueError("A referenced figure is missing")
    for q in draft.exam.questions:
        answer = review.answers[q.id].answer
        if q.question_type == QuestionType.MULTIPLE_CHOICE and answer not in q.choices:
            raise ValueError(f"Answer for {q.id} is not a choice key")
        if q.question_type == QuestionType.TRUE_FALSE and answer.casefold() not in {
            "true",
            "false",
        }:
            raise ValueError(f"Answer for {q.id} must be true or false")
    if any(q.stem_format == "latex" for q in draft.questions):
        raise ValueError("LaTeX stems need a math renderer before faithful PDF/DOCX export")
    texts = [draft.exam.title, draft.exam.instructions]
    for question in draft.exam.questions:
        texts.extend([question.stem, *question.choices.values()])
    for answer in review.answers.values():
        texts.extend([answer.answer, answer.solution or ""])
    if any("$" in value or re.search(r"\\[A-Za-z]+", value) for value in texts):
        raise ValueError("LaTeX math fragments need a math renderer before export")


def _sections(draft: ExamDraft, review: ExportReview, root: Path, answers: bool):
    exam = draft.exam
    yield ("title", "ĐÁP ÁN VÀ HƯỚNG DẪN GIẢI" if answers else exam.title, None)
    yield (
        "meta",
        f"{exam.subject} • {exam.duration_minutes} phút • {exam.total_points:g} điểm",
        None,
    )
    if not answers:
        yield ("body", exam.instructions, None)
    figure_map = {f.visual_id: f for f in draft.figures}
    meta_map = {q.id: q for q in draft.questions}
    passages = {p.start_question: p for p in exam.shared_passages}
    for index, question in enumerate(exam.questions, 1):
        if index in passages:
            passage = passages[index]
            yield (
                "body",
                f"Dùng thông tin sau cho câu {index}–{passage.end_question}: {passage.text}",
                None,
            )
        yield ("question", f"Câu {index} ({question.points:g} điểm). {question.stem}", None)
        if not answers:
            for key, choice in question.choices.items():
                yield ("body", f"{key}. {choice}", None)
            for visual_id in meta_map[question.id].figure_refs:
                yield ("image", "", root / figure_map[visual_id].path)
        else:
            result = review.answers[question.id]
            yield ("body", f"Đáp án: {result.answer}", None)
            if result.solution:
                yield ("body", f"Lời giải: {result.solution}", None)


def _docx(sections, output: Path) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Cm(2)
    section.left_margin = section.right_margin = Cm(2.2)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    for kind, content, image_path in sections:
        if kind == "image":
            doc.add_picture(str(image_path), width=Cm(12))
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(7 if kind == "question" else 4)
            if kind == "title":
                p.style = "Title"
                p.alignment = 1
            elif kind == "meta":
                p.alignment = 1
            if kind == "question":
                p.paragraph_format.keep_with_next = True
            p.add_run(content).bold = kind == "question"
    doc.save(output)


def _font() -> str:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont("ExamUnicode", str(path)))
            return "ExamUnicode"
    raise RuntimeError("A Unicode TTF font is needed for Vietnamese PDF output")


def _pdf(sections, output: Path) -> None:
    font = _font()
    styles = {
        "title": ParagraphStyle(
            "title", fontName=font, fontSize=15, leading=21, alignment=TA_CENTER, spaceAfter=12
        ),
        "meta": ParagraphStyle(
            "meta", fontName=font, fontSize=10, leading=16, alignment=TA_CENTER, spaceAfter=10
        ),
        "question": ParagraphStyle(
            "question",
            fontName=font,
            fontSize=11,
            leading=17,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.black,
        ),
        "body": ParagraphStyle("body", fontName=font, fontSize=10.5, leading=16, spaceAfter=5),
    }
    story = []
    for kind, content, image_path in sections:
        if kind == "image":
            reader = ImageReader(str(image_path))
            width, height = reader.getSize()
            target = min(410, width)
            story.append(Image(str(image_path), width=target, height=target * height / width))
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(escape(content).replace("\n", "<br/>"), styles[kind]))
    SimpleDocTemplate(
        str(output), pagesize=A4, leftMargin=55, rightMargin=55, topMargin=55, bottomMargin=55
    ).build(story)


def export(draft_root: Path, review_path: Path, output: Path) -> None:
    draft = ExamDraft.model_validate_json((draft_root / "exam_draft.json").read_text("utf-8"))
    review = ExportReview.model_validate_json(review_path.read_text("utf-8"))
    validate_export(draft, draft_root, review)
    output.mkdir(parents=True, exist_ok=False)
    for name, answers in (("de_thi", False), ("dap_an", True)):
        sections = list(_sections(draft, review, draft_root, answers))
        _docx(sections, output / f"{name}.docx")
        _pdf(sections, output / f"{name}.pdf")
        _audit_files(sections, output / f"{name}.docx", output / f"{name}.pdf")


def _audit_files(sections, docx_path: Path, pdf_path: Path) -> None:
    """Reject lost text or figures after serialization in either output format."""
    doc = Document(docx_path)
    doc_text = "\n".join(p.text for p in doc.paragraphs)
    pdf = PdfReader(pdf_path)
    pdf_text = "\n".join(page.extract_text() for page in pdf.pages)
    expected_images = sum(kind == "image" for kind, _, _ in sections)
    if len(doc.inline_shapes) != expected_images:
        raise ValueError("DOCX figure count differs from source")
    pdf_images = sum(len(page.images) for page in pdf.pages)
    if pdf_images < expected_images:
        raise ValueError("PDF figure count differs from source")
    for kind, content, _ in sections:
        if kind == "image":
            continue
        if content not in doc_text or content not in pdf_text:
            raise ValueError(f"Exported text missing from PDF or DOCX: {content[:40]}")


def prepare_review(draft_root: Path, output: Path) -> None:
    """Copy provisional Composer answers into an unapproved, editable review file."""
    draft = ExamDraft.model_validate_json((draft_root / "exam_draft.json").read_text("utf-8"))
    if verify_handoff(draft, draft_root):
        raise ValueError("Draft handoff is invalid")
    private_path = private_artifact_path(draft_root, draft.draft_id)
    proposed = json.loads(private_path.read_text("utf-8"))
    payload = {
        "schema_version": "export-review-v1",
        "draft_id": draft.draft_id,
        "revision": draft.revision,
        "student_sha256": digest((draft_root / "student_view.json").read_bytes()),
        "reviewer": "",
        "approved": False,
        "answers": proposed,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--prepare-review", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prepare_review:
        if args.review:
            parser.error("choose --review or --prepare-review")
        prepare_review(args.draft, args.prepare_review)
        return 0
    if not args.review:
        parser.error("--review is required for export")
    if not args.output:
        parser.error("--output is required for export")
    if args.output.exists():
        parser.error("output directory already exists")
    export(args.draft, args.review, args.output)
    print(
        json.dumps({"files": [str(p) for p in sorted(args.output.iterdir())]}, ensure_ascii=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
