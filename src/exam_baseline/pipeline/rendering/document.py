"""Pure assembly of student question text and native TikZ/PGFPlots code."""

from exam_baseline.core.constants import LATEX_BODY_MARKER as MARKER
from exam_baseline.draft.models import ExamDraft
from exam_baseline.pipeline.contracts import IllustrationBook
from exam_baseline.pipeline.rendering.syntax import (
    format_errors,
    prose,
    validate_drawing_code,
    validate_template,
)

DEFAULT_TEMPLATE = r"""\documentclass[12pt,a4paper]{article}
\usepackage{fontspec}
\usepackage{amsmath,amssymb,graphicx}
\usepackage{tikz,pgfplots}
\pgfplotsset{compat=1.18}
\IfFontExistsTF{Arial}{\setmainfont{Arial}}{\setmainfont{DejaVu Sans}}
\begin{document}
%% ASTRA_BODY %%
\end{document}
"""


def render_document(
    draft: ExamDraft,
    template: str | None,
    topic_names: dict[str, str],
    illustrations: IllustrationBook | None = None,
) -> str:
    validate_template(template)
    if format_errors(draft):
        raise ValueError("invalid draft or unsupported LaTeX fragments")
    if draft.visuals and illustrations is None:
        raise ValueError("Illustrator agent output is required")
    template = template or DEFAULT_TEMPLATE
    # Dependencies are deterministic, even when a minimal user template omits them.
    dependencies = (
        "\n\\usepackage{fontspec,amsmath,amssymb,tikz,pgfplots}\n\\pgfplotsset{compat=1.18}\n"
    )
    template = template.replace(r"\begin{document}", dependencies + r"\begin{document}")
    body = [
        rf"\begin{{center}}\Large\textbf{{{prose(draft.exam.title)}}}\end{{center}}",
        rf"\noindent Thời gian: {draft.exam.duration_minutes} phút. "
        rf"Tổng điểm: {draft.exam.total_points:g}.\par",
        prose(draft.exam.instructions) + r"\par",
    ]
    figures = {}
    for drawing in illustrations.drawings if illustrations else []:
        validate_drawing_code(drawing.latex)
        figures[drawing.visual_id] = drawing.latex
    metadata = {q.id: q for q in draft.questions}
    passages = {p.start_question: p for p in draft.exam.shared_passages}
    topic = None
    for index, question in enumerate(draft.exam.questions, start=1):
        if question.topic_id != topic:
            topic = question.topic_id
            body.append(r"\section*{" + prose(topic_names[topic]) + "}")
        if index in passages:
            passage = passages[index]
            body += [
                rf"\noindent\textit{{Dùng thông tin sau cho câu {index}"
                rf"--{passage.end_question}:}}\par",
                prose(passage.text) + r"\par",
            ]
        stem = (
            question.stem if metadata[question.id].stem_format == "latex" else prose(question.stem)
        )
        body.append(
            rf"\noindent\textbf{{Câu {index}.}} ({question.points:g} điểm) " + stem + r"\par"
        )
        for label, choice in question.choices.items():
            body.append(r"\noindent\hspace*{1em}" + prose(label) + ". " + prose(choice) + r"\par")
        for visual_id in metadata[question.id].figure_refs:
            if visual_id in figures:
                body.append("\\begin{center}\n" + figures[visual_id] + "\n\\end{center}")
    return template.replace(MARKER, "\n".join(body)) + "\n"
