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
    subject: str | None = None
    grade: int | None = None
    range_type: str = "knowledge"
    start: int | None = None
    end: int | None = None
    keywords: tuple[str, ...] = ()
    edition: str | None = None
    series: str | None = None
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


def normalize_part(part: str | None) -> str:
    """Normalize exam part identifiers (P1/P2/P3 or mcq/true_false/short_answer)."""
    if not isinstance(part, str) or not part.strip():
        raise Gap("invalid_request", "part must be a nonempty string (P1, P2, or P3).")
    cleaned = part.strip()
    if cleaned in CONFIG["parts"]:
        return cleaned
    lowered = cleaned.lower()
    if lowered in CONFIG["part_aliases"]:
        return CONFIG["part_aliases"][lowered]
    raise Gap("invalid_request", f"Unsupported exam part: {part!r}. Expected P1, P2, or P3.")


def normalize_level(level: str | None) -> str | None:
    """Normalize cognitive level labels (NB/TH/VD/VDC)."""
    if level is None:
        return None
    if not isinstance(level, str) or not level.strip():
        raise Gap("invalid_request", "level must be a nonempty string when provided.")
    cleaned = level.strip().upper()
    if cleaned in CONFIG["accepted_request_levels"]:
        return cleaned
    lowered = level.strip().lower()
    if lowered in CONFIG["level_aliases"]:
        return CONFIG["level_aliases"][lowered]
    raise Gap(
        "invalid_request",
        f"Unsupported cognitive level: {level!r}. Expected one of {', '.join(CONFIG['accepted_request_levels'])}.",
    )


@dataclass(frozen=True)
class MatrixQuestionSpec:
    """Per-question or per-group retrieval specification sent by MAS Orchestrator."""

    question_id: str
    part: str
    topic: str
    learning_objective: str | None = None
    level: str | None = None
    statement_levels: dict[str, str] | None = None
    group_id: str | None = None
    needs: tuple[str, ...] = tuple(CONFIG["retrieval_needs"])
    curriculum_unit_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.question_id, str) or not self.question_id.strip():
            raise Gap("invalid_request", "question_id must be a nonempty string.")
        if not isinstance(self.topic, str) or not self.topic.strip():
            raise Gap("invalid_request", f"topic must be a nonempty string for {self.question_id}.")
        canonical_part = normalize_part(self.part)
        object.__setattr__(self, "part", canonical_part)
        canonical_level = normalize_level(self.level)
        object.__setattr__(self, "level", canonical_level)
        if self.learning_objective is not None and not isinstance(self.learning_objective, str):
            raise Gap(
                "invalid_request", f"learning_objective must be a string for {self.question_id}."
            )
        if self.group_id is not None and (
            not isinstance(self.group_id, str) or not self.group_id.strip()
        ):
            raise Gap(
                "invalid_request", f"group_id must be a nonempty string for {self.question_id}."
            )
        if self.statement_levels is not None:
            if not isinstance(self.statement_levels, dict) or not self.statement_levels:
                raise Gap(
                    "invalid_request",
                    f"statement_levels must be a nonempty dict for {self.question_id}.",
                )
            normalized_statements = {}
            for sub_key, sub_lvl in self.statement_levels.items():
                if (
                    not isinstance(sub_key, str)
                    or sub_key.strip().lower() not in CONFIG["p2_statement_keys"]
                ):
                    raise Gap(
                        "invalid_request",
                        f"Invalid P2 statement key {sub_key!r} in {self.question_id}; expected a, b, c, or d.",
                    )
                norm_lvl = normalize_level(sub_lvl)
                if norm_lvl is None:
                    raise Gap(
                        "invalid_request",
                        f"Statement {sub_key!r} in {self.question_id} requires a cognitive level.",
                    )
                normalized_statements[sub_key.strip().lower()] = norm_lvl
            object.__setattr__(self, "statement_levels", normalized_statements)
        if not self.needs or any(n not in CONFIG["retrieval_needs"] for n in self.needs):
            raise Gap(
                "invalid_request",
                f"needs must be a subset of {', '.join(CONFIG['retrieval_needs'])}.",
            )
        object.__setattr__(self, "needs", tuple(dict.fromkeys(self.needs)))
        if (
            not isinstance(self.curriculum_unit_ids, tuple)
            or len(self.curriculum_unit_ids) > CONFIG["max_top_k"]
            or any(
                not isinstance(unit, str) or not unit.strip() for unit in self.curriculum_unit_ids
            )
            or len(set(self.curriculum_unit_ids)) != len(self.curriculum_unit_ids)
        ):
            raise Gap("invalid_request", "curriculum_unit_ids must contain distinct lesson IDs.")


@dataclass(frozen=True)
class MatrixRetrievalRequest:
    """Full exam matrix or batch question context request from MAS Orchestrator."""

    questions: tuple[MatrixQuestionSpec, ...]
    subject: str = "toan"
    matrix_id: str = "toan-thpt-matrix"
    vdc_policy: str = CONFIG["default_vdc_policy"]
    include_unknown_level: bool = False
    allow_curriculum_only: bool = False
    max_observations: int = CONFIG["default_max_observations_per_question"]
    max_examples: int = CONFIG["default_max_examples_per_question"]
    max_curriculum_units: int = CONFIG["default_max_curriculum_units_per_question"]
    mode: str = CONFIG["default_mode"]
    schema_version: str = VERSION

    def __post_init__(self):
        if self.schema_version != VERSION:
            raise Gap("unsupported_schema", "Unsupported request schema_version.")
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise Gap("invalid_request", "subject must be a nonempty string.")
        subj = self.subject.strip().lower()
        canonical_subj = None
        for k, aliases in CONFIG["subjects"].items():
            if subj == k or subj in aliases:
                canonical_subj = k
                break
        if canonical_subj is None:
            raise Gap("invalid_request", f"Unsupported subject: {self.subject!r}.")
        object.__setattr__(self, "subject", canonical_subj)
        if not self.questions or len(self.questions) > CONFIG["max_matrix_questions"]:
            raise Gap(
                "invalid_request",
                f"questions must contain between 1 and {CONFIG['max_matrix_questions']} items.",
            )
        seen_ids = set()
        for q in self.questions:
            if not isinstance(q, MatrixQuestionSpec):
                raise Gap("invalid_request", "Each question must be a MatrixQuestionSpec.")
            if q.question_id in seen_ids:
                raise Gap("invalid_request", f"Duplicate question_id in matrix: {q.question_id!r}.")
            seen_ids.add(q.question_id)
        if self.vdc_policy not in CONFIG["vdc_policies"]:
            raise Gap(
                "invalid_request",
                f"vdc_policy must be one of {', '.join(CONFIG['vdc_policies'])}.",
            )
        if type(self.include_unknown_level) is not bool:
            raise Gap("invalid_request", "include_unknown_level must be a boolean.")
        if type(self.allow_curriculum_only) is not bool:
            raise Gap("invalid_request", "allow_curriculum_only must be a boolean.")
        for field_name in ("max_observations", "max_examples", "max_curriculum_units"):
            val = getattr(self, field_name)
            if type(val) is not int or not 1 <= val <= CONFIG["max_top_k"]:
                raise Gap(
                    "invalid_request",
                    f"{field_name} must be an integer between 1 and {CONFIG['max_top_k']}.",
                )
        if self.mode not in CONFIG["modes"]:
            raise Gap("invalid_request", f"mode must be one of {', '.join(CONFIG['modes'])}.")


@dataclass
class QuestionContext:
    """Retrieved topic pack and provenance bound to a specific question_id."""

    question_id: str
    group_id: str | None
    status: str
    requested: dict[str, Any]
    resolved_level: dict[str, Any]
    matched_topic_packs: list[dict[str, Any]] = field(default_factory=list)
    curriculum_knowledge: list[dict[str, Any]] = field(default_factory=list)
    construction_patterns: list[dict[str, Any]] = field(default_factory=list)
    construction_observations: list[dict[str, Any]] = field(default_factory=list)
    p2_statement_coverage: dict[str, Any] | None = None
    examples: list[dict[str, Any]] = field(default_factory=list)
    common_mistakes: list[dict[str, Any]] = field(default_factory=list)
    provenance_summary: dict[str, Any] = field(default_factory=dict)
    reference_material_text: str = ""
    gaps: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class MatrixRetrievalResponse:
    """Top-level response for Orchestrator matrix context retrieval."""

    status: str = "gap"
    matrix_id: str = "toan-thpt-matrix"
    subject: str = "toan"
    release_info: dict[str, Any] = field(default_factory=dict)
    question_contexts: list[dict[str, Any]] = field(default_factory=list)
    mas_intake_rag: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    gaps: list[dict[str, str]] = field(default_factory=list)
    schema_version: str = VERSION
    config_sha256: str = hashlib.sha256(
        json.dumps(CONFIG, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    def to_dict(self):
        return asdict(self)
