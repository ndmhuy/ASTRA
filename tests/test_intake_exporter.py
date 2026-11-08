import json
from pathlib import Path

import pytest
from docx import Document
from pydantic import ValidationError
from pypdf import PdfReader

from exam_baseline.core.hashing import digest
from exam_baseline.draft.models import ExamDraft
from exam_baseline.exporter import ExportReview, export, validate_export
from exam_baseline.intake import Intake, encode_intake

ROOT = Path(__file__).parents[1]


def _review(root):
    draft = ExamDraft.model_validate_json((root / "exam_draft.json").read_text("utf-8"))
    private = json.loads(
        (root.parent / "teacher_private" / f"{draft.draft_id}.json").read_text("utf-8")
    )
    return ExportReview(
        draft_id=draft.draft_id,
        revision=draft.revision,
        student_sha256=digest((root / "student_view.json").read_bytes()),
        reviewer="Fixture arithmetic review",
        approved=True,
        answers=private,
    )


@pytest.mark.parametrize("case", ["01_text", "02_graph", "03_geometry", "04_chart", "05_mixed"])
def test_export_five_fixtures(case, tmp_path):
    root = ROOT / "examples" / "mini" / case / "handoff"
    review = _review(root)
    review_path = tmp_path / "review.json"
    review_path.write_text(review.model_dump_json(), encoding="utf-8")
    output = tmp_path / "files"
    export(root, review_path, output)
    assert {p.name for p in output.iterdir()} == {
        "de_thi.docx",
        "de_thi.pdf",
        "dap_an.docx",
        "dap_an.pdf",
    }
    student_text = "\n".join(p.text for p in Document(output / "de_thi.docx").paragraphs)
    answer_text = "\n".join(p.text for p in Document(output / "dap_an.docx").paragraphs)
    draft = ExamDraft.model_validate_json((root / "exam_draft.json").read_text("utf-8"))
    for q in draft.exam.questions:
        assert q.stem in student_text
        assert review.answers[q.id].answer in answer_text
        assert review.answers[q.id].solution in answer_text
    assert "Đáp án:" not in student_text
    for name in ("de_thi", "dap_an"):
        pdf_text = "\n".join(
            page.extract_text() for page in PdfReader(output / f"{name}.pdf").pages
        )
        assert draft.exam.subject in pdf_text
        assert "Câu 1" in pdf_text
    if draft.figures:
        assert len(Document(output / "de_thi.docx").inline_shapes) == len(draft.figures)


def test_review_rejects_changes_and_missing_answer():
    root = ROOT / "examples/mini/01_text/handoff"
    draft = ExamDraft.model_validate_json((root / "exam_draft.json").read_text("utf-8"))
    review = _review(root)
    review.student_sha256 = "0" * 64
    with pytest.raises(ValueError, match="exact student exam"):
        validate_export(draft, root, review)
    review = _review(root)
    review.answers = {}
    with pytest.raises(ValueError, match="question IDs"):
        validate_export(draft, root, review)
    with pytest.raises(ValidationError):
        ExportReview.model_validate({**_review(root).model_dump(), "approved": False})


def test_intake_scope_policy():
    source = json.loads((ROOT / "examples/mini/01_text/input.json").read_text("utf-8"))
    matrix = source["request"]["matrix"]
    payload = {
        "chatbot": {
            "intent": "generate_exam",
            "grade": 7,
            "curriculum": "GDPT 2018",
            "textbook": "Kết nối tri thức",
            "textbook_year": 2025,
            "matrix": matrix,
            "exam_format": "quiz",
            "answer_format": "worked_solutions",
        },
        "rag": [
            {
                "id": "e1",
                "text": "Giải 2x + 3 = 7.",
                "role": "content_support",
                "source_title": "SGK Toán 7",
                "locator": "trang 12",
                "subject": "Toán",
                "grade": 7,
                "textbook": "Kết nối tri thức",
                "textbook_year": 2025,
                "topic_ids": ["math"],
            }
        ],
    }
    intake = Intake.model_validate(payload)
    assert encode_intake(intake).require_evidence
    payload["rag"][0]["grade"] = 8
    with pytest.raises(ValidationError, match="conflicts with exam scope"):
        Intake.model_validate(payload)
