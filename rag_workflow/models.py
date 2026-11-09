"""Single definitions for the request, corpus passage and response contracts."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

CONFIG = json.loads(Path(__file__).with_name("config.json").read_text(encoding="utf-8"))
VERSION = CONFIG["schema_version"]


class Gap(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RetrievalRequest:
    query_text: str
    top_k: int = CONFIG["default_top_k"]
    schema_version: str = VERSION
    edition: str | None = None
    mode: str = CONFIG["default_mode"]

    def __post_init__(self):
        if self.schema_version != VERSION:
            raise Gap("unsupported_schema", "Unsupported request schema_version.")
        if not isinstance(self.query_text, str) or not self.query_text.strip():
            raise Gap("invalid_request", "query_text must be a nonempty string.")
        if len(self.query_text) > CONFIG["max_query_chars"]:
            raise Gap("query_over_limit", "Query exceeds the configured character limit.")
        if type(self.top_k) is not int or not 1 <= self.top_k <= CONFIG["max_top_k"]:
            raise Gap("invalid_request", "top_k is outside the configured range.")
        if self.edition is not None and (
            not isinstance(self.edition, str) or not self.edition.strip()
        ):
            raise Gap("invalid_request", "edition must be a nonempty string.")
        if not isinstance(self.mode, str) or self.mode not in CONFIG["modes"]:
            raise Gap(
                "invalid_request",
                f"mode must be one of {', '.join(CONFIG['modes'])}.",
            )


@dataclass(frozen=True)
class ResolvedScope:
    subject: str
    grade: int | None
    range_type: str
    start: int | None
    end: int | None
    keywords: tuple[str, ...]
    edition: str | None
    series: str | None = CONFIG["series"]
    accented_keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    subject: str
    grade: int
    title: str
    content: str
    chapter: int | None
    lesson: int | None
    semester: int | None
    series: str
    edition: str
    source_id: str
    source_locator: str
    source_version: str
    content_sha256: str
    approval_status: str
    approved_by: str | None
    approved_on: str | None
    rights_evidence: str
    evidence_class: str
    allow_local_retrieval: bool
    allow_quotation: bool
    content_kind: str = "knowledge"
    schema_version: str = VERSION

    def __post_init__(self):
        required = (
            "document_id",
            "subject",
            "title",
            "content",
            "series",
            "edition",
            "source_id",
            "source_locator",
            "source_version",
            "rights_evidence",
        )
        if any(
            not isinstance(getattr(self, k), str) or not getattr(self, k).strip() for k in required
        ):
            raise ValueError("Document text and provenance fields must be nonempty strings.")
        if self.schema_version != VERSION or self.subject not in CONFIG["subjects"]:
            raise ValueError("Unsupported document schema or canonical subject.")
        if type(self.grade) is not int or self.grade not in CONFIG["grades"]:
            raise ValueError("Unsupported grade.")
        for name in ("chapter", "lesson", "semester"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError(f"Invalid {name}.")
        if self.semester not in (None, 1, 2):
            raise ValueError("Invalid semester.")
        if self.approval_status not in (
            "draft",
            "ocr-draft",
            "teacher-checked",
            "approved",
            "superseded",
        ):
            raise ValueError("Unknown approval status.")
        if self.approval_status == "approved" and any(
            not isinstance(v, str) or not v.strip() for v in (self.approved_by, self.approved_on)
        ):
            raise ValueError("Approval needs a named reviewer and date.")
        if self.approval_status == "approved":
            date.fromisoformat(self.approved_on)
        if self.evidence_class not in ("official", "provincial", "third_party", "synthetic"):
            raise ValueError("Evidence class must preserve source authority.")
        if type(self.allow_local_retrieval) is not bool or type(self.allow_quotation) is not bool:
            raise ValueError("Rights permissions must be explicit booleans.")
        if self.content_kind not in ("knowledge", "curriculum"):
            raise ValueError("Reference items, keys and audit artifacts need separate role views.")
        if self.content_sha256 != hashlib.sha256(self.content.encode("utf-8")).hexdigest():
            raise ValueError("Content checksum mismatch.")


@dataclass(frozen=True)
class CorpusDocument:
    """Internal search projection; approval and source records stay separate."""

    document_id: str
    subject: str
    grade: int | None
    chapter: int | None
    lesson: int | None
    semester: int | None
    title: str
    content: str
    content_kind: str
    source_locator: str
    source_version: str
    approval_status: str
    evidence_class: str
    provenance: dict
    edition: str = "existing-corpus"
    schema_version: str = VERSION
    usage: str = "internal prototype; not teacher-approved"

    def __post_init__(self):
        if self.subject not in CONFIG["subjects"] or self.content_kind not in (
            "curriculum",
            "exam",
        ):
            raise ValueError("Unsupported corpus subject or content kind.")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (
                self.document_id,
                self.title,
                self.content,
                self.source_locator,
                self.source_version,
            )
        ):
            raise ValueError("Corpus text and source fields must be nonempty strings.")
        if self.grade is not None and (
            type(self.grade) is not int or self.grade not in CONFIG["grades"]
        ):
            raise ValueError("Unsupported corpus grade.")
        for value in (self.chapter, self.lesson, self.semester):
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError("Invalid corpus range metadata.")
        if self.semester not in (None, 1, 2):
            raise ValueError("Invalid corpus semester.")

    @property
    def content_sha256(self):
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


@dataclass
class RetrievalResponse:
    status: str = "gap"
    resolved_scope: ResolvedScope | None = None
    documents: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[dict[str, str]] = field(default_factory=list)
    corpus_sha256: str | None = None
    corpus_snapshot: str | None = None
    mode: str = CONFIG["default_mode"]
    ranking_method: str = CONFIG["ranking_version"]
    schema_version: str = VERSION
    config_sha256: str = hashlib.sha256(
        json.dumps(CONFIG, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    def to_dict(self):
        return asdict(self)
