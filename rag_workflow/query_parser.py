"""Conservative scope extraction: ambiguity never widens the search."""

import re
import unicodedata
from .models import CONFIG, Gap, ResolvedScope, RetrievalRequest

RANGE_WORDS = r"(?:chuong|chapters?|bai|lessons?|hoc\s*k[yi]|semesters?)"


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


def parse(request: RetrievalRequest, require_grade=True) -> ResolvedScope:
    raw_nfc = unicodedata.normalize("NFC", request.query_text).casefold()
    text = normalize(request.query_text)
    if re.search(r"\b(nua|half|dau nam|taught|da hoc|gan day)\b", text):
        raise Gap(
            "ambiguous_range",
            "Confirm the exact lessons already taught; partial chapters are not inferred.",
        )
    if re.search(r"canh dieu|chan troi", text):
        raise Gap("unsupported_series", "This corpus supports Kết nối tri thức only.")
    subjects = set()
    # Prevent compound terms ("điều hòa", "thuật toán", "bài toán", "tính toán") from false-matching subjects.
    subject_scan_text = re.sub(
        r"\b(?:dieu|trung|binh|tan|van|cong|hang|minh|do\s*thi)\s+hoa\b"
        r"|\b(?:thuat|bai|tinh|ke|du|thanh|an)\s+toan\b",
        " ",
        text,
    )
    for canonical, aliases in CONFIG["subjects"].items():
        for alias in (canonical, *aliases):
            norm_alias = normalize(alias)
            if (
                norm_alias == "hoa"
                and re.search(r"\bho[àa]\b", raw_nfc)
                and not re.search(r"\b(?:hóa|hoá)\b", raw_nfc)
            ):
                continue
            pattern = r"(?<!\w)" + re.escape(norm_alias) + r"(?!\w)"
            if re.search(pattern, subject_scan_text):
                subjects.add(canonical)
                subject_scan_text = re.sub(pattern, " ", subject_scan_text)
                if norm_alias not in ("hoa", "toan"):
                    text = re.sub(pattern, " ", text)
                elif norm_alias == "hoa":
                    text = re.sub(r"(?<!\bdieu )(?<!\btrung )\bhoa\b", " ", text)
                else:
                    text = re.sub(r"(?<!\bthuat )(?<!\bbai )(?<!\btinh )\btoan\b", " ", text)
    if len(subjects) != 1:
        raise Gap(
            "missing_subject" if not subjects else "ambiguous_subject",
            "Specify exactly one supported subject.",
        )
    grades = re.findall(r"\b(?:lop|khoi|grade)\s*(\d+)\b", text)
    if not grades and require_grade:
        raise Gap("missing_grade", "Specify the grade explicitly.")
    if grades and (len(set(grades)) != 1 or int(grades[0]) not in CONFIG["grades"]):
        raise Gap("invalid_grade", "Specify exactly one supported grade.")
    text = re.sub(r"\b(?:lop|khoi|grade)\s*\d+\b", " ", text)
    # Convert canonical Roman chapter/lesson numerals before numeric extraction.
    romans = {
        "i": 1,
        "ii": 2,
        "iii": 3,
        "iv": 4,
        "v": 5,
        "vi": 6,
        "vii": 7,
        "viii": 8,
        "ix": 9,
        "x": 10,
    }
    pattern = r"\b(chuong|chapter|bai|lesson|hoc\s*k[yi]|semester)\s*(\d+|[ivx]+)(?:\s*(?:-|–|—|den|to)\s*(?:\1\s*)?(\d+|[ivx]+))?\b"
    ranges = list(re.finditer(pattern, text))
    if not ranges:
        # A topic is an explicit range; broad subject-only requests need confirmation.
        kind, start, end = "topic", None, None
    elif len(ranges) != 1:
        raise Gap("ambiguous_range", "Use one chapter, lesson, or semester range per request.")
    else:
        match = ranges[0]
        kind = (
            "chapter"
            if match[1] in ("chuong", "chapter")
            else "lesson"
            if match[1] in ("bai", "lesson")
            else "semester"
        )

        def number(value):
            if value.isdigit():
                return int(value)
            if value not in romans:
                raise Gap("invalid_range", "Supported Roman range numerals are I–X.")
            return romans[value]

        start, end = number(match[2]), number(match[3] or match[2])
        if start < 1 or end < start or (kind == "semester" and end > 2):
            raise Gap("invalid_range", "Range endpoints must be positive, ordered and valid.")
        # Reject trailing range numbers like "bài 6 7", "bài 6 và 7", or "chương 2, 4".
        if re.match(
            r"^\s*(?:\d+\b|(?:,|&|\bva\b|\band\b)\s*(?:\d+|[ivx]+)\b(?!\s*=))",
            text[match.end() :],
        ):
            raise Gap("ambiguous_range", "Use one chapter, lesson, or semester range per request.")
        text = text[: match.start()] + " " + text[match.end() :]
    if re.search(rf"\b{RANGE_WORDS}\b", text):
        raise Gap("ambiguous_range", "Unresolved range or number; specify one explicit range.")
    keywords = tuple(
        dict.fromkeys(w for w in re.findall(r"\w+", text) if w not in CONFIG["stop_words"])
    )
    if kind == "topic" and not keywords:
        raise Gap("missing_range", "Specify a chapter, lesson, semester, or topic.")
    keyword_set = set(keywords)
    accented = tuple(
        dict.fromkeys(
            w
            for w in re.findall(r"\w+", raw_nfc)
            if normalize(w) in keyword_set and w != normalize(w)
        )
    )
    return ResolvedScope(
        subjects.pop(),
        int(grades[0]) if grades else None,
        kind,
        start,
        end,
        keywords,
        request.edition,
        accented_keywords=accented,
    )
