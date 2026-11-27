"""Convert an approved student paper to Word or Markdown."""

import re
import subprocess
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from pypandoc import get_pandoc_path

from exam_baseline.thpt.content import content_latex
from exam_baseline.thpt.contract_artifacts import render_assets
from exam_baseline.thpt.fonts import DEFAULT_FONT_PROFILE
from exam_baseline.thpt.rendering import choices_are_compact
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


def _table(rows: list[list[str]], column_spec: str) -> str:
    lines = [" & ".join(row) for row in rows]
    return (
        r"\begin{tabular}{"
        + column_spec
        + "}\n"
        + (r" \\" + "\n").join(lines)
        + "\n"
        + r"\end{tabular}"
    )


def _word_choices(choices: dict[str, str]) -> list[str]:
    values = [value for value in choices.values() if value]
    options = [f"{label}. {value}" for label, value in choices.items() if value]
    if len(values) != 4 or any(
        "\n" in value or "$$" in value or r"\[" in value or len(value) > 39 for value in values
    ):
        return options
    columns = 4 if choices_are_compact(values) else 2
    rows = [options[start : start + columns] for start in range(0, 4, columns)]
    return [_table(rows, rf"p{{{1 / columns:.2f}\textwidth}}" * columns)]


def _student_latex(paper: dict, figures: dict, *, markdown: bool) -> str:
    title = content_latex(paper["title"])
    body = [
        r"\documentclass{article}",
        r"\usepackage{amsmath,amssymb,graphicx}",
        r"\begin{document}",
    ]
    if markdown:
        body.extend(
            [
                rf"\section*{{{title}}}",
                f"Thời gian: {paper['durationMinutes']} phút",
                "Họ và tên: .......................................................... "
                "Lớp: ....................",
            ]
        )
    passages = {passage["id"]: passage for passage in paper.get("passages", [])}
    previous_part = previous_passage = previous_instruction = None
    for question in paper["questions"]:
        part = question["part"]
        if part != previous_part:
            heading = r"\subsection*{" if markdown else r"\section*{"
            body.append(heading + _HEADINGS[part] + "}")
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
                rows = [list(map(content_latex, row)) for row in [columns, *table["rows"]]]
                body.append(_table(rows, "l" * len(columns)))
        previous_part, previous_passage, previous_instruction = part, passage_id, instruction

        stable_id = question["stableId"]
        number = stable_id.rsplit("-", 1)[-1] if part.startswith("P") else question["id"]
        body.append(rf"\textbf{{Câu {number}.}} " + content_latex(question["stem"]))
        if figure := figures.get(stable_id.lower()):
            body.append(r"\includegraphics[width=0.75\textwidth]{" + figure["path"] + "}")
        choices = question["choices"]
        if markdown:
            body.extend(f"{label}. {choice}" for label, choice in choices.items() if choice)
        else:
            body.extend(_word_choices(choices))
        body.extend(
            f"{label}) " + content_latex(statement["text"])
            for label, statement in zip("abcd", question.get("statements", []), strict=False)
        )
        if question["questionType"] == "short_answer":
            body.append("Trả lời: ........................................")
    return _BLANK.sub(lambda _: r"\_\_\_\_\_\_\_\_", "\n\n".join([*body, r"\end{document}"]))


def _field(paragraph, instruction: str) -> None:
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), instruction)
    paragraph._p.append(field)


def _set_table_widths(table, widths: tuple[float, ...]) -> None:
    table.autofit = False
    for index, width in enumerate(widths):
        table.columns[index].width = Cm(width)
        for row in table.rows:
            row.cells[index].width = Cm(width)
    total = table._tbl.tblPr.find(qn("w:tblW"))
    total.set(qn("w:type"), "dxa")
    total.set(qn("w:w"), str(Cm(sum(widths)).twips))


def _hide_table_borders(table) -> None:
    borders = OxmlElement("w:tblBorders")
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = OxmlElement(f"w:{name}")
        edge.set(qn("w:val"), "nil")
        borders.append(edge)
    table._tbl.tblPr.append(borders)


def _word_frame(document, source: bytes) -> None:
    """Build the editable heading and footer from the approved TeX template."""
    front = source.decode("utf-8").split(r"\begin{document}", 1)[1].split("% LECTURING-PART:", 1)[0]
    exam_name = re.search(r"\\bfseries (KỲ THI[^}]+)", front)
    code = re.search(r"Mã đề:\s*(\d+)", front)
    subject = re.search(r"\\bfseries (Môn thi:[^}]+)", front)
    minutes = re.search(r"Thời gian làm bài:\s*(?:\}\s*&\s*)?(\d+) phút", front)
    if not (exam_name and code and minutes):
        raise ValueError("Approved exam source is missing a Word heading field")
    time_label = f"Thời gian làm bài: {minutes[1]} phút, không kể thời gian phát đề"
    first = document.paragraphs[0]._p
    header = document.add_table(rows=1, cols=2)
    first.addprevious(header._tbl)
    _set_table_widths(header, (6.3, 10.7))
    _hide_table_borders(header)

    def centered(cell, text, *, bold=False, italic=False, new=False):
        paragraph = cell.add_paragraph() if new else cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(text)
        run.bold, run.italic = bold, italic
        run.font.size = Pt(10)
        return paragraph

    if subject:
        centered(header.cell(0, 0), "ĐỀ LUYỆN TẬP", bold=True)
        pages = centered(header.cell(0, 0), "(Đề thi có ", new=True)
        _field(pages, "NUMPAGES")
        pages.add_run(" trang)")
        centered(header.cell(0, 1), exam_name[1], bold=True)
        centered(header.cell(0, 1), subject[1], bold=True, new=True)
        centered(header.cell(0, 1), time_label, italic=True, new=True)
    else:
        title = header.cell(0, 0).merge(header.cell(0, 1))
        centered(title, exam_name[1], bold=True)
        centered(title, "ĐỀ LUYỆN TẬP", bold=True, new=True)
        centered(title, time_label, italic=True, new=True)

    identification = document.add_table(rows=1, cols=2)
    first.addprevious(identification._tbl)
    _set_table_widths(identification, (11.6, 5.4))
    _hide_table_borders(identification)
    details = identification.cell(0, 0)
    details.text = (
        "Họ, tên thí sinh: ................................................................"
    )
    details.add_paragraph(
        "Số báo danh: ..................................................................."
    )
    code_cell = identification.cell(0, 1)
    code_line = code_cell.paragraphs[0]
    code_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    code_line.paragraph_format.left_indent = Cm(1.8)
    code_line.add_run(f"Mã đề: {code[1]}").bold = True
    box = OxmlElement("w:pBdr")
    for name in ("top", "left", "bottom", "right"):
        side = OxmlElement(f"w:{name}")
        side.set(qn("w:val"), "single")
        side.set(qn("w:sz"), "4")
        side.set(qn("w:space"), "3")
        box.append(side)
    code_line._p.get_or_add_pPr().append(box)

    footer = document.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if subject:
        footer.add_run("Trang ")
    _field(footer, "PAGE")
    if subject:
        footer.add_run("/")
        _field(footer, "NUMPAGES")
        footer.add_run(f" - Mã đề thi {code[1]}")


def export_student_document(
    paper,
    job,
    format: Literal["docx", "md"],
    *,
    source: bytes,
    compiler,
    timeout,
    cache_directory: Path,
) -> tuple[str, str, bytes]:
    markdown = format == "md"
    writer = (
        "markdown+tex_math_dollars-raw_html-raw_tex-link_attributes-header_attributes"
        if markdown
        else "docx"
    )
    # Keep every input and output private to this request, including all figure asset paths.
    with TemporaryDirectory(prefix="astra-export-") as temp:
        directory = Path(temp)
        figures = render_assets(
            directory,
            job["drawings"]["drawings"],
            font_profile=job["nativeRequest"].get("font_profile", DEFAULT_FONT_PROFILE),
            compiler=compiler,
            timeout=timeout,
            cache_directory=cache_directory,
        )
        conversion_input = directory / "paper.tex"
        conversion_input.write_text(
            _student_latex(paper, figures, markdown=markdown), encoding="utf-8"
        )
        output = directory / f"de_thi.{format}"
        subprocess.run(
            [
                get_pandoc_path(),
                "-f",
                "latex",
                "-t",
                writer,
                "--wrap=none",
                "--fail-if-warnings",
                "-o",
                output.name,
                conversion_input.name,
            ],
            cwd=directory,
            capture_output=True,
            check=True,
            timeout=timeout,
        )
        if markdown:
            if not figures:
                return output.name, "text/markdown; charset=utf-8", output.read_bytes()
            result = BytesIO()
            with ZipFile(result, "w", compression=ZIP_DEFLATED) as archive:
                archive.write(output, output.name)
                for path in sorted({figure["path"] for figure in figures.values()}):
                    archive.write(directory / path, path)
            return "de_thi.zip", "application/zip", result.getvalue()

        document = Document(output)
        for table in document.tables:
            if table.cell(0, 0).text.startswith("A. "):
                columns = len(table.columns)
                _set_table_widths(table, (17 / columns,) * columns)
                _hide_table_borders(table)
        _word_frame(document, source)
        for section in document.sections:
            section.page_width = Cm(21)
            section.page_height = Cm(29.7)
            section.top_margin = section.bottom_margin = Cm(2)
            section.left_margin = section.right_margin = Cm(2)
        for style in document.styles:
            if style.type in (WD_STYLE_TYPE.PARAGRAPH, WD_STYLE_TYPE.CHARACTER):
                style.font.name = "Times New Roman"
                fonts = style.element.get_or_add_rPr().rFonts
                for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
                    fonts.attrib.pop(qn(f"w:{attr}"), None)
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
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return output.name, media, result.getvalue()
