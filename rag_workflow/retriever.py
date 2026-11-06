"""Hard filters precede deterministic lexical ranking."""
import re
from dataclasses import asdict
from .models import CONFIG, Gap, ResolvedScope, SourceDocument
from .query_parser import normalize


def retrieve(documents: list[SourceDocument], scope: ResolvedScope, top_k: int):
    eligible = [d for d in documents if d.approval_status == "approved"
                and d.allow_local_retrieval and d.allow_quotation
                and d.series == scope.series and d.subject == scope.subject
                and d.grade == scope.grade]
    if scope.range_type != "topic":
        eligible = [d for d in eligible if getattr(d, scope.range_type) is not None
                    and scope.start <= getattr(d, scope.range_type) <= scope.end]
    if scope.edition is not None:
        eligible = [d for d in eligible if d.edition == scope.edition]
    elif len({d.edition for d in eligible}) > 1:
        raise Gap("ambiguous_edition", "Multiple editions match. Confirm an edition before retrieval.")
    if not eligible:
        raise Gap("no_documents_in_scope", "No approved, permitted documents match the exact scope.")
    hits = []
    seen = set()
    for document in eligible:
        title, content = normalize(document.title), normalize(document.content)
        title_words, content_words = set(re.findall(r"\w+", title)), set(re.findall(r"\w+", content))
        score = sum(CONFIG["title_weight"] * (w in title_words)
                    + CONFIG["content_weight"] * (w in content_words) for w in scope.keywords)
        if scope.keywords and " ".join(scope.keywords) in title + " " + content:
            score += CONFIG["phrase_bonus"]
        if not scope.keywords or score > 0:
            hits.append((score, document))
    # Scores are lexical weights, not calibrated probabilities of relevance.
    hits.sort(key=lambda hit: (-hit[0], hit[1].document_id))
    results = []
    for score, document in hits:
        if document.content_sha256 in seen:
            continue
        seen.add(document.content_sha256)
        result = asdict(document)
        result.pop("content")
        matched = next((m.start() for m in re.finditer(r"\w+", document.content)
                        if normalize(m[0]) in scope.keywords), 0)
        start = max(0, matched - CONFIG["excerpt_leading_chars"])
        result["excerpt"] = document.content[start:start + CONFIG["excerpt_chars"]]
        result["relevance_score"] = score
        results.append(result)
        if len(results) == top_k:
            break
    if not results:
        raise Gap("no_relevant_match", "In-scope documents exist but no query keyword matches.")
    return results
