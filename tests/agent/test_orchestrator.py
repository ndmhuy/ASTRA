import pytest

from exam_baseline.agent.models import TrustedApproval
from exam_baseline.agent.orchestrator import ConversationOrchestrator

from .helpers import request


def complete_draft(agent):
    first = agent.handle_turn(request("Tạo đề Toán lớp 12", "r1"))
    assert first.kind == "clarification"
    second = agent.handle_turn(request("20 câu, 45 phút, phần đạo hàm", "r2"))
    assert second.kind == "confirmation"
    return second


def approval_for(agent, **overrides):
    state = agent.sessions["c1"]
    values = dict(
        approval_id="approval-ui-1",
        conversation_id="c1",
        workspace_session_id="w1",
        draft_id=state.draft.draft_id,
        draft_revision=state.draft.revision,
        request_hash=state.draft.request_hash,
        requirements_schema_version=state.draft.requirements_schema_version,
        actor_id="teacher-1",
    )
    values.update(overrides)
    return TrustedApproval(**values)


def test_in01_in02_grouped_missing_and_slot_continuity():
    agent = ConversationOrchestrator()
    first = agent.handle_turn(request("Tạo đề Toán lớp 12"))
    assert first.kind == "clarification"
    assert first.data["missing_fields"] == ["topics", "question_count", "duration_minutes"]
    second = agent.handle_turn(request("20 câu, 45 phút, phần đạo hàm", "r2"))
    assert second.kind == "confirmation"
    fields = agent.sessions["c1"].draft.fields
    assert fields["subject"].value == "mathematics"
    assert fields["grade"].value == 12


def test_in03_preset_requires_explicit_acceptance():
    agent = ConversationOrchestrator()
    response = agent.handle_turn(request("Tạo đề Toán lớp 12, phần đạo hàm"))
    assert response.data["suggestions"]
    assert "question_count" not in agent.sessions["c1"].draft.fields
    accepted = agent.handle_turn(request("Chọn gợi ý mẫu", "r2"))
    assert accepted.kind == "confirmation"
    assert agent.sessions["c1"].draft.fields["question_count"].status == "confirmed"


def test_complete_is_only_mock_validated():
    agent = ConversationOrchestrator()
    response = complete_draft(agent)
    assert response.data["evaluation_source"] == "mock"
    assert "MOCK" in response.reply
    assert agent.sessions["c1"].active_job is None


def test_trusted_approval_must_match_exact_revision_and_hash():
    agent = ConversationOrchestrator()
    complete_draft(agent)
    with pytest.raises(ValueError, match="stale"):
        agent.approve_and_start(approval_for(agent, request_hash="old"))


def test_approval_starts_exactly_one_mock_job():
    agent = ConversationOrchestrator()
    complete_draft(agent)
    approval = approval_for(agent)
    first = agent.approve_and_start(approval)
    second = agent.approve_and_start(approval)
    assert first == second
    assert first.source == "mock"


def test_app_help_and_status_continue_during_job():
    agent = ConversationOrchestrator()
    complete_draft(agent)
    agent.approve_and_start(approval_for(agent))
    help_response = agent.handle_turn(request("ASTRA làm được gì?", "r3"))
    status_response = agent.handle_turn(request("Đang làm đến đâu?", "r4"))
    assert "đề xuất" in help_response.reply
    assert "MOCK" in status_response.reply


def test_second_generation_in_active_workspace_is_blocked():
    agent = ConversationOrchestrator()
    complete_draft(agent)
    receipt = agent.approve_and_start(approval_for(agent))
    response = agent.handle_turn(request("Tạo thêm một đề Toán", "r3"))
    assert response.data["active_job_id"] == receipt.job_id
    assert "không khởi động" in response.reply


def test_duplicate_turn_returns_identical_response():
    agent = ConversationOrchestrator()
    turn = request("Tạo đề Toán lớp 12", "same")
    assert agent.handle_turn(turn) == agent.handle_turn(turn)


def test_correction_preserves_unrelated_fields_and_invalidates_hash():
    agent = ConversationOrchestrator()
    complete_draft(agent)
    old_revision = agent.sessions["c1"].draft.revision
    response = agent.handle_turn(request("À thôi đổi còn 15 câu", "r3"))
    draft = agent.sessions["c1"].draft
    assert response.kind == "confirmation"
    assert draft.fields["grade"].value == 12
    assert draft.fields["question_count"].value == 15
    assert draft.revision > old_revision


def test_unknown_input_has_no_action():
    response = ConversationOrchestrator().handle_turn(request("xyzzy"))
    assert response.kind == "clarification"
    assert "plan" not in response.data


def test_workspace_identity_is_pinned():
    agent = ConversationOrchestrator()
    agent.handle_turn(request("Tạo đề Toán lớp 12", workspace="w1"))
    assert agent.sessions["c1"].workspace_session_id == "w1"
