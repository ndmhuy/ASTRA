"""Knowledge-first query tokenization and Vietnamese normalization."""

import re
import unicodedata
from .models import CONFIG, Gap, ResolvedScope, RetrievalRequest

STRUCTURAL_PREFIX = re.compile(
    r"\b(?:lop|khoi|grade)\s*\d+\b"
    r"|\b(chuong|chapters?|bai|lessons?|hoc\s*k[yi]|semesters?)\s*(?:\d+|[ivx]+)"
    r"(?:\s*(?:-|–|—|den|to)\s*(?:\1\s*)?(?:\d+|[ivx]+))?\b"
)
COMPOUND_TOAN = re.compile(
    r"(?<!\bthuat )(?<!\bbai )(?<!\btinh )(?<!\bke )(?<!\bdu )(?<!\bthanh )(?<!\ban )(?<!\bbao )\btoan\b"
)


def normalize(text: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
        if unicodedata.category(c) != "Mn"
    )


def accented_tokens(text: str) -> list[str]:
    """Extract lowercase NFC word tokens that carry Vietnamese diacritics."""
    nfc = unicodedata.normalize("NFC", text).casefold()
    return [w for w in re.findall(r"\w+", nfc) if w != normalize(w)]


def parse(request: RetrievalRequest) -> ResolvedScope:
    """Extract knowledge and topic keywords without constraining by subject, grade, or range."""
    raw_nfc = unicodedata.normalize("NFC", request.query_text).casefold()
    text = normalize(request.query_text)

    # Strip optional structural labels (e.g. "lớp 11", "chương 4", "bài 2") so their numbers
    # do not pollute knowledge keywords, while keeping numbers in topics ("định luật 2 Newton", "1945").
    text = STRUCTURAL_PREFIX.sub(" ", text)

    # Strip optional subject labels so bare subject names don't dilute topic vectors.
    for canonical, aliases in CONFIG["subjects"].items():
        for alias in (canonical, *aliases):
            norm_alias = normalize(alias)
            if norm_alias == "hoa":
                if re.search(r"\bmon\s+(?:hóa|hoá)\b", raw_nfc):
                    text = re.sub(r"\bmon\s+hoa\b", " ", text)
                continue
            if norm_alias == "toan":
                text = COMPOUND_TOAN.sub(" ", text)
                continue
            pattern = r"(?<!\w)" + re.escape(norm_alias) + r"(?!\w)"
            text = re.sub(pattern, " ", text)

    keywords = tuple(
        dict.fromkeys(w for w in re.findall(r"\w+", text) if w not in CONFIG["stop_words"])
    )
    if not keywords:
        raise Gap("missing_keywords", "Specify at least one knowledge or topic keyword to search.")
    keyword_set = set(keywords)
    accented = tuple(
        dict.fromkeys(
            w
            for w in re.findall(r"\w+", raw_nfc)
            if normalize(w) in keyword_set and w != normalize(w)
        )
    )
    return ResolvedScope(
        subject=None,
        grade=None,
        range_type="knowledge",
        start=None,
        end=None,
        keywords=keywords,
        edition=request.edition,
        series=None,
        accented_keywords=accented,
    )
