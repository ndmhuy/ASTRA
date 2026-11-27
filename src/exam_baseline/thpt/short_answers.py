"""Answer-sheet limits and explicit precision rules for THPT short answers."""

import re
from decimal import Decimal

MAX_ANSWER_CHARACTERS = 5
NUMERIC_ANSWER_PATTERN = r"^-?[0-9]+(?:,[0-9]+)?$"

_ROUNDING = re.compile(
    r"làm tròn[^.!?;]{0,90}?\b(?:đến|tới|ở)\s+(?:chữ số\s+)?"
    r"(?:hàng\s+(?P<place>phần mười|phần trăm|phần nghìn|đơn vị|chục|trăm|nghìn)"
    r"|(?P<count>[0-5]|không|một|hai|ba|bốn|năm)\s+(?:chữ số\s+)?"
    r"(?:thập phân|sau dấu phẩy)"
    r"|thập phân thứ\s+(?P<ordinal>[1-5]|nhất|hai|ba|tư|năm)"
    r"|(?P<integer>số nguyên gần nhất))\b"
)
_PLACES = {
    "phần nghìn": 3,
    "phần trăm": 2,
    "phần mười": 1,
    "đơn vị": 0,
    "chục": -1,
    "trăm": -2,
    "nghìn": -3,
    "số nguyên gần nhất": 0,
    "nhất": 1,
    "tư": 4,
    **{word: n for n, word in enumerate(("không", "một", "hai", "ba", "bốn", "năm"))},
    **{str(n): n for n in range(6)},
}


def validate_short_answer_precision(stem: str, answer: str) -> None:
    text = " ".join(stem.casefold().replace("$", "").split())
    exact = bool(re.search(r"\b(?:không làm tròn|ghi kết quả chính xác)\b", text))
    rounding_text = text.replace("không làm tròn", "")
    places = {
        _PLACES[next(value for value in match.groups() if value is not None)]
        for match in _ROUNDING.finditer(rounding_text)
    }
    if (exact and (places or "làm tròn" in rounding_text)) or len(places) > 1:
        raise ValueError("P3 has conflicting instructions for rounding the answer")
    if exact:
        return
    if not places:
        raise ValueError(
            "P3 must state 'không làm tròn' for an exact numeric result or specify a rounding place"
        )
    digits = places.pop()
    step = Decimal(1).scaleb(-digits)
    if len(answer.partition(",")[2]) > max(0, digits) or Decimal(answer.replace(",", ".")) % step:
        raise ValueError("P3 key has more precision than the rounding place specified in the stem")
