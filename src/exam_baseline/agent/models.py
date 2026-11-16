"""Versioned runtime contracts for the independent conversational agent core."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RequirementField(AgentModel):
    key: str = Field(min_length=1)
    ask_label: str = Field(min_length=1)
    value_type: Literal["string", "integer", "string_list", "enum"]
    required: bool = False
    default: Any | None = None
    allowed_values: list[Any] = Field(default_factory=list)
    minimum: int | None = None
    maximum: int | None = None
    depends_on: list[str] = Field(default_factory=list)


class RequirementPreset(AgentModel):
    preset_id: str
    label: str
    values: dict[str, Any]
    source: str
    version: str


class RequirementsDescriptor(AgentModel):
    schema_version: str
    capability_id: Literal["exam.generate"] = "exam.generate"
    availability: Literal["mock", "implemented", "unavailable"]
    fields: list[RequirementField]
    presets: list[RequirementPreset] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_fields(self):
        keys = [field.key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("requirement field keys must be unique")
        known = set(keys)
        for preset in self.presets:
            if not set(preset.values) <= known:
                raise ValueError("preset contains fields outside the descriptor")
        return self


FieldSource = Literal["user", "backend_default", "backend_preset"]
FieldStatus = Literal["provided", "suggested", "confirmed"]


class CollectedField(AgentModel):
    value: Any
    source: FieldSource
    status: FieldStatus
    updated_by_message_id: str
    revision: int = Field(ge=1)


class TeacherIntakeDraft(AgentModel):
    draft_id: str
    conversation_id: str
    workspace_session_id: str
    requirements_schema_version: str
    revision: int = Field(default=0, ge=0)
    fields: dict[str, CollectedField] = Field(default_factory=dict)
    excluded_topics: list[str] = Field(default_factory=list)
    normalized_preview: dict[str, Any] | None = None
    request_hash: str | None = None
    approved_revision: int | None = None

    def patch(
        self,
        values: dict[str, Any],
        message_id: str,
        *,
        source: FieldSource = "user",
        status: FieldStatus = "provided",
    ) -> bool:
        changed = False
        next_revision = self.revision + 1
        for key, value in values.items():
            current = self.fields.get(key)
            if (
                current
                and current.value == value
                and current.source == source
                and current.status == status
            ):
                continue
            self.fields[key] = CollectedField(
                value=value,
                source=source,
                status=status,
                updated_by_message_id=message_id,
                revision=next_revision,
            )
            changed = True
        if changed:
            self.revision = next_revision
            self.normalized_preview = None
            self.request_hash = None
            self.approved_revision = None
        return changed


EvaluationStatus = Literal[
    "needs_input", "validated_ready", "invalid", "unsupported", "unavailable"
]


class DraftEvaluation(AgentModel):
    status: EvaluationStatus
    source: Literal["mock", "backend"]
    requirements_schema_version: str
    missing_fields: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    allowed_suggestions: list[RequirementPreset] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    normalized_preview: dict[str, Any] | None = None
    request_hash: str | None = None


Intent = Literal[
    "generate_exam",
    "job_status",
    "app_help",
    "navigate_library",
    "explicit_edit",
    "difficulty_remark",
    "cancel_pending_edit",
    "accept_preset",
    "chatter",
    "unknown",
]


class UnderstandingResult(AgentModel):
    original_text: str
    normalized_text: str
    intents: list[Intent]
    slots: dict[str, Any] = Field(default_factory=dict)
    removed_topics: list[str] = Field(default_factory=list)
    display_question_index: int | None = None
    confidence: float = Field(ge=0, le=1)


class JobSnapshot(AgentModel):
    job_id: str
    workspace_session_id: str
    status: Literal["active", "completed", "failed", "unknown"]
    stage: str | None = None
    completed_items: int | None = None
    total_items: int | None = None
    final_package_available: bool = False
    source: Literal["mock", "backend"] = "mock"
    revision: int = Field(default=1, ge=1)


PendingStatus = Literal[
    "pending", "needs_target", "superseded", "cancelled", "submitted", "applied", "failed"
]


class PendingChange(AgentModel):
    change_id: str
    conversation_id: str
    workspace_session_id: str
    job_id: str
    exam_id: str | None = None
    question_id: str | None = None
    display_question_index: int | None = None
    instruction: str
    kind: Literal["question", "structural"]
    status: PendingStatus
    origin_message_id: str
    revision: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScreenContext(AgentModel):
    screen_id: Literal["welcome", "create", "library", "workspace"]
    state_version: int = Field(ge=0)
    workspace_session_id: str | None = None
    selected_question_id: str | None = None
    question_index_map: dict[int, str] = Field(default_factory=dict)
    available_actions: list[str] = Field(default_factory=list)


class TurnRequest(AgentModel):
    schema_version: Literal["agent-turn/0.1"] = "agent-turn/0.1"
    request_id: str
    conversation_id: str
    workspace_session_id: str
    message: str = Field(min_length=1, max_length=10_000)
    screen_context: ScreenContext


class TurnResponse(AgentModel):
    schema_version: Literal["agent-turn/0.1"] = "agent-turn/0.1"
    request_id: str
    conversation_id: str
    kind: Literal["reply", "clarification", "confirmation", "action_plan"]
    reply: str
    data: dict[str, Any] = Field(default_factory=dict)
    mock: bool = True


class TrustedApproval(AgentModel):
    approval_id: str
    conversation_id: str
    workspace_session_id: str
    draft_id: str
    draft_revision: int
    request_hash: str
    requirements_schema_version: str
    actor_id: str


class StartReceipt(AgentModel):
    job_id: str
    workspace_session_id: str
    idempotency_key: str
    accepted_at: datetime
    source: Literal["mock", "backend"] = "mock"


class ConversationState(AgentModel):
    conversation_id: str
    workspace_session_id: str
    draft: TeacherIntakeDraft
    active_job: JobSnapshot | None = None
    pending_changes: list[PendingChange] = Field(default_factory=list)
    processed_requests: dict[str, TurnResponse] = Field(default_factory=dict)


class SemanticUnderstandingPort:
    """Optional candidate extractor; implementations never authorize effects."""

    def extract_candidates(self, text: str) -> UnderstandingResult | None:  # pragma: no cover
        raise NotImplementedError
