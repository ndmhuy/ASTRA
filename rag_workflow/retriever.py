"""Hard filters precede deterministic lexical ranking."""
import re
from dataclasses import asdict
from .models import CONFIG, Gap, ResolvedScope, SourceDocument
from .query_parser import normalize
from .search_index import PassageIndex


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
    hits = PassageIndex(eligible).ranked(scope.keywords)
    seen = set()
    results = []
    for score, document, passage, matched_terms in hits:
        if document.content_sha256 in seen:
            continue
        seen.add(document.content_sha256)
        result = asdict(document)
        result.pop("content")
        matched = next((m.start() for m in re.finditer(r"\S+", passage.text)
                        if set(re.findall(r"\w+", normalize(m[0]))) & set(scope.keywords)), 0)
        start = max(0, matched - CONFIG["excerpt_leading_chars"])
        end = min(start + CONFIG["excerpt_chars"], len(passage.text))
        result["excerpt"] = passage.text[start:end]
        result["excerpt_start"] = passage.start + start
        result["excerpt_end"] = passage.start + end
        result["passage_id"] = f"{document.document_id}:{passage.start}-{passage.end}"
        result["passage_start"] = passage.start
        result["passage_end"] = passage.end
        result["matched_terms"] = matched_terms
        result["relevance_score"] = round(score, 6)
        result["ranking_method"] = CONFIG["ranking_version"]
        results.append(result)
        if len(results) == top_k:
            break
    if not results:
        raise Gap("no_relevant_match", "In-scope documents exist but no query keyword matches.")
    return results
