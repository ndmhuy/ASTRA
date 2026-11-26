"""Deterministic student XeLaTeX rendering for the 6 THPT 2026 contract formats."""

from __future__ import annotations

from exam_baseline.pipeline.rendering.syntax import _ESCAPES, prose
from exam_baseline.thpt.content import choice_latex, content_latex
from exam_baseline.thpt.fonts import DEFAULT_FONT_PROFILE, FontProfile
from exam_baseline.thpt2026.contract import question_type_map

_SECTION_DEFAULTS = {
    "P1": ("PHẦN I. Trắc nghiệm nhiều lựa chọn", "Chọn một phương án đúng A, B, C hoặc D."),
    "P2": (
        "PHẦN II. Trắc nghiệm đúng/sai",
        "Trong mỗi ý a), b), c), d) ở mỗi câu, chọn đúng hoặc sai.",
    ),
    "P3": ("PHẦN III. Trả lời ngắn", "Điền đáp án đúng theo yêu cầu của từng câu."),
}


def _safe_latex(text: str) -> str:
    cleaned = "".join(ch for ch in (text or "") if ch == "\n" or ord(ch) >= 32).strip()
    if not cleaned:
        return ""
    try:
        return content_latex(cleaned, check_equations=False)
    except ValueError:
        try:
            return prose(cleaned)
        except ValueError:
            return "".join(_ESCAPES.get(ch, ch) for ch in cleaned)


def _safe_choice(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    try:
        return choice_latex(cleaned)
    except ValueError:
        return _safe_latex(cleaned)


def _format_points(value: float | int) -> str:
    text = f"{float(value):g}".replace(".", ",")
    return f"({text} điểm)"


def _render_passage(passage: dict) -> list[str]:
    lines: list[str] = []
    q_range = passage.get("questionRange") or []
    instruction = str(passage.get("instruction") or "").strip()
    if instruction:
        lines.append(r"\noindent\textbf{" + _safe_latex(instruction) + r"}\par")
    elif len(q_range) == 2:
        lines.append(
            rf"\noindent\textbf{{Dùng thông tin sau cho câu {q_range[0]} đến câu "
            rf"{q_range[1]}:}}\par"
        )
    heading = str(passage.get("heading") or "").strip()
    if heading:
        lines.append(r"\noindent\textbf{" + _safe_latex(heading) + r"}\par")
    text = str(passage.get("text") or "").strip()
    if text:
        for para in text.split("\n\n"):
            chunk = para.strip()
            if chunk:
                lines.append(r"\noindent " + _safe_latex(chunk) + r"\par")
    table = passage.get("table")
    if table and table.get("columns"):
        cols = table["columns"]
        lines += [
            r"\begin{center}",
            r"\begin{tabular}{|" + "l|" * len(cols) + r"}\hline",
            " & ".join(r"\textbf{" + _safe_latex(str(c)) + "}" for c in cols) + r"\\\hline",
        ]
        for row in table.get("rows", []):
            cells = [_safe_latex(str(cell)) for cell in row]
            while len(cells) < len(cols):
                cells.append("")
            lines.append(" & ".join(cells[: len(cols)]) + r"\\\hline")
        lines += [r"\end{tabular}", r"\end{center}"]
    source = str(passage.get("source") or "").strip()
    if source:
        lines.append(r"\begin{flushright}\textit{" + _safe_latex(source) + r"}\end{flushright}")
    lines.append(r"\vspace{4pt}")
    return lines


def render_contract_exam_tex(
    profile: dict,
    questions: list[dict],
    passages: list[dict] | None = None,
    *,
    front_matter: list[str] | None = None,
    font_profile: FontProfile = DEFAULT_FONT_PROFILE,
) -> bytes:
    """Render standalone XeLaTeX source for the student paper only (keys excluded)."""
    if font_profile not in {"unicode_times", "original_t5"}:
        raise ValueError("Unknown font profile")

    font_name = "Times New Roman" if font_profile == "unicode_times" else "DejaVu Serif"
    lines = [
        r"\documentclass[12pt,a4paper]{article}",
        r"\usepackage[margin=2cm]{geometry}",
        r"\usepackage{fontspec,amsmath,amssymb,array}",
        rf"\IfFontExistsTF{{{font_name}}}{{\setmainfont{{{font_name}}}}}"
        r"{\setmainfont{TeX Gyre Termes}}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{3pt}",
        r"\begin{document}",
        r"\begin{center}",
        r"{\Large\textbf{ĐỀ LUYỆN TẬP TỐT NGHIỆP THPT 2026}}\\[4pt]",
        rf"\textbf{{Môn thi: {_safe_latex(profile['displayName'])}}}\\[2pt]",
        rf"Thời gian làm bài: {int(profile['durationMinutes'])} phút, không kể thời gian phát đề",
        r"\end{center}",
        r"\vspace{4pt}",
    ]

    if front_matter:
        for note in front_matter:
            if str(note).strip():
                lines.append(r"\noindent\textit{" + _safe_latex(str(note)) + r"}\par")
        lines.append(r"\vspace{4pt}")

    passage_map = {str(p["id"]): p for p in (passages or []) if p.get("id")}
    seen_passages: set[str] = set()
    q_by_id = {q["id"]: q for q in questions}
    spec_map = question_type_map(profile)

    for sec in profile["sections"]:
        sec_id = sec["id"]
        sec_type = sec["type"]
        default_title, default_instr = _SECTION_DEFAULTS.get(sec_id, (sec_id, ""))
        title = sec.get("title") or default_title
        lines.append(r"\section*{" + _safe_latex(title) + "}")
        if default_instr and sec_type != "written":
            instr = (
                "Choose one correct option A, B, C, or D."
                if profile.get("language") == "en" and sec_type == "mcq"
                else default_instr
            )
            lines.append(r"\noindent\textit{" + _safe_latex(instr) + r"}\par\vspace{4pt}")

        for idx in range(sec["count"]):
            qid = f"{sec_id}-{idx + 1}"
            q = q_by_id[qid]
            _, pos = spec_map[qid]
            pid = q.get("passage_id")
            if pid and pid in passage_map and pid not in seen_passages:
                lines.extend(_render_passage(passage_map[pid]))
                seen_passages.add(pid)

            stem_tex = _safe_latex(str(q.get("stem") or ""))
            points_label = ""
            points_by_item = sec.get("pointsByItem") or []
            if pos < len(points_by_item):
                points_label = " " + _format_points(points_by_item[pos])

            if sec_type == "written":
                wc_targets = sec.get("wordCountTargets") or []
                wc = q.get("word_count_target") or (
                    wc_targets[pos] if pos < len(wc_targets) else None
                )
                wc_hint = f" (khoảng {int(wc)} chữ)" if wc else ""
                lines.append(
                    rf"\noindent\textbf{{Câu {idx + 1}{points_label}{wc_hint}.}} "
                    + stem_tex
                    + r"\par"
                )
            elif stem_tex:
                lines.append(rf"\noindent\textbf{{Câu {idx + 1}.}} " + stem_tex + r"\par")
            else:
                lines.append(rf"\noindent\textbf{{Câu {idx + 1}.}}\par")

            if sec_type == "mcq":
                choices = q.get("choices") or {}
                for letter in "ABCD":
                    lines.append(
                        rf"\noindent\hspace*{{1em}}\textbf{{{letter}.}} "
                        + _safe_choice(str(choices.get(letter, "")))
                        + r"\par"
                    )
            elif sec_type == "true_false":
                for letter, stmt in zip("abcd", q.get("statements") or [], strict=False):
                    lines.append(
                        rf"\noindent\hspace*{{1em}}\textbf{{{letter})}} "
                        + _safe_latex(str(stmt.get("text") or ""))
                        + r"\par"
                    )
            lines.append(r"\vspace{3pt}")

    lines.append(r"\end{document}")
    return ("\n".join(lines) + "\n").encode("utf-8")
