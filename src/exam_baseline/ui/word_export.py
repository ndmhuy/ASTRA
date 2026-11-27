"""Convert an approved student paper to editable Word content."""

import re
import subprocess
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from pypandoc import get_pandoc_path

from exam_baseline.thpt.content import content_latex
from exam_baseline.thpt.contract_artifacts import render_assets
from exam_baseline.thpt.fonts import DEFAULT_FONT_PROFILE
from exam_baseline.thpt.subjects import SECTION_SPEC

_HEADINGS = {
    "P1": "Phần I. Trắc nghiệm nhiều lựa chọn",
    "P2": "Phần II. Trắc nghiệm đúng/sai",
    "P3": "Phần III. Trả lời ngắn",
    "TV": "Phần 1. Sử dụng ngôn ngữ · 1.1. Tiếng Việt",
    "TA": "Phần 1. Sử dụng ngôn ngữ · 1.2. Tiếng Anh",
    "TO": "Phần 2. Toán học",
    "LOGIC": "Phần 3. Tư duy khoa học · 3.1. Logic, phân tích số liệu",
    "SCIENCE": "Phần 3. Tư duy khoa học · 3.2. Suy luận khoa học",
}
_BLANK = re.compile(r"\\underline\{\\hspace\{[0-3](?:\.\d{1,2})?cm\}\}")
_QUESTION_CONTINUES = re.compile(r"^(?:Câu \d+\.|[A-C]\. |[a-c]\) )")


def _student_latex(paper: dict, figures: dict) -> str:
    title = content_latex(paper["title"])
    body = [
        r"\documentclass{article}",
        r"\usepackage{amsmath,amssymb,graphicx}",
        rf"\title{{{title}}}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        f"Thời gian: {paper['durationMinutes']} phút",
        "Họ và tên: .......................................................... "
        "Lớp: ....................",
    ]
    passages = {passage["id"]: passage for passage in paper.get("passages", [])}
    previous_part = previous_passage = previous_instruction = None
    for question in paper["questions"]:
        part = question["part"]
        if part != previous_part:
            body.append(r"\section*{" + _HEADINGS[part] + "}")
            if part in SECTION_SPEC:
                body.append(content_latex(SECTION_SPEC[part][2]))
        instruction = question.get("groupInstruction")
        if instruction and instruction != previous_instruction:
            body.append(r"\textbf{" + content_latex(instruction) + "}")
        passage_id = question.get("passageId")
        if passage_id != previous_passage and (passage := passages.get(passage_id)):
            for field in ("instruction", "heading", "text"):
                if value := passage.get(field):
                    text = content_latex(value)
                    body.append(text if field == "text" else r"\textbf{" + text + "}")
            if table := passage.get("table"):
                columns = table["columns"]
                rows = [" & ".join(map(content_latex, row)) for row in [columns, *table["rows"]]]
                body.append(
                    r"\begin{tabular}{"
                    + "l" * len(columns)
                    + "}\n"
                    + (r" \\" + "\n").join(rows)
                    + "\n"
                    + r"\end{tabular}"
                )
        previous_part, previous_passage, previous_instruction = part, passage_id, instruction

        stable_id = question["stableId"]
        number = stable_id.rsplit("-", 1)[-1] if part.startswith("P") else question["id"]
        body.append(rf"\textbf{{Câu {number}.}} " + content_latex(question["stem"]))
        if figure := figures.get(stable_id.lower()):
            body.append(r"\includegraphics[width=0.75\textwidth]{" + figure["path"] + "}")
        body.extend(f"{label}. {choice}" for label, choice in question["choices"].items() if choice)
        body.extend(
            f"{label}) " + content_latex(statement["text"])
            for label, statement in zip("abcd", question.get("statements", []), strict=False)
        )
        if question["questionType"] == "short_answer":
            body.append("Trả lời: ........................................")
    return _BLANK.sub(lambda _: r"\_\_\_\_\_\_\_\_", "\n\n".join([*body, r"\end{document}"]))


def export_student_word(paper, job, *, compiler, timeout, cache_directory: Path) -> bytes:
    # Keep every input and output private to this request, including all figure asset paths.
    with TemporaryDirectory(prefix="astra-word-") as temp:
        directory = Path(temp)
        figures = render_assets(
            directory,
            job["drawings"]["drawings"],
            font_profile=job["nativeRequest"].get("font_profile", DEFAULT_FONT_PROFILE),
            compiler=compiler,
            timeout=timeout,
            cache_directory=cache_directory,
        )
        source = directory / "paper.tex"
        source.write_text(_student_latex(paper, figures), encoding="utf-8")
        output = directory / "de_thi.docx"
        subprocess.run(
            [
                get_pandoc_path(),
                "-f",
                "latex",
                "-t",
                "docx",
                "--fail-if-warnings",
                "-o",
                output.name,
                source.name,
            ],
            cwd=directory,
            capture_output=True,
            check=True,
            timeout=timeout,
        )
        document = Document(output)
        for section in document.sections:
            section.page_width = Cm(21)
            section.page_height = Cm(29.7)
            section.top_margin = section.bottom_margin = Cm(2)
            section.left_margin = section.right_margin = Cm(2)
        for name in ("Normal", "Body Text", "First Paragraph", "Compact"):
            style = document.styles[name]
            style.paragraph_format.space_after = Pt(4)
        for name in ("Title", "Heading 1"):
            document.styles[name].font.color.rgb = RGBColor(0, 0, 0)
        for paragraph in document.paragraphs:
            if _QUESTION_CONTINUES.match(paragraph.text) or paragraph._p.xpath(".//w:drawing"):
                paragraph.paragraph_format.keep_with_next = True
        result = BytesIO()
        document.save(result)
        return result.getvalue()
