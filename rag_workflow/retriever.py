"""Hard filters precede deterministic lexical, embedding and hybrid ranking."""

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
        if d.approval_status == "approved"
        and d.allow_local_retrieval
        and d.allow_quotation
        and d.series == scope.series
        and d.subject == scope.subject
        and d.grade == scope.grade
    ]
    if scope.range_type != "topic":
        eligible = [
            d
            for d in eligible
            if getattr(d, scope.range_type) is not None
            and scope.start <= getattr(d, scope.range_type) <= scope.end
        ]
    if scope.edition is not None:
        eligible = [d for d in eligible if d.edition == scope.edition]
    elif len({d.edition for d in eligible}) > 1:
        raise Gap(
            "ambiguous_edition", "Multiple editions match. Confirm an edition before retrieval."
        )
    if not eligible:
        raise Gap(
            "no_documents_in_scope", "No approved, permitted documents match the exact scope."
        )
    return ranked_results(
        eligible,
        scope.keywords,
        top_k,
        mode=mode,
        accented=scope.accented_keywords,
    )
