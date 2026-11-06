"""LaTeX/TikZ safety and syntax checks; no file writes or model calls."""

import re

from exam_baseline.core.constants import LATEX_BODY_MARKER as MARKER
from exam_baseline.draft.models import ExamDraft

_COMMANDS = set(
    """frac dfrac tfrac sqrt sum prod int iint iiint oint lim log ln exp sin cos
tan cot sec csc arcsin arccos arctan sinh cosh tanh min max inf sup det gcd Pr binom dbinom
tbinom vec overrightarrow overleftarrow overline underline hat widehat bar dot ddot
tilde widetilde text textrm textbf textit emph mathrm mathbf mathit mathsf mathbb mathcal
mathscr boldsymbol operatorname left right middle big Big bigg Bigg bigl bigr Bigl Bigr
begin end quad qquad thinspace space hspace vspace le leq ge geq ne neq approx sim simeq
equiv cong propto pm mp times div cdot ast circ bullet to mapsto gets rightarrow leftarrow
Rightarrow Leftarrow Leftrightarrow leftrightarrow iff implies in notin ni subset subseteq
supset supseteq cup cap emptyset varnothing forall exists neg land lor angle measuredangle
perp parallel triangle square degree infty partial nabla ell ldots cdots vdots ddots
alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu
xi pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi psi omega Gamma Delta
Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega lvert rvert vert Vert lVert rVert lbrace
rbrace langle rangle lfloor rfloor lceil rceil underbrace overbrace substack displaystyle
textstyle scriptstyle scriptscriptstyle limits nolimits label tag nonumber notag cr
documentclass usepackage setmainfont setsansfont setmonofont IfFontExistsTF geometry
setlength parindent parskip baselinestretch pagestyle thispagestyle noindent par newline
textwidth linewidth centering raggedright section subsection title author date maketitle
vfill hfill dotfill newpage clearpage small normalsize large Large LARGE huge Huge
footnotesize scriptsize tiny bfseries itshape item itemsep topsep arraystretch
""".split()
)


_ENVIRONMENTS = {
    "document",
    "center",
    "flushleft",
    "flushright",
    "enumerate",
    "itemize",
    "aligned",
    "align",
    "align*",
    "gathered",
    "gather",
    "gather*",
    "cases",
    "matrix",
    "pmatrix",
    "bmatrix",
    "vmatrix",
    "Vmatrix",
    "array",
    "tabular",
    "equation",
    "equation*",
    "split",
    "multline",
    "multline*",
}


_PACKAGES = {
    "tikz",
    "pgfplots",
    "fontspec",
    "amsmath",
    "amssymb",
    "graphicx",
    "geometry",
    "array",
    "enumitem",
    "xcolor",
    "babel",
    "polyglossia",
    "unicode-math",
    "mathtools",
}


_MATH = re.compile(
    r"(?<!\\)(\$\$[\s\S]*?(?<!\\)\$\$|\$[^$\n]*(?<!\\)\$|"
    r"\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\])"
)


_PREAMBLE_COMMANDS = set(
    """documentclass usepackage setmainfont setsansfont setmonofont
IfFontExistsTF geometry setlength parindent parskip baselinestretch pagestyle thispagestyle
textwidth linewidth title author date maketitle arraystretch itemsep topsep""".split()
)


_PROSE_COMMANDS = {
    "textbf",
    "textit",
    "textrm",
    "emph",
    "noindent",
    "par",
    "newline",
    "small",
    "normalsize",
    "large",
    "Large",
    "bfseries",
    "itshape",
}


_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def check_fragment(value: str, *, template: bool = False, drawing: bool = False) -> list[str]:
    errors = []
    allowed = _COMMANDS | (
        {
            "draw",
            "path",
            "fill",
            "filldraw",
            "node",
            "coordinate",
            "addplot",
            "legend",
            "addlegendentry",
            "clip",
            "pgfplotsset",
        }
        if drawing or template
        else set()
    )
    for command in re.findall(r"\\([A-Za-z]+)", value):
        if command not in allowed or (not template and command in _PREAMBLE_COMMANDS):
            errors.append(f"unsupported_command:{command}")
    depth = 0
    for match in re.finditer(r"(?<!\\)[{}]", value):
        depth += 1 if match[0] == "{" else -1
        if depth < 0:
            errors.append("unbalanced_braces")
            break
    if depth != 0:
        errors.append("unbalanced_braces")
    stack = []
    for action, env in re.findall(r"\\(begin|end)\s*\{([^{}]+)\}", value):
        environments = _ENVIRONMENTS | ({"tikzpicture", "axis", "scope"} if drawing else set())
        if env not in environments or (env == "document" and not template):
            errors.append("unsupported_environment")
        if action == "begin":
            stack.append(env)
        elif not stack or stack.pop() != env:
            errors.append("unbalanced_environments")
    if stack:
        errors.append("unbalanced_environments")
    return sorted(set(errors))


def validate_template(template: str | None) -> None:
    if template is None:
        return
    if template.count(MARKER) != 1:
        raise ValueError("template requires exactly one %% ASTRA_BODY %%")
    before, after = template.split(MARKER)
    if (
        template.count(r"\begin{document}") != 1
        or template.count(r"\end{document}") != 1
        or r"\begin{document}" not in before
        or r"\end{document}" not in after
    ):
        raise ValueError("template marker must be inside document")
    errors = check_fragment(template, template=True)
    document_body = template.split(r"\begin{document}")[1].split(r"\end{document}")[0]
    remaining = document_body.replace(MARKER, "")
    remaining = re.sub(r"(?m)%.*$", "", remaining).strip()
    if remaining:
        errors.append("template_body_must_only_contain_marker")
    classes = re.findall(r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}", template)
    if len(classes) != 1 or classes[0] not in {"article", "report", "book", "exam"}:
        errors.append("unsupported_documentclass")
    for package_list in re.findall(r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}", template):
        if any(p.strip() not in _PACKAGES for p in package_list.split(",")):
            errors.append("unsupported_package")
    if errors:
        raise ValueError("invalid template: " + ", ".join(errors))


def prose(value: str) -> str:
    """Preserve supported explicit math, escape prose, reject ambiguous math delimiters."""
    parts = _MATH.split(value)
    output = []
    for i, part in enumerate(parts):
        if i % 2:
            errors = check_fragment(part)
            if errors:
                raise ValueError(", ".join(errors))
            output.append(part)
        else:
            if re.search(r"(?<!\\)\$|\\[()[\]]", part):
                raise ValueError("unbalanced_math_delimiters")
            # Accept escaped dollar as literal prose.
            part = part.replace(r"\$", "$")
            output.append("".join(_ESCAPES.get(c, c) for c in part))
    return "".join(output)


def format_errors(draft: ExamDraft) -> list[dict]:
    errors = []
    meta = {q.id: q for q in draft.questions}
    fields = [(None, draft.exam.title), (None, draft.exam.instructions)]
    fields += [(None, p.text) for p in draft.exam.shared_passages]
    for q in draft.exam.questions:
        try:
            if meta[q.id].stem_format == "latex":
                problems = check_fragment(q.stem)
                # Math delimiter balance is checked even for raw supported LaTeX.
                prose(q.stem)
                for index, part in enumerate(_MATH.split(q.stem)):
                    if index % 2 == 0 and (
                        any(c not in _PROSE_COMMANDS for c in re.findall(r"\\([A-Za-z]+)", part))
                        or re.search(r"(?<!\\)[%#&_^]", part)
                    ):
                        problems.append("raw_latex_prose_requires_escaped_text_and_math_delimiters")
                if problems:
                    raise ValueError(", ".join(problems))
            else:
                prose(q.stem)
        except ValueError as exc:
            errors.append({"question_id": q.id, "code": "latex_format", "message": str(exc)})
        fields += [(q.id, text) for text in q.choices.values()]
    for question_id, text in fields:
        try:
            prose(text)
        except ValueError as exc:
            errors.append({"question_id": question_id, "code": "latex_format", "message": str(exc)})
    return errors


def validate_drawing_code(code: str) -> None:
    """Conservative static subset; runtime compilation still uses no-shell-escape."""
    errors = check_fragment(code, drawing=True)
    if (
        not code.strip().startswith(r"\begin{tikzpicture}")
        or not code.strip().endswith(r"\end{tikzpicture}")
        or code.count(r"\begin{tikzpicture}") != 1
    ):
        errors.append("one_tikzpicture_required")
    if re.search(
        r"\^\^|\b(table|graphics|gnuplot|external|shell|file|execute)\b|\.code", code, re.IGNORECASE
    ):
        errors.append("external_io_or_executable_drawing_not_supported")
    if errors:
        raise ValueError("invalid illustration: " + ", ".join(errors))
