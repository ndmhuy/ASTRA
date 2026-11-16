from exam_baseline.agent.jobs import MockJobManager
from exam_baseline.agent.models import ScreenContext
from exam_baseline.agent.orchestrator import ConversationOrchestrator

from .helpers import request
from .test_orchestrator import approval_for, complete_draft


def active_agent():
    agent = ConversationOrchestrator()
    complete_draft(agent)
    agent.approve_and_start(approval_for(agent))
    return agent


def test_job04_remark_does_not_queue_edit():
    agent = active_agent()
    response = agent.handle_turn(request("Câu 3 khó quá", "r3"))
    assert response.kind == "clarification"
    assert agent.sessions["c1"].pending_changes == []


def test_job05_maps_display_index_to_stable_id():
    agent = active_agent()
    context = ScreenContext(
        screen_id="workspace",
        state_version=2,
        workspace_session_id="w1",
        question_index_map={3: "q-stable-42"},
    )
    response = agent.handle_turn(request("Sửa câu 3 dễ hơn", "r3", context))
    assert response.data["pending_change"]["question_id"] == "q-stable-42"
    assert response.data["pending_change"]["status"] == "pending"


def test_job06_never_guesses_question_id():
    agent = active_agent()
    response = agent.handle_turn(request("Sửa câu 3 dễ hơn", "r3"))
    change = response.data["pending_change"]
    assert change["question_id"] is None
    assert change["status"] == "needs_target"


def test_structural_change_supersedes_prior_structural_change():
    agent = active_agent()
    agent.handle_turn(request("Đổi còn 15 câu", "r3"))
    agent.handle_turn(request("Đổi còn 10 câu", "r4"))
    statuses = [entry.status for entry in agent.sessions["c1"].pending_changes]
    assert statuses == ["superseded", "pending"]


def test_cancel_pending_question_edit():
    agent = active_agent()
    context = ScreenContext(
        screen_id="workspace",
        state_version=2,
        workspace_session_id="w1",
        question_index_map={3: "q42"},
    )
    agent.handle_turn(request("Sửa câu 3 dễ hơn", "r3", context))
    response = agent.handle_turn(request("Thôi giữ câu 3", "r4", context))
    assert response.data["cancelled"] == 1
    assert agent.sessions["c1"].pending_changes[0].status == "cancelled"


def test_completion_requires_final_package_before_batch():
    agent = active_agent()
    agent.handle_turn(request("Đổi còn 15 câu", "r3"))
    without_package = agent.complete_mock_job("c1", final_package_available=False)
    assert without_package["proposed_edit_batch"] == []
    assert not without_package["applied"]


def test_completion_proposes_but_does_not_apply_batch():
    agent = active_agent()
    agent.handle_turn(request("Đổi còn 15 câu", "r3"))
    result = agent.complete_mock_job("c1")
    assert len(result["proposed_edit_batch"]) == 1
    assert not result["applied"]


def test_active_job_limit_is_per_workspace_not_global():
    jobs = MockJobManager()
    first = jobs.start("w1", "key-w1")
    second = jobs.start("w2", "key-w2")
    assert first.job_id != second.job_id
    assert jobs.active_for("w1").job_id == first.job_id
    assert jobs.active_for("w2").job_id == second.job_id
