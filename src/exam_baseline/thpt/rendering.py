"""Render content only; no model may return or rewrite the template frame."""

from exam_baseline.pipeline.rendering.syntax import validate_drawing_code
from exam_baseline.thpt.content import choice_latex, content_latex
from exam_baseline.thpt.fonts import DEFAULT_FONT_PROFILE, FontProfile, apply_font_profile
from exam_baseline.thpt.models import Illustrations, Question
from exam_baseline.thpt.template import assemble


def student_view(questions: list[Question]) -> list[dict]:
    return [
        dict(id=q.id, stem=q.stem, choices=q.choices, statements=[s.text for s in q.statements])
        for q in questions
    ]


def render(
    questions: list[Question],
    illustrations: Illustrations,
    *,
    font_profile: FontProfile = DEFAULT_FONT_PROFILE,
) -> bytes:
    figures = {d.question_id: d.latex for d in illustrations.drawings}
    expected = {q.id for q in questions if q.illustration_request}
    if len(figures) != len(illustrations.drawings) or set(figures) != expected:
        raise ValueError("Illustrator must return exactly the requested question IDs")
    for code in figures.values():
        validate_drawing_code(code)
    parts = {p: [] for p in ("P1", "P2", "P3")}
    for q in questions:
        part, number = q.id.split("-")
        # Validate private prose too, before it can be rendered in a solutions document.
        content_latex(q.solution)
        body = [rf"\noindent \textbf{{Câu {number}:}} " + content_latex(q.stem) + r"\\"]
        if q.id in figures:
            body += [
                r"\begin{center}",
                r"\begin{adjustbox}{max width=0.95\linewidth, max totalheight=0.38\textheight}",
                figures[q.id],
                r"\end{adjustbox}",
                r"\end{center}",
            ]
        for letter in "ABCD" if q.choices else "":
            body.append(r"\noindent " + letter + ". " + choice_latex(q.choices[letter]) + r"\\")
        for letter, statement in zip("abcd", q.statements, strict=False):
            content_latex(statement.solution)
            body.append(r"\noindent " + letter + ") " + content_latex(statement.text) + r"\\")
        parts[part].append("\n".join(body))
    source = assemble({p: "\n\n".join(body) + "\n\n" for p, body in parts.items()})
    return apply_font_profile(source, font_profile)
