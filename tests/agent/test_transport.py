import pytest
from fastapi.testclient import TestClient

from exam_baseline.agent.capabilities import ActionPlan, MockCapabilityExecutor
from exam_baseline.agent.http import create_agent_app
from exam_baseline.agent.orchestrator import ConversationOrchestrator
from exam_baseline.agent.service import AgentService

from .helpers import request
from .test_capabilities import context, enabled_registry


def setup():
    registry = enabled_registry()
    service = AgentService(ConversationOrchestrator(registry=registry))
    client = TestClient(create_agent_app(service))
    turn = request("Mở Tủ đề", context=context())
    response = client.post("/agent/turns", json=turn.model_dump()).json()
    plan = ActionPlan.model_validate(response["data"]["plan"])
    receipts = MockCapabilityExecutor(registry).execute(plan, context())
    feedback = {
        "feedback_id": "f1",
        "conversation_id": "c1",
        "workspace_session_id": "w1",
        "original_request_id": "r1",
        "results": [item.model_dump() for item in receipts],
    }
    return client, turn, feedback


def test_http_full_receipt_loop_and_replay():
    client, turn, feedback = setup()
    first = client.post("/agent/execution-results", json=feedback)
    assert first.status_code == 200
    assert first.json()["reply"] == "Đã mở Tủ đề."
    assert client.post("/agent/execution-results", json=feedback).json() == first.json()
    assert client.post("/agent/turns", json=turn.model_dump()).status_code == 200


@pytest.mark.parametrize(
    "field", ["workspace_session_id", "conversation_id", "original_request_id"]
)
def test_feedback_wrong_address_rejected(field):
    client, _, feedback = setup()
    feedback[field] = "wrong"
    assert client.post("/agent/execution-results", json=feedback).status_code == 409


@pytest.mark.parametrize("field", ["action_id", "plan_id"])
def test_forged_receipt_identity_rejected(field):
    client, _, feedback = setup()
    feedback["results"][0][field] = "unknown"
    assert client.post("/agent/execution-results", json=feedback).status_code == 409


def test_success_requires_observed_navigation():
    client, _, feedback = setup()
    feedback["results"][0]["data"] = {"screen_id": "welcome"}
    assert client.post("/agent/execution-results", json=feedback).status_code == 409


def test_request_id_cannot_be_reused_for_another_message():
    client, turn, _ = setup()
    turn.message = "Tạo đề Toán"
    assert client.post("/agent/turns", json=turn.model_dump()).status_code == 409


def test_workspace_switch_rejected_before_draft_mutation():
    service = AgentService()
    service.turn(request("Tạo đề Toán lớp 12"))
    with pytest.raises(ValueError, match="workspace"):
        service.turn(request("15 câu", "r2", workspace="w2"))
    assert "question_count" not in service.agent.sessions["c1"].draft.fields


def test_session_limit_and_json_validation():
    service = AgentService(max_sessions=1, max_turns=1)
    service.turn(request("xin chào"))
    with pytest.raises(ValueError, match="TURN_LIMIT"):
        service.turn(request("xin chào", "r2"))
    with pytest.raises(ValueError, match="SESSION_LIMIT"):
        service.turn(request("xin chào", conversation="c2"))
    client = TestClient(create_agent_app())
    payload = request("xin chào").model_dump()
    payload["approved"] = True
    assert client.post("/agent/turns", json=payload).status_code == 422


def test_openapi_exposes_real_transport_contracts():
    schema = create_agent_app().openapi()
    assert "/agent/turns" in schema["paths"]
    assert "ExecutionFeedback" in schema["components"]["schemas"]


def test_health_endpoint_identifies_offline_agent():
    response = TestClient(create_agent_app()).get("/agent/health")
    assert response.status_code == 200
    assert response.json() == {
        "service": "astra-agent",
        "schema_version": "agent-turn/0.1",
        "status": "ok",
    }
