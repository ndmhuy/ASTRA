"""Read a single immutable JSONL snapshot; never crawl or open source links."""
import hashlib
import json
from pathlib import Path
from .models import Gap, SourceDocument


def load_documents(path: Path) -> tuple[list[SourceDocument], str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Gap("corpus_unavailable", str(exc)) from exc
    return decode_documents(raw)


def decode_documents(raw: bytes) -> tuple[list[SourceDocument], str]:
    documents, ids = [], set()
    try:
        lines = raw.decode("utf-8-sig").splitlines()
    except UnicodeError as exc:
        raise Gap("malformed_document", "Corpus must be UTF-8 JSONL.") from exc
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if isinstance(record, dict) and "unit_id" in record:
                raise Gap("curriculum_metadata_only", "Legacy curriculum rows are draft scope metadata, not approved knowledge passages. Review and publish a passage pack first.")
            document = SourceDocument(**record)
            if document.document_id in ids:
                raise ValueError("Duplicate document_id.")
        except (ValueError, TypeError) as exc:
            if isinstance(exc, Gap):
                raise
            raise Gap("malformed_document", f"Line {number}: {exc}") from exc
        documents.append(document)
        ids.add(document.document_id)
    return documents, hashlib.sha256(raw).hexdigest()
