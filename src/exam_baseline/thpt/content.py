"""Keep clear mathematical choices in math mode; never print raw TeX as prose."""

import re
import unicodedata

from exam_baseline.pipeline.rendering.syntax import prose

_MATH_SPANS = re.compile(r"(?<!\\)\${1,2}.*?(?<!\\)\${1,2}|\\\(.*?\\\)|\\\[.*?\\\]", re.DOTALL)
_TEXT_COMMAND = re.compile(r"\\(?:text|textrm|textbf|textit|emph)\s*\{")
_VIETNAMESE = re.compile(r"[À-ỹ]")
_BLANK = re.compile(r"\\underline\{\\hspace\{[0-3](?:\.\d{1,2})?cm\}\}|(?<!\\)_{3,}")
_BARE_EQUATION = re.compile(r"(?<![\w\\])[A-Za-z]{1,3}[0-9]*(?:\s*[+*/-]\s*[A-Za-z0-9]+)*\s*=")
_SUBJECT_LABEL = re.compile(r"(\\mathrm|[_^])\{([^{}\\]+)\}")
_SUBJECT_ASSIGNMENT = re.compile(r"\b([A-Z][a-z]?|[a-z])\s*=\s*-?\d+(?:[.,]\d+)?\b")
_CHEMICAL_FORMULA = re.compile(r"(?:[A-Z][a-z]?(?:_(?:\{\d+\}|\d+))?)+")
_JSON_LATEX_ESCAPES = {
    "\text": r"\text",
    "\times": r"\times",
    "\tfrac": r"\tfrac",
    "\frac": r"\frac",
    "\beta": r"\beta",
    "\right": r"\right",
    "\rho": r"\rho",
    "\nu": r"\nu",
}


def normalize_subject_content(value: str) -> str:
    """Repair common notation escapes while preserving the underlying question."""

    stripped = value.strip()
    if "_" in stripped and _CHEMICAL_FORMULA.fullmatch(stripped):
        return r"$\mathrm{" + stripped + "}$"

    def label(match):
        command, content = match.groups()
        if not _VIETNAMESE.search(content):
            return match[0]
        text = r"\text{" + content + "}"
        return text if command == r"\mathrm" else command + "{" + text + "}"

    def formula(value):
        for escaped, latex in _JSON_LATEX_ESCAPES.items():
            value = re.sub(re.escape(escaped) + r"(?![a-zA-Z])", lambda _, cmd=latex: cmd, value)
        value = value.replace(r"\mathring{A}", r"\text{Å}")
        return _SUBJECT_LABEL.sub(label, value)

    def prose_segment(value):
        return _SUBJECT_ASSIGNMENT.sub(lambda m: "$" + m[0] + "$", value)

    out = []
    cursor = 0
    for match in _MATH_SPANS.finditer(value):
        out.extend((prose_segment(value[cursor : match.start()]), formula(match[0])))
        cursor = match.end()
    out.append(prose_segment(value[cursor:]))
    return "".join(out)


def _prose_segment(value: str, check_equations: bool) -> str:
    unchecked = _BLANK.sub("", value)
    if re.search(r"(?<!\\)\^|\\[A-Za-z]+|(?<![\w\\])[A-Za-z]{1,3}_", unchecked):
        raise ValueError("Undelimited mathematics/TeX in prose; enclose formulas in $...$")
    if check_equations and _BARE_EQUATION.search(unchecked):
        raise ValueError("Undelimited equation in prose; enclose the complete formula in $...$")
    output, cursor = [], 0

    def escaped_prose(text):
        return prose(re.sub(r"\\([%&#_{}])", r"\1", text))

    for blank in _BLANK.finditer(value):
        output.append(escaped_prose(value[cursor : blank.start()]))
        output.append(blank[0] if blank[0].startswith("\\") else r"\underline{\hspace{2cm}}")
        cursor = blank.end()
    # Accept ordinary escaped punctuation without printing an extra literal backslash.
    output.append(escaped_prose(value[cursor:]))
    return "".join(output)


def _without_text_arguments(math: str) -> str:
    """Ignore explicit text groups, including nested/escaped braces."""
    remaining = []
    cursor = 0
    while match := _TEXT_COMMAND.search(math, cursor):
        remaining.append(math[cursor : match.start()])
        depth = 1
        for brace in re.finditer(r"(?<!\\)[{}]", math[match.end() :]):
            depth += 1 if brace[0] == "{" else -1
            if depth == 0:
                cursor = match.end() + brace.end()
                break
        else:
            raise ValueError("Unbalanced text group in mathematics")
    remaining.append(math[cursor:])
    return "".join(remaining)


def content_latex(value: str, *, check_equations: bool = True) -> str:
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", value):
        raise ValueError("Control character in content; escape LaTeX backslashes correctly in JSON")
    output, cursor = [], 0
    for math in _MATH_SPANS.finditer(value):
        output.append(_prose_segment(value[cursor : math.start()], check_equations))
        if "\t" in math[0]:
            raise ValueError(
                "Tab inside math; a JSON backslash escape may have corrupted a command"
            )
        output.append(prose(math[0]))
        cursor = math.end()
    output.append(_prose_segment(value[cursor:], check_equations))
    for math in _MATH_SPANS.finditer(unicodedata.normalize("NFC", value)):
        outside = _without_text_arguments(math[0])
        if any(unicodedata.name(c, "").startswith("LATIN") for c in _VIETNAMESE.findall(outside)):
            raise ValueError(
                "Vietnamese prose inside math mode: move words outside $...$ or use \\text{...}"
            )
    return "".join(output)


def choice_latex(value: str) -> str:
    value = value.strip()
    if "$" in value or any(mark in value for mark in (r"\(", r"\[")):
        return content_latex(value)
    if re.fullmatch(r"\{[-+\d;,\s]+\}", value):
        value = r"\{" + value[1:-1] + r"\}"
    # Legacy Composer responses sometimes omit delimiters on a whole expression.
    # Recognize only ASCII mathematics, not arbitrary Vietnamese/text options.
    words = re.findall(r"[A-Za-z]+", re.sub(r"\\[A-Za-z]+", "", value))
    if re.fullmatch(r"[A-Za-z0-9\s\\{}()[\].,;:+*/=<>\-_|^!'\"]+", value) and all(
        len(word) == 1 for word in words
    ):
        return content_latex("$" + value + "$")
    if re.search(r"\\[A-Za-z]+|[_^]", value):
        raise ValueError("Choice mixes prose and raw mathematics; enclose formulas in $...$")
    return content_latex(value)
