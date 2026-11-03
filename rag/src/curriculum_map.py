"""The curriculum map: rows of knowledge units, and the baseline API over them (lane L13; design v9 part L).

A skeleton of the programme (subject, grade, book order, title, a typical phase of the school year): no passages,
no embeddings, no model, no network. The rows are the draft data in `curriculum_map_data/*.jsonl` (copied from
`docs/mas-cloud/knowledge-map`, status `draft`). Owner decision 2026-10-23: draft rows are usable now and the owner
decides their status later, so every call takes `verified_only` (False by default); with True a draft row is
invisible, which is how a caller that must not rely on drafts says so.

Every miss is a `GAP` (falsy, with a reason), never a guess and never an empty list standing in for "unknown".
Nothing here is read unless a caller asks; the flag that asks is `mas.rag` (`rag.py`).
"""

from __future__ import annotations

import json
import logging
import math
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger("grading_tools.curriculum_map")

DATA_DIR = Path(__file__).resolve().parent / "curriculum_map_data"
GRADES = (10, 11, 12)
STATUSES = ("draft", "verified")
#: A test point is the end of a band of the school year: (semester, band rank) with early=0, mid=1, late=2.
TEST_POINTS = {"hk1_mid": (1, 1), "hk1_end": (1, 2), "hk2_mid": (2, 1), "hk2_end": (2, 2)}
_BAND_RANK = {"early": 0, "mid": 1, "late": 2}
#: A word the user writes for a subject, folded, and the name the rows use, folded.
_ALIASES = {"vatly": "vatli", "dialy": "diali", "hoa": "hoahoc", "sinh": "sinhhoc", "su": "lichsu",
            "dia": "diali", "van": "nguvan", "anh": "tienganh", "gdktpl": "gdktpl"}
_STOP = frozenset("bai chuong va cua la cac the trong nhung mot co cho voi tu den ve".split())


@dataclass(frozen=True)
class Gap:
    """Nothing to answer with. Falsy; `reason` is a short code, `query` what was asked."""

    reason: str
    query: Any = None

    def __bool__(self) -> bool:
        return False


def is_gap(value: Any) -> bool:
    return isinstance(value, Gap)


@dataclass(frozen=True)
class KnowledgeUnit:
    unit_id: str
    subject: str
    grade: int
    kind: str
    title_vi: str
    order: int
    parent_id: str | None = None
    keywords_vi: tuple[str, ...] = ()
    outcomes_vi: tuple[str, ...] | None = None
    semester: int | None = None
    band: str | None = None
    provenance: str | None = None
    source: dict = field(default_factory=dict, compare=False, hash=False)
    status: str = "draft"
    book_series: str | None = None


@dataclass(frozen=True)
class Hit:
    unit: KnowledgeUnit
    score: float


@dataclass(frozen=True)
class Scope:
    """The units of several grades of one subject, and the grades that have no row at all."""

    units: tuple[KnowledgeUnit, ...]
    missing_grades: list[int]

    def __bool__(self) -> bool:
        return bool(self.units)


def fold(value: Any) -> str:
    """Lower case, no diacritics (đ included), single spaces. Not a string: ""."""
    if not isinstance(value, str):
        return ""
    plain = unicodedata.normalize("NFD", value.replace("đ", "d").replace("Đ", "D"))
    plain = "".join(c for c in plain if unicodedata.category(c) != "Mn")
    return " ".join(plain.lower().split())


def subject_key(subject: Any) -> str:
    key = re.sub(r"[^a-z0-9]", "", fold(subject))
    return _ALIASES.get(key, key)


def _text_tuple(value: Any) -> tuple[str, ...]:
    return tuple(v.strip() for v in value if isinstance(v, str) and v.strip()) if isinstance(value, list) else ()


def _unit_of(row: Any) -> KnowledgeUnit | None:
    if not isinstance(row, dict):
        return None
    title, unit_id, subject = row.get("title_vi"), row.get("unit_id"), row.get("subject")
    grade, order = row.get("grade"), row.get("order")
    if not (isinstance(title, str) and title.strip() and isinstance(unit_id, str) and unit_id
            and isinstance(subject, str) and subject.strip()):
        return None
    if isinstance(grade, bool) or not isinstance(grade, int):
        return None
    phase = row.get("typical_phase") if isinstance(row.get("typical_phase"), dict) else {}
    semester = phase.get("semester") if isinstance(phase.get("semester"), int) else None
    band = phase.get("band") if isinstance(phase.get("band"), str) and phase["band"] in _BAND_RANK else None
    book = row.get("book") if isinstance(row.get("book"), dict) else {}
    return KnowledgeUnit(
        unit_id=unit_id, subject=subject.strip(), grade=grade, kind=str(row.get("kind") or ""),
        title_vi=title.strip(), order=order if isinstance(order, int) and not isinstance(order, bool) else 0,
        parent_id=row.get("parent_id") if isinstance(row.get("parent_id"), str) else None,
        keywords_vi=_text_tuple(row.get("keywords_vi")),
        outcomes_vi=_text_tuple(row.get("outcomes_vi")) or None,
        semester=semester, band=band, provenance=phase.get("provenance"),
        source=dict(row["source"]) if isinstance(row.get("source"), dict) else {},
        status=row.get("status") if row.get("status") in STATUSES else "draft",
        book_series=book.get("series"))


def parse_lines(lines: Iterable[str]) -> list[KnowledgeUnit]:
    """Units from JSON lines; a line that is not a unit is skipped (and logged), never fatal."""
    units = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            unit = _unit_of(json.loads(line))
        except (ValueError, TypeError, RecursionError, AttributeError):
            unit = None
        if unit is None:
            logger.warning("curriculum map: line %d is not a unit, skipped", number)
            continue
        units.append(unit)
    return units


@lru_cache(maxsize=None)
def _load() -> tuple[KnowledgeUnit, ...]:
    units: list[KnowledgeUnit] = []
    for path in sorted(DATA_DIR.glob("*.jsonl")):
        try:
            units += parse_lines(path.read_text(encoding="utf-8").splitlines())
        except (OSError, ValueError) as exc:  # UnicodeDecodeError is a ValueError
            logger.warning("curriculum map: %s unreadable: %s", path.name, exc)
    return tuple(units)


def all_units(*, verified_only: bool = False) -> tuple[KnowledgeUnit, ...]:
    units = _load()
    return tuple(u for u in units if u.status == "verified") if verified_only else units


def unit_by_id(unit_id: Any) -> KnowledgeUnit | None:
    return next((u for u in all_units() if u.unit_id == unit_id), None)


def _rows(subject: Any, grades: Iterable[int], verified_only: bool) -> list[KnowledgeUnit]:
    key, wanted = subject_key(subject), set(grades)
    if not key:
        return []
    return sorted((u for u in all_units(verified_only=verified_only)
                   if subject_key(u.subject) == key and u.grade in wanted), key=lambda u: (u.grade, u.order))


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def units_for(subject: Any, grade: Any, upto: Any = None, *, verified_only: bool = False) -> list[KnowledgeUnit] | Gap:
    """The units of one subject and grade in book order, up to a boundary.

    `upto`: None (all); a test point (`hk1_mid`, `hk1_end`, `hk2_mid`, `hk2_end`: the rows whose phase lies at or
    before it; a row with no phase is not placed, see `unplaced`); an int (rows with `order` up to it); or a
    `unit_id` of this subject and grade (up to and including it).
    """
    if not _is_int(grade):
        return Gap("bad_grade", grade)
    rows = _rows(subject, (grade,), verified_only)
    if not rows:
        return Gap("no_rows", (subject, grade))
    if upto is None:
        return rows
    if isinstance(upto, str) and upto in TEST_POINTS:
        semester, band = TEST_POINTS[upto]
        kept = [u for u in rows if u.semester is not None
                and (u.semester, _BAND_RANK.get(u.band, 2)) <= (semester, band)]
        return kept or Gap("no_phase", upto)
    if _is_int(upto) and upto >= 1:
        return [u for u in rows if u.order <= upto] or Gap("nothing_before_boundary", upto)
    if isinstance(upto, str):
        edge = next((u for u in rows if u.unit_id == upto), None)
        if edge is not None:
            return [u for u in rows if u.order <= edge.order]
    return Gap("bad_boundary", upto)


def unplaced(subject: Any, grade: Any, *, verified_only: bool = False) -> list[KnowledgeUnit]:
    """The rows of a subject and grade that carry no phase, so no test point can place them."""
    rows = units_for(subject, grade, verified_only=verified_only)
    return [] if is_gap(rows) else [u for u in rows if u.semester is None]


def cumulative_scope(subject: Any, grades: Any = GRADES, *, verified_only: bool = False) -> Scope | Gap:
    """Every unit of a subject over several grades (a national exam is cumulative), and the grades with no row."""
    asked = sorted({g for g in (grades if isinstance(grades, (list, tuple, set)) else ()) if _is_int(g)})
    if not asked:
        return Gap("bad_grades", grades)
    units = _rows(subject, asked, verified_only)
    if not units:
        return Gap("no_rows", (subject, tuple(asked)))
    present = {u.grade for u in units}
    return Scope(tuple(units), [g for g in asked if g not in present])


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", fold(text)) if t not in _STOP and (len(t) > 1 or t.isdigit())]


def _match(query_token: str, doc_tokens: set[str]) -> float:
    if query_token in doc_tokens:
        return 1.0
    if len(query_token) >= 4 and any(len(t) >= 4 and (t.startswith(query_token) or query_token.startswith(t))
                                     for t in doc_tokens):
        return 0.5
    return 0.0


def find(subject: Any, text: Any, *, grades: Iterable[int] | None = None, limit: int = 5,
         verified_only: bool = False) -> list[Hit] | Gap:
    """Units whose title, keywords or outcomes share words with `text` (diacritics folded both ways), best first.

    BM25-style: a word that few units carry counts more; a prefix of four letters or more counts half.
    """
    query = _tokens(text) if isinstance(text, str) else []
    if not query:
        return Gap("empty_query", text)
    asked = tuple(g for g in (GRADES if grades is None else grades) if _is_int(g))
    pool = _rows(subject, GRADES, verified_only)
    if not pool:
        return Gap("no_rows", subject)
    docs = {u.unit_id: _tokens(" ".join((u.title_vi, *u.keywords_vi, *(u.outcomes_vi or ())))) for u in pool}
    average = sum(len(d) for d in docs.values()) / len(docs) or 1.0
    df = {t: sum(1 for d in docs.values() if _match(t, set(d))) for t in set(query)}
    hits = []
    for unit in pool:
        if unit.grade not in asked:
            continue
        tokens = set(docs[unit.unit_id])
        length, score = len(docs[unit.unit_id]), 0.0
        for token in set(query):
            weight = _match(token, tokens)
            if not weight:
                continue
            idf = math.log(1 + (len(pool) - df[token] + 0.5) / (df[token] + 0.5))
            score += weight * idf * 2.2 / (1.0 + 1.2 * (0.25 + 0.75 * length / average))
        if score > 0:
            hits.append(Hit(unit, round(score, 6)))
    if not hits:
        return Gap("no_match", text)
    hits.sort(key=lambda h: (-h.score, h.unit.grade, h.unit.order))
    return hits[:max(1, int(limit))]
