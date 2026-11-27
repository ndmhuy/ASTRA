"""Native LaTeX question, passage and table assembly; answers stay private."""

from exam_baseline.pipeline.rendering.syntax import validate_drawing_code
from exam_baseline.thpt.content import content_latex
from exam_baseline.thpt.fonts import apply_font_profile
from exam_baseline.thpt.rendering import render_choice_rows
from exam_baseline.vact import template


def student_view(section):
    return dict(
        questions=[
            dict(id=q.id, stem=q.stem, choices=q.choices, passage_id=q.passage_id)
            for q in section.questions
        ],
        passages=[p.model_dump() for p in section.passages],
    )


def render(sections, drawings, font_profile):
    questions = [q for section in sections for q in section.questions]
    if [q.id for q in questions] != [f"q{i}" for i in range(1, 121)]:
        raise ValueError("VACT document requires all 120 questions in order")
    figures = {d.question_id: d.latex for d in drawings.drawings}
    if len(figures) != len(drawings.drawings) or set(figures) != {
        q.id for q in questions if q.illustration_request
    }:
        raise ValueError("Illustration bindings differ from requested diagrams")
    for code in figures.values():
        validate_drawing_code(code)
    parts = {key: [] for key in template.SECTIONS}
    for batch, section in zip(template.batches(), sections, strict=True):
        body = parts[batch.section]
        passages = {p.id: p for p in section.passages}
        seen = set()
        for q in section.questions:
            if q.passage_id and q.passage_id not in seen:
                p = passages[q.passage_id]
                group = next(g for g in batch.groups if g.id == p.id)
                body += [
                    rf"\noindent\textbf{{Dùng thông tin sau cho câu {group.start}"
                    rf"--{group.end}:}}\par"
                ]
                if p.heading:
                    body.append(r"\textbf{" + content_latex(p.heading) + r"}\par")
                body.append(content_latex(p.text) + r"\par")
                if p.table:
                    body += [
                        r"\begin{center}\begin{adjustbox}{max width=\linewidth}",
                        r"\begin{tabular}{|" + "c|" * len(p.table.columns) + r"}\hline",
                    ]
                    for row in [p.table.columns, *p.table.rows]:
                        body.append(" & ".join(content_latex(c) for c in row) + r"\\\hline")
                    body += [r"\end{tabular}\end{adjustbox}\end{center}"]
                seen.add(p.id)
            body.append(
                r"\noindent\textbf{Câu " + q.id[1:] + ":} " + content_latex(q.stem) + r"\par"
            )
            if q.id in figures:
                body += [
                    r"\begin{center}\begin{adjustbox}{max width=0.95\linewidth, "
                    r"max totalheight=0.38\textheight}",
                    figures[q.id],
                    r"\end{adjustbox}\end{center}",
                ]
            body.append(render_choice_rows(q.choices))
            body.append(r"\par\vspace{0.3cm}")
    return apply_font_profile(
        template.assemble({k: "\n".join(v) + "\n" for k, v in parts.items()}), font_profile
    )
