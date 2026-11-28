"""Chat observes real persisted state through read-only synthetic fixtures."""

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jsonschema import ValidationError, validate

from exam_baseline.agent.context import ground_turn
from exam_baseline.agent.native import semantic_context
from exam_baseline.agent.v3 import FrameV3, TurnV3, semantic_schema
from exam_baseline.api.app import create_app
from exam_baseline.config import Settings

HEADERS = {
    "X-Astra-Agent": "astra-intent-v1",
    "X-Astra-Semantic": "astra-semantic-v3",
    "X-Astra-Dialogue": "grounded-v1",
}


def turn(workspace):
    return {
        "schemaVersion": "astra-intent-v1",
        "workspaceId": workspace,
        "clientMessageId": str(uuid4()),
        "message": "Synthetic state inquiry",
        "context": {
            "screen": "workspace",
            "setup": False,
            "status": "complete",
            "grounded": {"lifecycle": "completed"},
        },
    }


def seed(client, app, subject, status="running"):
    workspace = str(uuid4())
    assert (
        client.put(
            f"/api/workspaces/{workspace}",
            json={
                "revision": 0,
                "mode": "template",
                "title": "Selected from form",
                "draft": "",
                "messages": [],
            },
        ).status_code
        == 200
    )
    data = {
        "status": status,
        "revision": 1,
        "approved": False,
        "rawQuestions": [],
        "request": {
            "subject": subject,
            "itemCount": 28,
            "durationMinutes": 50,
            "formatId": "thpt-physics",
            "prompt": "Keep synthetic requirements",
        },
        "progress": {"completedItems": 3, "totalItems": 28, "message": "Synthetic Composer"},
    }
    job, _ = app.state.ui_jobs.store.create(str(uuid4()), "fixture", data, workspace)
    return workspace, job


def test_backend_overrides_claimed_completion_and_replay_remains_idempotent(tmp_path):
    observed = []

    async def interpret(value):
        observed.append(value)
        return FrameV3(dialogueAct="QUESTION", goals=[{"goal": "READ_PROGRESS"}])

    app = create_app(Settings.for_offline(), agent_interpreter=interpret, ui_output_root=tmp_path)
    with TestClient(app) as client:
        workspace, job = seed(client, app, "Vật Lý")
        other, _ = seed(client, app, "Tiếng Anh")
        request = turn(workspace)
        assert client.post("/agent/turn", json=request, headers=HEADERS).status_code == 200
        facts = observed[0].context.grounded.backend
        assert facts.current.lifecycle == "running" and facts.current.subject == "Vật Lý"
        assert (facts.current.count, facts.current.minutes, facts.current.completed) == (28, 50, 3)
        assert facts.activeCount == 2 and {f.subject for f in facts.active} == {
            "Vật Lý",
            "Tiếng Anh",
        }
        assert not facts.current.approved
        # Same client message remains a replay, even while the observed job progresses.
        changed = {**job, "progress": {"completedItems": 4, "totalItems": 28}}
        app.state.ui_jobs.store.save(changed)
        assert client.post("/agent/turn", json=request, headers=HEADERS).status_code == 200
        assert len(observed) == 1
        assert client.post("/agent/turn", json=turn(workspace), headers=HEADERS).status_code == 200
        assert observed[1].context.grounded.backend.current.completed == 4
        assert app.state.ui_jobs.store.get(job["jobId"])["status"] == "running"
        assert other != workspace


def test_completed_state_and_reply_are_read_only_and_opt_in(tmp_path):
    async def interpret(value):
        assert value.context.grounded.backend.current.lifecycle == "completed"
        return FrameV3(dialogueAct="CONVERSATION", reply="Cảm ơn bạn đã trao đổi.")

    app = create_app(Settings.for_offline(), agent_interpreter=interpret, ui_output_root=tmp_path)
    with TestClient(app) as client:
        workspace, job = seed(client, app, "Vật Lý", "completed")
        response = client.post("/agent/turn", json=turn(workspace), headers=HEADERS)
        assert response.json()["frame"]["reply"] == "Cảm ơn bạn đã trao đổi."
        legacy_headers = {k: v for k, v in HEADERS.items() if k != "X-Astra-Dialogue"}
        legacy = client.post("/agent/turn", json=turn(workspace), headers=legacy_headers)
        assert "reply" not in legacy.json()["frame"]
        stored = app.state.ui_jobs.store.get(job["jobId"])
        assert not stored["approved"] and stored["status"] == "completed"


def test_ui_state_projection_matches_chat_and_requires_no_inference(tmp_path):
    async def forbidden(value):
        raise AssertionError("State GET must not interpret or generate anything")

    app = create_app(Settings.for_offline(), agent_interpreter=forbidden, ui_output_root=tmp_path)
    with TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        workspace, job = seed(client, app, "Vật Lý")
        response = client.get(f"/agent/workspace-state?workspace_id={workspace}")
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        data = response.json()
        assert data["schemaVersion"] == "astra-workspace-state-v1"
        assert data["current"]["subject"] == "Vật Lý" and data["current"]["completed"] == 3
        assert data["activeCount"] == 1
        assert "jobId" not in response.text and app.state.ui_jobs.store.get(job["jobId"]) == job


def test_model_context_does_not_include_executable_ids_or_raw_secret(tmp_path):
    class Store:
        def list_workspaces(self):
            return [
                {
                    "id": "a",
                    "title": "Fixture sk-private-test-credential",
                    "jobId": "secret-job-id",
                    "generationId": "secret-job-id",
                    "generationStatus": "running",
                    "generationState": {"completedItems": 1},
                }
            ]

        def get(self, identifier):
            return {
                "request": {
                    "subject": "Vật Lý",
                    "itemCount": 28,
                    "durationMinutes": 50,
                    "prompt": "token=private-value",
                }
            }

    payload = TurnV3.model_validate(turn(str(uuid4())))
    payload.workspaceId = "a"
    data = semantic_context(ground_turn(payload, Store()))
    serialized = json.dumps(data)
    assert "private-test-credential" not in serialized and "private-value" not in serialized
    assert "secret-job-id" not in serialized


def test_full_goal_schema_rejects_cross_goal_parameters_and_accepts_dialogue():
    schema = semantic_schema()
    validate({"dialogueAct": "CONVERSATION", "reply": "Mình sẵn sàng hỗ trợ bạn."}, schema)
    validate(
        {
            "dialogueAct": "QUESTION",
            "goals": [{"goal": "READ_PROGRESS", "parameters": {"scope": "active"}}],
        },
        schema,
    )
    with pytest.raises(ValidationError):
        validate(
            {
                "dialogueAct": "QUESTION",
                "goals": [{"goal": "READ_PROGRESS", "parameters": {"subject": "Vật Lý"}}],
            },
            schema,
        )
