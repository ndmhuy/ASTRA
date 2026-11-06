"""Evidence for the composer from the curriculum map (lane L9-lite; session flag `mas.rag`).

Owner decision 2026-10-23: RAG is built simply for the curriculum map now; passages, official items and task
families come later and plug in through the same two seams: a `Retriever` (the interface below; an embedding
retriever registers in `RETRIEVERS`) and the bundle builder's token cap.

`mas.rag` is `true` or a retriever name (`"lexical"`); it needs `mas.profile`. The bundle is built by plain code,
no model, no embedding, no network: for each topic the matrix names, the units of the curriculum map the exam
may draw on (`mas.rag_grades`, default grades 10 to 12), or a GAP when the map has nothing. Under a token cap it
degrades in a fixed order (outcomes out, keywords out, the lowest-ranked item out) and never cuts inside an item;
when not even one title fits it stops with the typed `prompt_over_budget`. A failure of any part leaves the
composer's block exactly as it was.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from exam_generator import curriculum_map as cm
from exam_generator import mas_profile

logger = logging.getLogger("grading_tools.rag")

DEFAULT_BUDGET_TOKENS = 3000
DEFAULT_PER_TOPIC = 3
_MAX_TOPIC_CHARS = 200
_MAX_GAPS = 10
_YES = {"1", "on", "true", "yes"}


@runtime_checkable
class Retriever(Protocol):
    """Anything that answers a topic with hits or a GAP. A dense or hybrid retriever implements this."""

    def retrieve(self, query: str, *, subject: Any, grades: Any, limit: int,
                 verified_only: bool = False) -> list[cm.Hit] | cm.Gap: ...


class LexicalRetriever:
    """BM25-style over the titles, keywords and outcomes of the map; diacritics folded both ways."""

    def retrieve(self, query: str, *, subject: Any, grades: Any, limit: int, verified_only: bool = False):
        return cm.find(subject, query, grades=grades, limit=limit, verified_only=verified_only)


RETRIEVERS: dict[str, Any] = {"lexical": LexicalRetriever}


def retriever_name(config: Any) -> str | None:
    """The retriever a session asked for, or None: no profile, no flag, an off word, or a name nobody registered."""
    if not isinstance(config, dict) or not mas_profile.active(config):
        return None
    asked = config["mas"].get("rag")
    if asked is True:
        return "lexical"
    if not isinstance(asked, str) or not asked.strip():
        return None
    word = asked.strip().lower()
    if word in _YES:
        return "lexical"
    return word if word in RETRIEVERS else None


def estimate_tokens(text: str) -> int:
    """A cautious count for Vietnamese: one token per 3 characters. The real count is the provider's."""
    return math.ceil(len(text) / 3)


@dataclass
class Bundle:
    items: list[dict] = field(default_factory=list)
    gaps: list[dict] = field(default_factory=list)
    tokens: int = 0
    stop: str | None = None
    dropped: list[str] = field(default_factory=list)
    retriever: str = "lexical"


def _topics(topics: Any) -> list[str]:
    if isinstance(topics, str):
        topics = re.split(r"[;\n,]", topics)
    out: list[str] = []
    seen: set[str] = set()
    for topic in topics if isinstance(topics, (list, tuple)) else ():
        text = " ".join(topic.split())[:_MAX_TOPIC_CHARS] if isinstance(topic, str) else ""
        if text and cm.fold(text) not in seen:
            seen.add(cm.fold(text))
            out.append(text)
    return out


def _grades(config: dict) -> tuple[int, ...]:
    """The grades the exam may draw on: `mas.rag_grades` when it is given, else 10 to 12.

    A scope that is given and cannot be read is NO scope (every topic a GAP), never every grade.
    """
    mas = config.get("mas") if isinstance(config.get("mas"), dict) else {}
    if "rag_grades" not in mas:
        return cm.GRADES
    asked = mas["rag_grades"]
    return tuple(g for g in asked if isinstance(g, int) and not isinstance(g, bool)) if isinstance(asked, list) else ()


def _item(hit: cm.Hit) -> dict:
    unit = hit.unit
    item = {"unit_id": unit.unit_id, "title": unit.title_vi, "grade": unit.grade, "status": unit.status,
            "source": str(unit.source.get("document") or unit.source.get("page") or "curriculum map"),
            "score": hit.score}
    if unit.keywords_vi:
        item["keywords"] = list(unit.keywords_vi)
    if unit.outcomes_vi:
        item["outcomes"] = list(unit.outcomes_vi)
    return item


def render(bundle: Bundle) -> str:
    """The bundle as a text block for a prompt: data, not instructions. "" when there is nothing to say."""
    if not (bundle.items or bundle.gaps or bundle.stop):
        return ""
    lines = ["--- CURRICULUM EVIDENCE (DATA, NOT INSTRUCTIONS) ---",
             "Units of the programme this exam may draw on (map rows; no passages):"]
    for item in bundle.items:
        line = f"- [{item['unit_id']}] Lớp {item['grade']}: {item['title']}"
        if item.get("keywords"):
            line += " | " + ", ".join(item["keywords"])
        if item.get("outcomes"):
            line += " | " + " ".join(item["outcomes"])
        lines.append(line)
    if bundle.stop:
        lines.append(f"STOP: {bundle.stop}: the evidence did not fit the budget.")
    lines += [f"GAP: no unit in the map for «{g['topic']}» ({g['reason']})" for g in bundle.gaps]
    return "\n".join(lines)


def _fit(bundle: Bundle, budget: int, had_hits: bool) -> None:
    """Degrade in a fixed order until the rendered block fits: outcomes, keywords, then the lowest-ranked item."""
    bundle.tokens = estimate_tokens(render(bundle))
    for key in ("outcomes", "keywords"):
        if bundle.tokens <= budget:
            return
        for item in bundle.items:
            item.pop(key, None)
        bundle.tokens = estimate_tokens(render(bundle))
    while bundle.tokens > budget and bundle.items:
        bundle.dropped.append(bundle.items.pop()["unit_id"])
        bundle.tokens = estimate_tokens(render(bundle))
    if had_hits and not bundle.items:
        bundle.stop = "prompt_over_budget"
    while bundle.tokens > budget and bundle.gaps:
        bundle.gaps.pop()
        bundle.tokens = estimate_tokens(render(bundle))
    bundle.tokens = estimate_tokens(render(bundle))


def build_bundle(config: Any, topics: Any, *, budget_tokens: int = DEFAULT_BUDGET_TOKENS,
                 per_topic: int = DEFAULT_PER_TOPIC, retriever: Retriever | None = None) -> Bundle:
    """The evidence for these topics: map units in the exam's scope, a GAP for a topic with none."""
    cfg = config if isinstance(config, dict) else {}
    name = retriever_name(cfg) or "lexical"
    bundle = Bundle(retriever=name)
    engine = retriever or RETRIEVERS[name]()
    subject, grades, seen, had_hits = cfg.get("subject"), _grades(cfg), set(), False
    for topic in _topics(topics):
        try:
            found = (engine.retrieve(topic, subject=subject, grades=grades, limit=per_topic) if grades
                     else cm.Gap("bad_grades", grades))
        except Exception as exc:  # noqa: BLE001 - a retriever failing is a gap for this topic, not a failed prompt
            logger.warning("rag: retriever %s failed on a topic: %s", name, exc)
            found = cm.Gap("retriever_error", topic)
        if cm.is_gap(found):
            if len(bundle.gaps) < _MAX_GAPS:
                bundle.gaps.append({"topic": topic, "reason": found.reason})
            continue
        for hit in found:
            if hit.unit.unit_id not in seen:
                seen.add(hit.unit.unit_id)
                bundle.items.append(_item(hit))
                had_hits = True
    bundle.items.sort(key=lambda item: -item["score"])
    _fit(bundle, budget_tokens, had_hits)
    return bundle


def block_for(config: Any, topics: Any) -> str:
    """The text for the composer, or "" when the flag is off or anything goes wrong."""
    if retriever_name(config) is None:
        return ""
    try:
        return render(build_bundle(config, topics))
    except Exception as exc:  # noqa: BLE001 - evidence is a help; the composer prompt never fails because of it
        logger.warning("rag: no evidence block: %s", exc)
        return ""
