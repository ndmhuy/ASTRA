from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class CapabilitySummary(CamelModel):
    id: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=300)
    status: Literal["available_real", "available_mock", "unavailable", "planned"]
    callable: bool = False
    requires_confirmation: bool = Field(default=False, alias="requiresConfirmation")


class SessionSummary(CamelModel):
    id: str
    title: str = Field(max_length=100)
    status: Literal["draft", "generating", "complete", "error"]
    created_at: str = Field(alias="createdAt")


class NoteSummary(CamelModel):
    id: str
    target_question: int | None = Field(default=None, alias="targetQuestion")
    requested_change: str = Field(alias="requestedChange", max_length=500)
    stable_question_id: str | None = Field(default=None, alias="stableQuestionId")
    status: Literal["pending", "approved", "applying", "applied", "failed", "cancelled"]


class ActiveJobSummary(CamelModel):
    id: str
    stage: str
    percent: int = Field(ge=0, le=100)
    source: Literal["real", "mock", "unknown"]


class UiContextSnapshot(CamelModel):
    workspace_id: str | None = Field(default=None, alias="workspaceId")
    screen: Literal["start", "workspace"]
    active_modal: str | None = Field(default=None, alias="activeModal")
    sidebar_collapsed: bool = Field(alias="sidebarCollapsed")
    state_version: int = Field(alias="stateVersion", ge=1)
    active_job: ActiveJobSummary | None = Field(default=None, alias="activeJob")
    exam_revision: int | None = Field(default=None, alias="examRevision")
    exam_id: str | None = Field(default=None, alias="examId")
    content_hash: str | None = Field(default=None, alias="contentHash")
    selected_question: dict[str, Any] | None = Field(default=None, alias="selectedQuestion")
    questions: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    view_mode: Literal["paper", "review", "pdf"] = Field(default="paper", alias="viewMode")
    preview: dict[str, Any] | None = None
    approved: bool = False
    setup: dict[str, Any] = Field(default_factory=dict)
    pending_confirmation: dict[str, Any] | None = Field(default=None, alias="pendingConfirmation")
    active_task: dict[str, Any] | None = Field(default=None, alias="activeTask")
    sessions: list[SessionSummary] = Field(default_factory=list, max_length=50)
    notes: list[NoteSummary] = Field(default_factory=list, max_length=50)
    capabilities: list[CapabilitySummary] = Field(default_factory=list, max_length=50)


class AgentTurnRequest(CamelModel):
    turn_id: str = Field(alias="turnId", min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
    context: UiContextSnapshot


class AgentDecision(CamelModel):
    kind: Literal["answer", "clarify", "unsupported", "propose_ui_action"]
    text: str = Field(min_length=1, max_length=1500)
    action_id: str | None = Field(default=None, alias="actionId", max_length=100)
    capability_id: str | None = Field(default=None, alias="capabilityId", max_length=80)
    expected_state_version: int | None = Field(default=None, alias="expectedStateVersion", ge=1)
    params: dict[str, Any] = Field(default_factory=dict)
    target: dict[str, Any] = Field(default_factory=dict)


class AgentTurnResponse(CamelModel):
    turn_id: str = Field(alias="turnId")
    decisions: list[AgentDecision] = Field(min_length=1, max_length=4)
    provider: Literal["offline", "gemini"]
    knowledge_status: Literal["verified_ui_registry_only", "approved_document"] = Field(
        alias="knowledgeStatus"
    )


class GeminiDecision(CamelModel):
    kind: Literal["answer", "clarify", "unsupported", "propose_ui_action"]
    text: str = Field(min_length=1, max_length=1000)
    capability_id: str | None = Field(default=None, alias="capabilityId", max_length=80)
    params: dict[str, Any] = Field(default_factory=dict)
    target: dict[str, Any] = Field(default_factory=dict)


class GeminiPlan(CamelModel):
    decisions: list[GeminiDecision] = Field(min_length=1, max_length=4)
