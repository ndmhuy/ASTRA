"""Common result serialization for approved packs and internal corpus searches."""

from dataclasses import asdict
import hashlib
import json
import re

from .models import CONFIG, Gap
from .search_index import PassageIndex, tokens


def document_dict(document):
    """Include computed checksums as well as stored provenance fields."""
    return dict(asdict(document), content_sha256=document.content_sha256)


def collection_fingerprint(documents):
    """SHA-256 of the ordered, canonical JSON search projection."""
    raw = json.dumps([asdict(d) for d in documents], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ranked_results(documents, keywords, top_k, mode=None, accented=()):
    """Return one best passage per content hash, with a match-centered excerpt."""
    active_mode = mode or CONFIG.get("default_mode", "hybrid")
    method = CONFIG.get("ranking_versions", {}).get(active_mode, CONFIG["ranking_version"])
    results, seen = [], set()
    for score, bm25, emb, document, passage, matched_terms in PassageIndex(
        documents
    ).ranked_detailed(keywords, accented=accented, mode=active_mode):
        if document.content_sha256 in seen:
            continue
        seen.add(document.content_sha256)
        matched = next(
            (
                m.start()
                for m in re.finditer(r"\S+", passage.text)
                if set(tokens(m[0])) & set(keywords)
            ),
            0,
        )
        start = max(0, matched - CONFIG["excerpt_leading_chars"])
        end = min(start + CONFIG["excerpt_chars"], len(passage.text))
        result = document_dict(document)
        result.pop("content")
        result.update(
            source_id=getattr(document, "source_id", document.document_id),
            excerpt=passage.text[start:end],
            excerpt_start=passage.start + start,
            excerpt_end=passage.start + end,
            passage_id=f"{document.document_id}:{passage.start}-{passage.end}",
            passage_start=passage.start,
            passage_end=passage.end,
            passage_label=passage.label,
            matched_terms=matched_terms,
            relevance_score=round(score, 6),
            bm25_score=round(bm25, 6),
            embedding_score=round(emb, 6),
            ranking_method=method,
        )
        if hasattr(document, "usage"):
            result["usage"] = document.usage
        results.append(result)
        if len(results) == top_k:
            break
    if not results:
        raise Gap("no_relevant_match", "In-scope documents exist but no query keyword matches.")
    return results
