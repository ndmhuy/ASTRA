"""Deterministic Vietnamese intent and slot baseline with no network dependency."""

from __future__ import annotations

import re
import unicodedata

from .models import Intent, UnderstandingResult

SUBJECT_ALIASES = {
    "mathematics": ("toan", "toan hoc", "math", "mathematics"),
    "physics": ("vat ly", "vat li", "physics"),
    "chemistry": ("hoa hoc", "hoa", "chemistry"),
}

TOPIC_ALIASES = {
    "đạo hàm": ("dao ham", "derivative"),
    "tích phân": ("tich phan", "integral"),
    "xác suất": ("xac suat", "probability"),
    "lượng giác": ("luong giac", "trigonometry"),
}


def normalize_vietnamese(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    plain = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", plain.casefold()).strip()


def _has_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) for phrase in phrases)


def understand(text: str) -> UnderstandingResult:
    normalized = normalize_vietnamese(text)
    if re.match(r"^(?:noi dung de|van ban|tai lieu)\b", normalized):
        return UnderstandingResult(
            original_text=text,
            normalized_text=normalized,
            intents=["unknown"],
            confidence=0.2,
        )
    slots: dict[str, object] = {}
    removed_topics: list[str] = []
    intents: list[Intent] = []

    for canonical, aliases in SUBJECT_ALIASES.items():
        if _has_any(normalized, aliases):
            slots["subject"] = canonical
            break

    grade = re.search(r"\b(?:lop|khoi|grade)\s*(1[0-2]|[1-9])\b", normalized)
    if not grade and "subject" in slots:
        grade = re.search(
            r"\b(?:toan(?: hoc)?|math(?:ematics)?|vat (?:ly|li)|physics|hoa(?: hoc)?|chemistry)"
            r"\s*(1[0-2]|[1-9])\b",
            normalized,
        )
    if grade:
        slots["grade"] = int(grade.group(1))
    count = re.search(r"\b(\d{1,3})\s*(?:cau|questions?)\b", normalized)
    if count:
        slots["question_count"] = int(count.group(1))
    duration = re.search(r"\b(\d{1,3})\s*(?:phut|minutes?)\b", normalized)
    if duration:
        slots["duration_minutes"] = int(duration.group(1))

    topics: list[str] = []
    for canonical, aliases in TOPIC_ALIASES.items():
        if not _has_any(normalized, aliases):
            continue
        if re.search(
            rf"\b(?:khong|bo|tru)\s+(?:lay\s+)?(?:phan\s+)?{re.escape(aliases[0])}\b",
            normalized,
        ):
            removed_topics.append(canonical)
        else:
            topics.append(canonical)
    if topics:
        slots["topics"] = topics

    question_match = re.search(r"\bcau\s*(\d{1,3})\b", normalized)
    display_index = int(question_match.group(1)) if question_match else None
    explicit_question_edit = bool(
        display_index
        and re.search(
            r"\b(sua|doi|lam)\b.*\bcau\s*\d+|\bcau\s*\d+\b.*\b(de hon|kho hon)", normalized
        )
    )
    structural_edit = bool(count and re.search(r"\b(doi|giam|tang|con|sua)\b", normalized))

    cancellation = re.search(
        r"\b(thoi|bo|huy|giu)\b.*(?:\b(?:yeu cau|sua)\b|\bcau\s*\d+\b)", normalized
    ) or re.search(r"\bkhong\s+sua\s+cau\s*\d+\b", normalized)
    if cancellation:
        intents.append("cancel_pending_edit")
    elif explicit_question_edit or structural_edit:
        intents.append("explicit_edit")
    elif display_index and re.search(r"\b(kho|de)\s*(qua|the)?\b", normalized):
        intents.append("difficulty_remark")

    if re.search(r"\b(dang lam|den dau|tien do|xong chua|bao nhieu phan tram)\b", normalized):
        intents.append("job_status")
    if re.search(r"\b(astra|ung dung|chuc nang|lam duoc gi|xuat word|xuat pdf)\b", normalized):
        intents.append("app_help")
    if re.search(r"\b(mo|den|vao)\b.*\b(tu de|thu vien)\b", normalized):
        intents.append("navigate_library")
    if re.search(r"\b(?:ve|mo|den|vao)\b.*\b(?:trang chao|man hinh chinh|trang chu)\b", normalized):
        intents.append("navigate_welcome")
    if re.search(r"\b(?:mo|den|vao)\b.*\b(?:trang |muc )?(?:soan de|tao de)\b", normalized):
        intents.append("navigate_create")
    if re.search(
        r"\b(?:tao|mo|bat dau)\b.*\b(?:workspace|khong gian|phien lam viec|ban nhap)\b", normalized
    ):
        intents.append("create_session")
        slots["session_mode"] = (
            "template" if re.search(r"\b(?:tu mau|template)\b", normalized) else "custom"
        )
    if re.search(r"\b(?:mo|hien)\b.*\b(?:thiet lap|cau hinh)\b.*\bde\b", normalized):
        intents.append("open_exam_setup")
    if re.search(r"\bthu gon\b.*\b(?:menu|thanh ben|sidebar)\b", normalized):
        intents.append("collapse_sidebar")
    if re.search(r"\bmo rong\b.*\b(?:menu|thanh ben|sidebar)\b", normalized):
        intents.append("expand_sidebar")
    if re.search(r"\b(tao|ra|soan|lam)\b.*\b(de|bai kiem tra|exam)\b", normalized):
        intents.append("generate_exam")
    if re.search(r"\b(chon|dong y|lay)\b.*\b(goi y|preset|mau)\b", normalized):
        intents.append("accept_preset")
    if not intents and re.search(r"\b(xin chao|cam on|hello|ok)\b", normalized):
        intents.append("chatter")
    if not intents:
        intents.append("generate_exam" if slots or removed_topics else "unknown")

    return UnderstandingResult(
        original_text=text,
        normalized_text=normalized,
        intents=list(dict.fromkeys(intents)),
        slots=slots,
        removed_topics=removed_topics,
        display_question_index=display_index,
        confidence=0.9 if intents != ["unknown"] else 0.2,
    )
