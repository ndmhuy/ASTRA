"""Conversation orchestration over deterministic ports and explicit mock boundaries."""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from .capabilities import Action, ActionPlan, CapabilityRegistry
from .jobs import MockJobManager, PendingChangeLedger
from .knowledge import FixtureAppKnowledgeProvider
from .models import (
    ConversationState,
    TeacherIntakeDraft,
    TrustedApproval,
    TurnRequest,
    TurnResponse,
)
from .requirements import (
    DraftEvaluationPort,
    FixtureRequirementsProvider,
    MockDraftEvaluationPort,
    RequirementsProvider,
    apply_descriptor_defaults,
)
from .understanding import understand


class ConversationOrchestrator:
    """In-memory Phase 1 core. No backend, UI, model, or network calls are performed."""

    def __init__(
        self,
        requirements: RequirementsProvider | None = None,
        evaluator: DraftEvaluationPort | None = None,
        jobs: MockJobManager | None = None,
        registry: CapabilityRegistry | None = None,
    ):
        self.requirements = requirements or FixtureRequirementsProvider()
        self.evaluator = evaluator or MockDraftEvaluationPort()
        self.jobs = jobs or MockJobManager()
        self.registry = registry or CapabilityRegistry()
        self.knowledge = FixtureAppKnowledgeProvider()
        self.ledger = PendingChangeLedger()
        self.sessions: dict[str, ConversationState] = {}

    def _state(self, request: TurnRequest) -> ConversationState:
        state = self.sessions.get(request.conversation_id)
        if state is None:
            descriptor = self.requirements.get_descriptor()
            state = ConversationState(
                conversation_id=request.conversation_id,
                workspace_session_id=request.workspace_session_id,
                draft=TeacherIntakeDraft(
                    draft_id=f"draft-{uuid5(NAMESPACE_URL, request.conversation_id).hex[:12]}",
                    conversation_id=request.conversation_id,
                    workspace_session_id=request.workspace_session_id,
                    requirements_schema_version=descriptor.schema_version,
                ),
            )
            self.sessions[request.conversation_id] = state
        return state

    def _response(
        self,
        request: TurnRequest,
        state: ConversationState,
        kind: str,
        reply: str,
        **data,
    ) -> TurnResponse:
        response = TurnResponse(
            request_id=request.request_id,
            conversation_id=request.conversation_id,
            kind=kind,
            reply=reply,
            data=data,
            mock=True,
        )
        state.processed_requests[request.request_id] = response
        return response

    def handle_turn(self, request: TurnRequest) -> TurnResponse:
        state = self._state(request)
        prior = state.processed_requests.get(request.request_id)
        if prior:
            return prior
        parsed = understand(request.message)
        descriptor = self.requirements.get_descriptor()
        apply_descriptor_defaults(state.draft, descriptor, request.request_id)

        if state.active_job:
            refreshed = self.jobs.snapshot(state.active_job.job_id)
            if refreshed:
                state.active_job = refreshed

        if "job_status" in parsed.intents:
            if not state.active_job:
                return self._response(
                    request, state, "reply", "Không có job tạo đề nào đang được theo dõi."
                )
            job = state.active_job
            if job.status == "unknown":
                text = (
                    "Trạng thái mock hiện chưa xác định; mình không đoán tiến độ "
                    "hoặc tự khởi động lại."
                )
            else:
                counts = ""
                if job.completed_items is not None and job.total_items is not None:
                    counts = f" ({job.completed_items}/{job.total_items} mục)"
                text = (
                    f"MOCK: job đang ở trạng thái {job.status}, "
                    f"bước {job.stage or 'chưa rõ'}{counts}."
                )
            return self._response(request, state, "reply", text, job=job.model_dump(mode="json"))

        if "app_help" in parsed.intents:
            fact = self.knowledge.answer(parsed.normalized_text)
            return self._response(request, state, "reply", fact["answer"], knowledge=fact)

        if "cancel_pending_edit" in parsed.intents and state.active_job:
            count = self.ledger.cancel_question(
                state.pending_changes, parsed.display_question_index
            )
            return self._response(
                request,
                state,
                "reply",
                f"Đã hủy {count} yêu cầu sửa đang chờ; job đang chạy không bị thay đổi.",
                cancelled=count,
            )

        if "difficulty_remark" in parsed.intents and state.active_job:
            return self._response(
                request,
                state,
                "clarification",
                "Thầy cô có muốn mình ghi nhận yêu cầu sửa câu này không? "
                "Hiện mình chưa tạo thay đổi từ một nhận xét.",
                pending_change_count=len(state.pending_changes),
            )

        if "explicit_edit" in parsed.intents and state.active_job:
            question_id = None
            kind = "structural"
            if parsed.display_question_index is not None:
                kind = "question"
                question_id = request.screen_context.question_index_map.get(
                    parsed.display_question_index
                )
            change = self.ledger.add(
                state.pending_changes,
                conversation_id=request.conversation_id,
                workspace_session_id=request.workspace_session_id,
                job_id=state.active_job.job_id,
                origin_message_id=request.request_id,
                instruction=request.message,
                kind=kind,
                display_question_index=parsed.display_question_index,
                question_id=question_id,
            )
            if change.status == "needs_target":
                reply = (
                    "Đã lưu ghi chú nhưng chưa xác định được ID ổn định của câu; "
                    "cần chọn đúng câu trước khi đề xuất sửa."
                )
            else:
                reply = "Đã ghi nhận yêu cầu ở sổ thay đổi MOCK; chưa áp dụng vào job đang chạy."
            return self._response(
                request, state, "reply", reply, pending_change=change.model_dump(mode="json")
            )

        if (
            "generate_exam" in parsed.intents
            and state.active_job
            and state.active_job.status == "active"
        ):
            return self._response(
                request,
                state,
                "reply",
                "Workspace này đang có một job MOCK hoạt động; mình không khởi động "
                "hoặc tự xếp hàng đề thứ hai.",
                active_job_id=state.active_job.job_id,
            )

        if "navigate_library" in parsed.intents:
            if not self.registry.enabled("ui.navigate", request.screen_context):
                return self._response(
                    request,
                    state,
                    "reply",
                    "Điều hướng bằng hội thoại hiện chưa được cài trong executor của giao diện.",
                )
            plan = ActionPlan(
                plan_id=f"plan-{request.request_id}",
                conversation_id=request.conversation_id,
                expected_state_version=request.screen_context.state_version,
                actions=[
                    Action(
                        action_id=f"action-{request.request_id}",
                        capability_id="ui.navigate",
                        target="application",
                        params={"screen_id": "library"},
                    )
                ],
            )
            return self._response(
                request,
                state,
                "action_plan",
                "Mình sẽ mở Tủ đề sau khi executor xác nhận.",
                plan=plan.model_dump(mode="json"),
            )

        if "accept_preset" in parsed.intents:
            if not descriptor.presets:
                return self._response(
                    request, state, "reply", "Backend fixture không cung cấp preset phù hợp."
                )
            preset = descriptor.presets[0]
            state.draft.patch(
                preset.values,
                request.request_id,
                source="backend_preset",
                status="confirmed",
            )

        if parsed.slots:
            known = {field.key for field in descriptor.fields}
            state.draft.patch(
                {key: value for key, value in parsed.slots.items() if key in known},
                request.request_id,
            )
        if parsed.removed_topics:
            current = (
                list(state.draft.fields.get("topics").value)
                if "topics" in state.draft.fields
                else []
            )
            remaining = [topic for topic in current if topic not in parsed.removed_topics]
            state.draft.excluded_topics = sorted(
                set(state.draft.excluded_topics) | set(parsed.removed_topics)
            )
            state.draft.patch({"topics": remaining}, request.request_id)

        if "generate_exam" in parsed.intents or parsed.slots or "accept_preset" in parsed.intents:
            evaluation = self.evaluator.evaluate(state.draft, descriptor)
            if evaluation.status == "needs_input":
                labels = [
                    field.ask_label
                    for field in descriptor.fields
                    if field.key in evaluation.missing_fields
                ]
                suggestion = ""
                if evaluation.allowed_suggestions:
                    suggestion = " Nếu chưa biết chọn, có thể dùng preset fixture: " + "; ".join(
                        preset.label for preset in evaluation.allowed_suggestions
                    )
                return self._response(
                    request,
                    state,
                    "clarification",
                    "Thầy cô vui lòng cho biết: " + ", ".join(labels) + "." + suggestion,
                    missing_fields=evaluation.missing_fields,
                    suggestions=[item.model_dump() for item in evaluation.allowed_suggestions],
                    draft_revision=state.draft.revision,
                )
            if evaluation.status == "invalid":
                return self._response(
                    request,
                    state,
                    "clarification",
                    "Một số giá trị chưa hợp lệ theo descriptor fixture: "
                    + "; ".join(evaluation.validation_errors),
                    errors=evaluation.validation_errors,
                )
            if evaluation.status == "validated_ready":
                state.draft.normalized_preview = evaluation.normalized_preview
                state.draft.request_hash = evaluation.request_hash
                return self._response(
                    request,
                    state,
                    "confirmation",
                    "MOCK: yêu cầu đã đủ theo descriptor fixture. Cần một sự kiện "
                    "phê duyệt tin cậy khớp chính xác trước khi bắt đầu.",
                    draft_id=state.draft.draft_id,
                    draft_revision=state.draft.revision,
                    request_hash=evaluation.request_hash,
                    normalized_preview=evaluation.normalized_preview,
                    evaluation_source="mock",
                )

        if "chatter" in parsed.intents:
            return self._response(request, state, "reply", "Mình vẫn ở đây để hỗ trợ ASTRA.")
        return self._response(
            request,
            state,
            "clarification",
            "Mình chưa xác định được yêu cầu trong phạm vi ASTRA. Thầy cô muốn "
            "tạo đề, xem tiến độ hay hỏi về ứng dụng?",
        )

    def approve_and_start(self, approval: TrustedApproval):
        state = self.sessions.get(approval.conversation_id)
        if not state:
            raise ValueError("unknown conversation")
        draft = state.draft
        expected = (
            approval.workspace_session_id == state.workspace_session_id
            and approval.draft_id == draft.draft_id
            and approval.draft_revision == draft.revision
            and approval.request_hash == draft.request_hash
            and approval.requirements_schema_version == draft.requirements_schema_version
        )
        if not expected:
            raise ValueError("stale or mismatched trusted approval")
        key = f"generate:{approval.conversation_id}:{draft.draft_id}:{draft.revision}"
        receipt = self.jobs.start(state.workspace_session_id, key)
        state.active_job = self.jobs.snapshot(receipt.job_id)
        draft.approved_revision = draft.revision
        return receipt

    def complete_mock_job(self, conversation_id: str, final_package_available: bool = True):
        state = self.sessions[conversation_id]
        if not state.active_job:
            raise ValueError("no active job")
        state.active_job = self.jobs.update(
            state.active_job.job_id,
            status="completed",
            stage="mock_completed",
            final_package_available=final_package_available,
        )
        return {
            "job": state.active_job.model_dump(mode="json"),
            "proposed_edit_batch": self.ledger.consolidate(state.pending_changes)
            if final_package_available
            else [],
            "applied": False,
            "reason": "No registered backend edit capability exists",
        }
