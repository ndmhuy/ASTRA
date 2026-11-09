"""Governance permission filter followed by lexical, embedding and hybrid knowledge ranking."""

from .models import CONFIG, Gap, ResolvedScope, SourceDocument
from .results import ranked_results


def retrieve(
    documents: list[SourceDocument],
    scope: ResolvedScope,
    top_k: int,
    mode: str = CONFIG["default_mode"],
):
    eligible = [
        d
        for d in documents
        if d.approval_status == "approved" and d.allow_local_retrieval and d.allow_quotation
    ]
    if scope.edition is not None:
        eligible = [d for d in eligible if d.edition == scope.edition]
    if not eligible:
        raise Gap(
            "no_documents_in_scope", "No approved, permitted documents are available in the corpus."
        )
    return ranked_results(
        eligible,
        scope.keywords,
        top_k,
        mode=mode,
        accented=scope.accented_keywords,
    )
