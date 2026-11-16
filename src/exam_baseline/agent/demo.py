"""Reproducible offline vertical slice. Every external boundary is marked MOCK."""

from __future__ import annotations

import json

from .models import ScreenContext, TrustedApproval, TurnRequest
from .orchestrator import ConversationOrchestrator


def run_demo() -> list[dict]:
    agent = ConversationOrchestrator()
    context = ScreenContext(
        screen_id="workspace",
        state_version=1,
        workspace_session_id="ws-demo",
        question_index_map={3: "question-stable-42"},
    )
    trace: list[dict] = []

    def turn(request_id: str, message: str):
        response = agent.handle_turn(
            TurnRequest(
                request_id=request_id,
                conversation_id="conv-demo",
                workspace_session_id="ws-demo",
                message=message,
                screen_context=context,
            )
        )
        trace.append({"input": message, "response": response.model_dump(mode="json")})
        return response

    turn("req-1", "Tạo đề Toán lớp 12")
    turn("req-2", "Chọn gợi ý mẫu, phần đạo hàm")
    state = agent.sessions["conv-demo"]
    approval = TrustedApproval(
        approval_id="approval-from-trusted-mock-ui",
        conversation_id="conv-demo",
        workspace_session_id="ws-demo",
        draft_id=state.draft.draft_id,
        draft_revision=state.draft.revision,
        request_hash=state.draft.request_hash or "",
        requirements_schema_version=state.draft.requirements_schema_version,
        actor_id="teacher-fixture",
    )
    receipt = agent.approve_and_start(approval)
    trace.append(
        {
            "trusted_mock_approval": approval.model_dump(),
            "start_receipt": receipt.model_dump(mode="json"),
        }
    )
    turn("req-3", "ASTRA làm được gì?")
    turn("req-4", "Đang làm đến đâu?")
    turn("req-5", "Câu 3 khó quá")
    turn("req-6", "Sửa câu 3 dễ hơn")
    turn("req-7", "Đổi còn 15 câu")
    turn("req-8", "Thôi giữ câu 3")
    turn("req-9", "Tạo thêm một đề Toán")
    trace.append({"mock_completion": agent.complete_mock_job("conv-demo")})
    return trace


def main() -> int:
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
