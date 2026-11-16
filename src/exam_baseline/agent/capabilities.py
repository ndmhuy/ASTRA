"""Strict data-driven capability planning and a receipt-based mock executor."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from .models import AgentModel, ScreenContext


class Capability(AgentModel):
    capability_id: str
    enabled: bool = False
    target: str
    required_params: list[str]
    allowed_params: list[str]


class Action(AgentModel):
    action_id: str
    capability_id: str
    target: str
    params: dict[str, Any]


class ActionPlan(AgentModel):
    schema_version: Literal["agent-actions/0.1"] = "agent-actions/0.1"
    plan_id: str
    conversation_id: str
    expected_state_version: int
    actions: list[Action] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def unique_action_ids(self):
        ids = [action.action_id for action in self.actions]
        if len(ids) != len(set(ids)):
            raise ValueError("action IDs must be unique")
        return self


class ActionReceipt(AgentModel):
    plan_id: str
    action_id: str
    status: Literal["success", "failed", "skipped"]
    error_code: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    state_version: int

    @model_validator(mode="after")
    def consistent_outcome(self):
        if (self.status == "success") != (self.error_code is None):
            raise ValueError("success requires no error; failure/skipped requires an error")
        return self


class CapabilityRegistry:
    def __init__(self, capabilities: list[Capability] | None = None):
        self.capabilities = {
            item.capability_id: item
            for item in (
                capabilities
                or [
                    Capability(
                        capability_id="ui.navigate",
                        enabled=False,
                        target="application",
                        required_params=["screen_id"],
                        allowed_params=["screen_id", "workspace_session_id"],
                    )
                ]
            )
        }

    @classmethod
    def local_ui(cls):
        """Capabilities installed by the reviewed local React adapter; no backend effects."""
        return cls(
            [
                Capability(
                    capability_id="ui.navigate",
                    enabled=True,
                    target="application",
                    required_params=["screen_id"],
                    allowed_params=["screen_id", "workspace_session_id"],
                ),
                Capability(
                    capability_id="ui.session.create",
                    enabled=True,
                    target="exam-sessions",
                    required_params=["mode"],
                    allowed_params=["mode"],
                ),
                Capability(
                    capability_id="ui.exam.open_setup",
                    enabled=True,
                    target="exam-setup",
                    required_params=["workspace_session_id"],
                    allowed_params=["workspace_session_id"],
                ),
                Capability(
                    capability_id="ui.sidebar.set_collapsed",
                    enabled=True,
                    target="main-navigation",
                    required_params=["collapsed"],
                    allowed_params=["collapsed"],
                ),
            ]
        )

    def enabled(self, capability_id: str, context: ScreenContext) -> bool:
        capability = self.capabilities.get(capability_id)
        return bool(
            capability and capability.enabled and capability_id in context.available_actions
        )

    def validate(self, action: Action, context: ScreenContext) -> str | None:
        capability = self.capabilities.get(action.capability_id)
        if not capability:
            return "UNKNOWN_CAPABILITY"
        if not self.enabled(action.capability_id, context):
            return "CAPABILITY_UNAVAILABLE"
        if action.target != capability.target:
            return "INVALID_PARAMS"
        keys = set(action.params)
        if not set(capability.required_params) <= keys or not keys <= set(
            capability.allowed_params
        ):
            return "INVALID_PARAMS"
        if action.capability_id == "ui.navigate":
            screen = action.params.get("screen_id")
            if screen not in {"welcome", "create", "library", "workspace"}:
                return "INVALID_PARAMS"
            has_workspace = bool(action.params.get("workspace_session_id"))
            if (screen == "workspace") != has_workspace:
                return "INVALID_PARAMS"
        elif action.capability_id == "ui.session.create":
            if action.params.get("mode") not in {"template", "custom"}:
                return "INVALID_PARAMS"
        elif action.capability_id == "ui.exam.open_setup":
            if (
                not isinstance(action.params.get("workspace_session_id"), str)
                or not action.params["workspace_session_id"]
            ):
                return "INVALID_PARAMS"
        elif action.capability_id == "ui.sidebar.set_collapsed":
            if not isinstance(action.params.get("collapsed"), bool):
                return "INVALID_PARAMS"
        return None


class MockCapabilityExecutor:
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.receipts: dict[tuple[str, str], ActionReceipt] = {}

    def execute(self, plan: ActionPlan, context: ScreenContext) -> list[ActionReceipt]:
        replay = [self.receipts.get((plan.plan_id, action.action_id)) for action in plan.actions]
        if all(replay):
            return [receipt for receipt in replay if receipt is not None]
        if plan.expected_state_version != context.state_version:
            first = plan.actions[0]
            return [
                ActionReceipt(
                    plan_id=plan.plan_id,
                    action_id=first.action_id,
                    status="failed",
                    error_code="STALE_CONTEXT",
                    state_version=context.state_version,
                )
            ]
        receipts: list[ActionReceipt] = []
        failed = False
        for action in plan.actions:
            key = (plan.plan_id, action.action_id)
            if key in self.receipts:
                receipts.append(self.receipts[key])
                continue
            if failed:
                receipt = ActionReceipt(
                    plan_id=plan.plan_id,
                    action_id=action.action_id,
                    status="skipped",
                    error_code="DEPENDENCY_FAILED",
                    state_version=context.state_version,
                )
            else:
                error = self.registry.validate(action, context)
                if error:
                    receipt = ActionReceipt(
                        plan_id=plan.plan_id,
                        action_id=action.action_id,
                        status="failed",
                        error_code=error,
                        state_version=context.state_version,
                    )
                    failed = True
                else:
                    if action.capability_id == "ui.navigate":
                        context.screen_id = action.params["screen_id"]
                        context.workspace_session_id = action.params.get("workspace_session_id")
                    context.state_version += 1
                    data: dict[str, Any]
                    if action.capability_id == "ui.navigate":
                        data = {
                            "screen_id": context.screen_id,
                            "workspace_session_id": context.workspace_session_id,
                        }
                    elif action.capability_id == "ui.session.create":
                        data = {
                            "created_workspace_session_id": "mock-created-session",
                            "mode": action.params["mode"],
                        }
                    elif action.capability_id == "ui.exam.open_setup":
                        data = {
                            "workspace_session_id": action.params["workspace_session_id"],
                            "dialog_visible": True,
                        }
                    else:
                        data = {"collapsed": action.params["collapsed"]}
                    receipt = ActionReceipt(
                        plan_id=plan.plan_id,
                        action_id=action.action_id,
                        status="success",
                        data=data,
                        state_version=context.state_version,
                    )
            self.receipts[key] = receipt
            receipts.append(receipt)
        return receipts
