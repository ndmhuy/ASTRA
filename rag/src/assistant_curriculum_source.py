"""The curriculum map as a source: a structured scope first (subject, grade, chapter), words second.

Reads `exam_generator.curriculum_map` and changes nothing there. The words are the map's own lexical ranking with one
addition the data showed it needs: a teacher writes "định luật Ôm" and the map says "Ohm", which folds to different
letters, so a short table of spellings is applied to the query before it is matched.
"""
from __future__ import annotations

import re

from exam_generator import curriculum_map as cm
from exam_generator.assistant.knowledge import Passage, Retrieval

#: How teachers write a subject -> the map's own subject name. Folded (no diacritics, lower case).
SUBJECT_ALIASES = {
    "toan": "Toán", "ly": "Vật lí", "vat ly": "Vật lí", "vat li": "Vật lí", "hoa": "Hóa học", "hoa hoc": "Hóa học",
    "sinh": "Sinh học", "sinh hoc": "Sinh học", "su": "Lịch sử", "lich su": "Lịch sử", "dia": "Địa lí", "dia li": "Địa lí",
    "dia ly": "Địa lí", "van": "Ngữ văn", "ngu van": "Ngữ văn", "anh": "Tiếng Anh", "tieng anh": "Tiếng Anh",
    "gdktpl": "GDKT&PL", "kinh te phap luat": "GDKT&PL", "gdcd": "GDKT&PL",
    # Registered subjects the map has no rows for: recognised, so the answer is "no data" and not a search that matches nothing real.
    "tin hoc": "Tin học", "cong nghe": "Công nghệ", "tieng nga": "Tiếng Nga", "tieng phap": "Tiếng Pháp",
    "tieng trung": "Tiếng Trung", "tieng duc": "Tiếng Đức", "tieng nhat": "Tiếng Nhật", "tieng han": "Tiếng Hàn",
}
#: Spellings that fold to different letters than the map's: query word -> the map's word.
QUERY_ALIASES = {"om": "ohm", "niuton": "newton", "newton": "newton", "jun": "joule", "jul": "joule"}
_ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}
# The map's own stop list also drops "tu", which is both "từ" and "tụ" (a lesson called Tụ điện cannot be found), so it is not reused.
_FUNCTION = set("va cua la cac the trong nhung mot co cho voi den ve".split())
_STOP_TAIL = set("o dau nam co gom nhung bai nao gi la thuoc lop may hoc mon chuong chuyen de ra em muon phut khong minh can thay cho toi".split())


def _folded(text: str) -> str:
    return re.sub(r"\s+", " ", cm.fold(text)).strip()


def parse_scope(text: str) -> dict:
    """Subject, grade and chapter number as far as the words say them; anything unsaid stays absent."""
    f = _folded(text)
    scope: dict = {}
    grade = re.search(r"\blop\s*(1[0-2])\b", f) or re.search(r"\b(?:ly|hoa|sinh|su|dia|van|toan|anh|tin|cong nghe)\s*(1[0-2])\b", f) \
        or re.search(r"\b(1[0-2])\b", f)
    if grade:
        scope["grade"] = int(grade.group(1))
    for alias in sorted(SUBJECT_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", f):
            scope["subject"] = SUBJECT_ALIASES[alias]
            break
    chapter = re.search(r"\bchuong\s+(\d{1,2}|[ivx]{1,4})\b", f)
    if chapter:
        raw = chapter.group(1)
        scope["chapter"] = int(raw) if raw.isdigit() else _ROMAN.get(raw)
    if re.search(r"\bchuyen de\b", f):
        scope["kind"] = "chuyên đề"
    if re.search(r"\bhoc ki\s*(1|i)\b|\bhk\s*1\b", f):
        scope["semester"] = 1
    elif re.search(r"\bhoc ki\s*(2|ii)\b|\bhk\s*2\b", f):
        scope["semester"] = 2
    return scope


def _chapter_number(unit: cm.KnowledgeUnit) -> int | None:
    m = re.match(r"\s*chuong\s+(\d{1,2}|[ivx]+)\b", _folded(unit.title_vi))
    if not m:
        return None
    return int(m.group(1)) if m.group(1).isdigit() else _ROMAN.get(m.group(1))


def _words(text: str, scope: dict) -> str:
    """What is left of the question once the scope and the question words are taken out, with spellings mapped to the map's."""
    f = re.sub(r"[^a-z0-9\s]", " ", _folded(text))
    for alias in sorted(SUBJECT_ALIASES, key=len, reverse=True):
        f = re.sub(rf"\b{re.escape(alias)}\b", " ", f)
    out = []
    for token in f.split():
        if token in _STOP_TAIL or token in _FUNCTION or token.isdigit() or len(token) < 2:
            continue
        out.append(QUERY_ALIASES.get(token, token))
    return " ".join(out)


def _coverage(unit: cm.KnowledgeUnit, words: str) -> float:
    """The share of the question's words the unit's title, keywords or outcomes carry (a 4-letter prefix counts)."""
    query = set(words.split())
    if not query:
        return 0.0
    have = set(re.sub(r"[^a-z0-9\s]", " ", _folded(" ".join((unit.title_vi, *unit.keywords_vi, *(unit.outcomes_vi or ()))))).split())
    hit = sum(1 for q in query if q in have or (len(q) >= 4 and any(len(t) >= 4 and (t.startswith(q) or q.startswith(t)) for t in have)))
    return hit / len(query)


def _ranked(subject: str, words: str, grades) -> list:
    """The map's lexical hits, re-ranked by how many of the question's own words each unit carries; under half is no match."""
    got = cm.find(subject, words, grades=grades, limit=80)
    if cm.is_gap(got):
        return []
    kept = [h for h in got if _coverage(h.unit, words) >= 0.5]
    return sorted(kept, key=lambda h: (-_coverage(h.unit, words), -h.score))


def _passage(unit: cm.KnowledgeUnit, score: float = 0.0) -> Passage:
    parent = cm.unit_by_id(unit.parent_id) if unit.parent_id else None
    where = f"{unit.subject} {unit.grade}" + (f" › {parent.title_vi}" if parent else "")
    note = " (tên chưa xác minh)" if "chưa xác minh" in unit.title_vi else ""
    return Passage(id=unit.unit_id, title=unit.title_vi, text=f"{where} · {unit.kind}{note}", source="curriculum", score=score,
                   meta={"grade": unit.grade, "status": unit.status, "kind": unit.kind})


class CurriculumSource:
    name = "curriculum"

    def search(self, query: dict, *, limit: int) -> Retrieval:
        text = str(query.get("text") or "")
        scope = {**parse_scope(text), **{k: v for k, v in query.items() if k in ("subject", "grade", "chapter", "semester", "kind") and v}}
        subjects = sorted({u.subject for u in cm.all_units()})
        meta = {"scope": scope, "valid_subjects": subjects}
        subject = scope.get("subject")
        if not subject:
            return self._across_subjects(text, scope, limit, meta)
        rows = [u for u in cm.all_units() if u.subject == subject]
        if not rows:
            return Retrieval(self.name, gap="no_rows", meta=meta)
        if scope.get("grade"):
            rows = [u for u in rows if u.grade == scope["grade"]]
            if not rows:
                return Retrieval(self.name, gap="no_rows", meta=meta)
        if scope.get("semester"):
            known = [u for u in rows if u.semester]
            if not known:
                return Retrieval(self.name, gap="semester_unknown", meta=meta)
            rows = [u for u in known if u.semester == scope["semester"]]
        if scope.get("chapter"):
            chapters = [u for u in rows if _chapter_number(u) == scope["chapter"]]
            if chapters:
                kids = sorted((u for u in rows if u.parent_id in {c.unit_id for c in chapters}), key=lambda u: u.order)
                return Retrieval(self.name, [_passage(c) for c in chapters] + [_passage(k) for k in kids][:limit * 3], None, meta)
        if scope.get("kind"):
            kind = [u for u in rows if u.kind == scope["kind"]]
            if kind:
                return Retrieval(self.name, [_passage(u) for u in sorted(kind, key=lambda u: (u.grade, u.order))][:limit * 3], None, meta)
        words = _words(text, scope)
        if not words:
            top = [u for u in rows if u.kind in ("chương", "chuyên đề", "phần", "unit", "chủ đề")] or rows
            return Retrieval(self.name, [_passage(u) for u in sorted(top, key=lambda u: (u.grade, u.order))][:limit * 3], None, meta)
        grades = [scope["grade"]] if scope.get("grade") else None
        hits = _ranked(subject, words, grades)
        if scope.get("semester"):
            hits = [h for h in hits if h.unit.semester == scope["semester"]] or hits
        if not hits:
            # Say what DOES exist for this subject and grade, so the answer can be "no such lesson; here is what the map has".
            titles = [u.title_vi for u in sorted(rows, key=lambda u: (u.grade, u.order)) if u.kind in ("bài", "chuyên đề", "chủ đề", "unit")][:12]
            return Retrieval(self.name, gap="no_match", meta={**meta, "unit_titles": titles})
        return Retrieval(self.name, [_passage(h.unit, h.score) for h in hits[:limit]], None, meta)

    def _across_subjects(self, text: str, scope: dict, limit: int, meta: dict) -> Retrieval:
        """No subject was named: rank every subject's best units for the words, and say the subject was a guess."""
        words = _words(text, scope)
        if not words:
            return Retrieval(self.name, gap="empty_query", meta=meta)
        grades = [scope["grade"]] if scope.get("grade") else None
        found = []
        for subject in meta["valid_subjects"]:
            found += _ranked(subject, words, grades)
        found.sort(key=lambda h: (-_coverage(h.unit, words), -h.score))
        if not found:
            return Retrieval(self.name, gap="no_match", meta=meta)
        return Retrieval(self.name, [_passage(h.unit, h.score) for h in found[:limit]], None, {**meta, "subject_guessed": True})
