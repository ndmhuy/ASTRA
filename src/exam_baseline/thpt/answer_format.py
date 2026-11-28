"""Parse native THPT true/false answers for repair and verification."""

import re

_BOOL_TRUE = frozenset({"đúng", "dung", "đ", "d", "true", "t"})


def _parse_p2_booleans(answer: str) -> list[bool] | None:
    tokens = r"đúng|dung|sai|true|false|đ|d|s|t|f"
    separator = r"(?:\s*[,;]\s*|\s+)"
    labeled = rf"([a-d])\s*[):.\-=]\s*({tokens})"
    lowered = answer.strip().casefold()
    if re.fullmatch(rf"{labeled}(?:{separator}{labeled}){{3}}[.;]?", lowered):
        by_label = {label: token in _BOOL_TRUE for label, token in re.findall(labeled, lowered)}
        if len(by_label) == 4:
            return [by_label[label] for label in "abcd"]
        return None
    if re.fullmatch(rf"(?:{tokens})(?:{separator}(?:{tokens})){{3}}[.;]?", lowered):
        return [token in _BOOL_TRUE for token in re.findall(tokens, lowered)]
    return None
