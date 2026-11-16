import pytest

from exam_baseline.agent.capabilities import ActionPlan, CapabilityRegistry, MockCapabilityExecutor
from exam_baseline.agent.models import ScreenContext
from exam_baseline.agent.orchestrator import ConversationOrchestrator
from exam_baseline.agent.service import AgentService, ExecutionFeedback

from .helpers import request

ALL_UI_ACTIONS = [
    "ui.navigate",
    "ui.session.create",
    "ui.exam.open_setup",
    "ui.sidebar.set_collapsed",
]


def ui_context():
    return ScreenContext(
        screen_id="workspace",
        state_version=7,
        workspace_session_id="w1",
        available_actions=ALL_UI_ACTIONS,
    )


@pytest.mark.parametrize(
    ("message", "capability_id", "params"),
    [
        ("Mở Tủ đề", "ui.navigate", {"screen_id": "library"}),
        ("Mở mục Soạn đề", "ui.navigate", {"screen_id": "create"}),
        ("Về màn hình chính", "ui.navigate", {"screen_id": "welcome"}),
        ("Tạo một không gian làm việc mới", "ui.session.create", {"mode": "custom"}),
        ("Mở thiết lập đề", "ui.exam.open_setup", {"workspace_session_id": "w1"}),
        ("Thu gọn menu", "ui.sidebar.set_collapsed", {"collapsed": True}),
        ("Mở rộng menu", "ui.sidebar.set_collapsed", {"collapsed": False}),
    ],
)
def test_m2_intent_produces_one_strict_ui_action(message, capability_id, params):
    agent = ConversationOrchestrator(registry=CapabilityRegistry.local_ui())
    response = agent.handle_turn(request(message, context=ui_context()))
    plan = ActionPlan.model_validate(response.data["plan"])
    assert response.kind == "action_plan"
    assert len(plan.actions) == 1
    assert plan.actions[0].capability_id == capability_id
    assert plan.actions[0].params == params


@pytest.mark.parametrize(
    ("message", "expected_reply"),
    [
        ("Mở Tủ đề", "Đã mở Tủ đề."),
        ("Tạo một không gian làm việc mới", "Đã tạo bản nháp mới."),
        ("Mở thiết lập đề", "Đã mở phần thiết lập đề."),
        ("Thu gọn menu", "Đã thu gọn menu."),
    ],
)
def test_m2_receipt_is_observed_before_final_reply(message, expected_reply):
    registry = CapabilityRegistry.local_ui()
    service = AgentService(ConversationOrchestrator(registry=registry))
    turn = request(message, context=ui_context())
    response = service.turn(turn)
    plan = ActionPlan.model_validate(response.data["plan"])
    receipts = MockCapabilityExecutor(registry).execute(plan, ui_context())
    final = service.feedback(
        ExecutionFeedback(
            feedback_id="feedback-1",
            conversation_id="c1",
            workspace_session_id="w1",
            original_request_id="r1",
            results=receipts,
        )
    )
    assert final.reply == expected_reply


def test_forged_success_for_session_creation_is_rejected():
    registry = CapabilityRegistry.local_ui()
    service = AgentService(ConversationOrchestrator(registry=registry))
    response = service.turn(request("Tạo một bản nháp mới", context=ui_context()))
    plan = ActionPlan.model_validate(response.data["plan"])
    receipts = MockCapabilityExecutor(registry).execute(plan, ui_context())
    receipts[0].data = {}
    with pytest.raises(ValueError, match="SESSION_CREATION_NOT_OBSERVED"):
        service.feedback(
            ExecutionFeedback(
                feedback_id="feedback-forged",
                conversation_id="c1",
                workspace_session_id="w1",
                original_request_id="r1",
                results=receipts,
            )
        )
