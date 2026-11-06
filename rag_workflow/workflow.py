"""The public retrieval entry point; failures have explicit machine-readable gaps."""
from pathlib import Path
from .document_loader import load_documents
from .models import Gap, RetrievalRequest, RetrievalResponse
from .query_parser import parse
from .retriever import retrieve


def run(payload: dict, corpus_path: Path) -> RetrievalResponse:
    response = RetrievalResponse()
    try:
        if not isinstance(payload, dict):
            raise Gap("invalid_request", "Request must be a JSON object.")
        try:
            request = RetrievalRequest(**payload)
        except TypeError as exc:
            raise Gap("invalid_request", "Unknown or missing request fields.") from exc
        response.resolved_scope = parse(request)
        documents, response.corpus_sha256 = load_documents(corpus_path)
        response.documents = retrieve(documents, response.resolved_scope, request.top_k)
        response.status = "success"
    except Gap as exc:
        response.gaps.append({"code": exc.code, "message": str(exc)})
    return response
