"""Render content only; no model may return or rewrite the template frame."""

import re

from exam_baseline.pipeline.rendering.syntax import validate_drawing_code
from exam_baseline.thpt.content import choice_latex, content_latex
from exam_baseline.thpt.fonts import DEFAULT_FONT_PROFILE, FontProfile, apply_font_profile
from exam_baseline.thpt.models import Illustrations, Question
from exam_baseline.thpt.template import assemble

_COMPLEX_CHOICE = re.compile(
    r"\\(?:frac|dfrac|tfrac|begin|sum|int|lim|prod|matrix|pmatrix|bmatrix|cases)\b|\$\$|\\\[",
    re.IGNORECASE,
)
_CHOICE_ROWS_MARKER = "% ASTRA_CHOICE_ROWS_FIT"


def render_choice_rows(choices: dict[str, str], *, legacy_grid: bool = False) -> str:
    """Use four or two columns when they fit, otherwise give each choice its own row."""
    values = [choices[label].strip() for label in "ABCD"]
    options = [
        f"{label}.~{choice_latex(value)}" for label, value in zip("ABCD", values, strict=True)
    ]
    quarter_width = r"\dimexpr.25\linewidth-.75em\relax"
    half_width = r"\dimexpr.5\linewidth-.5em\relax"

    def row(cells, width):
        boxes = [rf"\parbox[t]{{{width}}}{{\raggedright {cell}}}" for cell in cells]
        return r"\noindent " + "\\hfill%\n".join(boxes) + r"\par"

    pairs = "\n".join((row(options[:2], half_width), r"\nobreak", row(options[2:], half_width)))
    compact = not any(
        "\n" in value
        or _COMPLEX_CHOICE.search(value)
        or len(" ".join(value.replace("$", "").split())) > 16
        for value in values
    )
    if legacy_grid and not compact:
        return pairs

    singles = "\n".join(row([option], r"\linewidth") for option in options)
    # Display math and explicit line breaks need paragraph mode, not the measuring box.
    if any("\n" in value or "$$" in value or r"\[" in value for value in values):
        return "\n".join((_CHOICE_ROWS_MARKER, singles))

    measured = "".join(rf"\hbox{{{option}}}" for option in options)
    fallback = pairs
    if not legacy_grid:
        fallback = "\n".join(
            (
                rf"\ifdim\wd0>{half_width}",
                singles,
                r"\else",
                pairs,
                r"\fi",
            )
        )
    layout = fallback
    if compact:
        layout = "\n".join(
            (
                rf"\ifdim\wd0>{quarter_width}",
                fallback,
                r"\else",
                row(options, quarter_width),
                r"\fi",
            )
        )
    placed = "\n".join((r"\begingroup", rf"\setbox0=\vbox{{{measured}}}", layout, r"\endgroup"))
    return placed if legacy_grid else "\n".join((_CHOICE_ROWS_MARKER, placed))


def reflow_saved_choice_rows(source: bytes, questions: list[dict]) -> bytes:
    """Replace legacy choice blocks in a verified copy of the saved LaTeX."""
    if _CHOICE_ROWS_MARKER.encode() in source:
        return source
    has_old_rows = b"\n\\noindent A. " in source
    for question in questions:
        choices = question.get("choices") or {}
        if set(choices) != set("ABCD"):
            continue
        grid = ("\n" + render_choice_rows(choices, legacy_grid=True) + "\n").encode("utf-8")
        updated = b"\n" + render_choice_rows(choices).encode("utf-8") + b"\n"
        # Match only top-level grids immediately after the stem or its illustration.
        for prefix in (b"\\par", b"\\end{center}"):
            source = source.replace(prefix + grid, prefix + updated)
        if has_old_rows:
            legacy = "\n".join(
                rf"\noindent {label}. {choice_latex(choices[label])}\\" for label in "ABCD"
            )
            block = ("\n" + legacy + "\n").encode("utf-8")
            # Old stems used a forced line break. End that paragraph before the choices.
            source = source.replace(b"\\\\" + block, b"\\par" + updated)
            source = source.replace(block, updated)
    return source


def student_view(questions: list[Question]) -> list[dict]:
    return [
        dict(id=q.id, stem=q.stem, choices=q.choices, statements=[s.text for s in q.statements])
        for q in questions
    ]


def render_parts(
    questions: list[Question],
    illustrations: Illustrations,
    *,
    before: dict[str, str] | None = None,
) -> dict[str, str]:
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
        content_latex(q.solution, check_equations=False)
        stem_end = r"\par" if q.choices else r"\\"
        body = [rf"\noindent \textbf{{Câu {number}:}} " + content_latex(q.stem) + stem_end]
        if q.id in figures:
            body += [
                r"\begin{center}",
                r"\begin{adjustbox}{max width=0.95\linewidth, max totalheight=0.38\textheight}",
                figures[q.id],
                r"\end{adjustbox}",
                r"\end{center}",
            ]
        if q.choices:
            body.append(render_choice_rows(q.choices))
        for letter, statement in zip("abcd", q.statements, strict=False):
            content_latex(statement.solution, check_equations=False)
            body.append(r"\noindent " + letter + ") " + content_latex(statement.text) + r"\\")
        parts[part].append((before or {}).get(q.id, "") + "\n".join(body))
    return {p: "\n\n".join(body) + "\n\n" for p, body in parts.items()}


def render(
    questions: list[Question],
    illustrations: Illustrations,
    *,
    font_profile: FontProfile = DEFAULT_FONT_PROFILE,
) -> bytes:
    source = assemble(render_parts(questions, illustrations))
    return apply_font_profile(source, font_profile)
