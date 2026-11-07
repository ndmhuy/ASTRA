"""Keep clear mathematical choices in math mode; never print raw TeX as prose."""

import re
import unicodedata

from exam_baseline.pipeline.rendering.syntax import prose

_MATH_SPANS = re.compile(r"(?<!\\)\${1,2}.*?(?<!\\)\${1,2}|\\\(.*?\\\)|\\\[.*?\\\]", re.DOTALL)
_TEXT_COMMAND = re.compile(r"\\(?:text|textrm|textbf|textit|emph)\s*\{")
_VIETNAMESE = re.compile(r"[À-ỹ]")


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


def content_latex(value: str) -> str:
    rendered = prose(value)
    for math in _MATH_SPANS.finditer(unicodedata.normalize("NFC", value)):
        outside = _without_text_arguments(math[0])
        if any(unicodedata.name(c, "").startswith("LATIN") for c in _VIETNAMESE.findall(outside)):
            raise ValueError(
                "Vietnamese prose inside math mode: move words outside $...$ or use \\text{...}"
            )
    return rendered


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
