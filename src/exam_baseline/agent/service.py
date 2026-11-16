"""Bounded, serialized transport service and correlated execution feedback loop.

No UI effects run here. Feedback is an adapter observation, not authentication.
"""

from threading import RLock

from pydantic import Field

from .capabilities import ActionPlan, ActionReceipt
from .models import AgentModel, TurnRequest, TurnResponse
from .orchestrator import ConversationOrchestrator


class ExecutionFeedback(AgentModel):
    feedback_id: str = Field(min_length=1, max_length=100)
    conversation_id: str = Field(min_length=1, max_length=100)
    workspace_session_id: str = Field(min_length=1, max_length=100)
    original_request_id: str = Field(min_length=1, max_length=100)
    results: list[ActionReceipt] = Field(min_length=1, max_length=5)


class AgentService:
    """Single-process memory; limits fail closed rather than evicting replay records."""

    def __init__(self, agent=None, max_sessions=100, max_turns=200):
        self.agent = agent or ConversationOrchestrator()
        self.max_sessions = max_sessions
        self.max_turns = max_turns
        self._lock = RLock()
        self._requests: dict[tuple[str, str], TurnRequest] = {}
        self._feedback: dict[tuple[str, str], tuple[ExecutionFeedback, TurnResponse]] = {}
        self._settled: dict[tuple[str, str], tuple[ExecutionFeedback, TurnResponse]] = {}

    def turn(self, request: TurnRequest) -> TurnResponse:
        with self._lock:
            key = (request.conversation_id, request.request_id)
            previous = self._requests.get(key)
            if previous is not None:
                if previous != request:
                    raise ValueError("REQUEST_ID_REUSED")
                return (
                    self.agent.sessions[request.conversation_id]
                    .processed_requests[request.request_id]
                    .model_copy(deep=True)
                )
            state = self.agent.sessions.get(request.conversation_id)
            if state is None and len(self.agent.sessions) >= self.max_sessions:
                raise ValueError("SESSION_LIMIT")
            if state is not None and len(state.processed_requests) >= self.max_turns:
                raise ValueError("TURN_LIMIT")
            response = self.agent.handle_turn(request)
            self._requests[key] = request.model_copy(deep=True)
            return response.model_copy(deep=True)

    def feedback(self, feedback: ExecutionFeedback) -> TurnResponse:
        with self._lock:
            feedback_key = (feedback.conversation_id, feedback.feedback_id)
            prior = self._feedback.get(feedback_key)
            if prior:
                if prior[0] != feedback:
                    raise ValueError("FEEDBACK_ID_REUSED")
                return prior[1].model_copy(deep=True)
            key = (feedback.conversation_id, feedback.original_request_id)
            request = self._requests.get(key)
            if request is None or request.workspace_session_id != feedback.workspace_session_id:
                raise ValueError("UNKNOWN_OR_WRONG_TARGET")
            response = self.agent.sessions[feedback.conversation_id].processed_requests[
                feedback.original_request_id
            ]
            if response.kind != "action_plan":
                raise ValueError("NO_PENDING_PLAN")
            plan = ActionPlan.model_validate(response.data["plan"])
            expected_ids = [action.action_id for action in plan.actions]
            if [result.action_id for result in feedback.results] != expected_ids:
                raise ValueError("ACTION_RECEIPTS_MISMATCH")
            failed = False
            for action, result in zip(plan.actions, feedback.results, strict=True):
                if result.plan_id != plan.plan_id:
                    raise ValueError("PLAN_MISMATCH")
                if failed and result.status != "skipped":
                    raise ValueError("DEPENDENCY_SEQUENCE_INVALID")
                if result.status == "skipped" and not failed:
                    raise ValueError("UNEXPECTED_SKIPPED_ACTION")
                if result.status == "success":
                    if result.state_version < plan.expected_state_version:
                        raise ValueError("STALE_RECEIPT")
                    if (
                        action.capability_id == "ui.navigate"
                        and result.data.get("screen_id") != action.params["screen_id"]
                    ):
                        raise ValueError("NAVIGATION_NOT_OBSERVED")
                    if action.capability_id == "ui.session.create":
                        created = result.data.get("created_workspace_session_id")
                        if not isinstance(created, str) or not created:
                            raise ValueError("SESSION_CREATION_NOT_OBSERVED")
                        if result.data.get("mode") != action.params["mode"]:
                            raise ValueError("SESSION_MODE_MISMATCH")
                    if action.capability_id == "ui.exam.open_setup" and (
                        result.data.get("dialog_visible") is not True
                        or result.data.get("workspace_session_id")
                        != action.params["workspace_session_id"]
                    ):
                        raise ValueError("SETUP_NOT_OBSERVED")
                    if action.capability_id == "ui.sidebar.set_collapsed" and (
                        result.data.get("collapsed") != action.params["collapsed"]
                    ):
                        raise ValueError("SIDEBAR_STATE_NOT_OBSERVED")
                else:
                    failed = True
            settled = self._settled.get(key)
            if settled:
                if settled[0].results != feedback.results:
                    raise ValueError("PLAN_ALREADY_SETTLED")
                return settled[1].model_copy(deep=True)
            successes = sum(result.status == "success" for result in feedback.results)
            if failed:
                reply = f"Đã thực hiện {successes} thao tác; các thao tác còn lại chưa hoàn tất."
            else:
                action = plan.actions[-1]
                result = feedback.results[-1]
                if action.capability_id == "ui.navigate":
                    labels = {
                        "welcome": "màn hình chính",
                        "create": "mục Soạn đề",
                        "library": "Tủ đề",
                        "workspace": "không gian làm việc",
                    }
                    label = labels[action.params["screen_id"]]
                    reply = f"Đã mở {label}."
                elif action.capability_id == "ui.session.create":
                    reply = "Đã tạo bản nháp mới."
                elif action.capability_id == "ui.exam.open_setup":
                    reply = "Đã mở phần thiết lập đề."
                else:
                    reply = "Đã thu gọn menu." if result.data["collapsed"] else "Đã mở rộng menu."
            final = TurnResponse(
                request_id=feedback.original_request_id,
                conversation_id=feedback.conversation_id,
                kind="reply",
                reply=reply,
                data={"results": [item.model_dump() for item in feedback.results]},
            )
            record = (feedback.model_copy(deep=True), final)
            self._feedback[feedback_key] = record
            self._settled[key] = record
            return final.model_copy(deep=True)
