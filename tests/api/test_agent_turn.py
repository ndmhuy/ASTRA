"""Test the local interpretation boundary without provider inference."""

from uuid import uuid4

from fastapi.testclient import TestClient

from exam_baseline.agent import admission
from exam_baseline.agent.contracts import VERSION, Decision, Intent
from exam_baseline.api.app import create_app
from exam_baseline.config import Settings

HEADERS = {"X-Astra-Agent": VERSION}


def payload(**changes):
    return {
        "schemaVersion": VERSION,
        "clientMessageId": str(uuid4()),
        "workspaceId": str(uuid4()),
        "message": "Xin mở phần thiết lập",
        "context": {"screen": "workspace", "setup": False},
        **changes,
    }


def test_admission_replay_boundary_and_limits(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(admission, "monotonic", lambda: clock[0])
    calls = []

    async def fixture(turn):
        calls.append(turn.clientMessageId)
        return Decision(kind="task", intents=[Intent(id="OPEN_SETUP", args={})])

    app = create_app(
        Settings(_env_file=None, provider="mock", model="mock-fixture-v1"),
        agent_interpreter=fixture,
        ui_output_root=tmp_path,
    )
    with TestClient(app) as client:
        endpoint = "/agent/turn"
        request = payload()
        assert client.post(endpoint, json=request).status_code == 403
        assert (
            client.post(
                endpoint, json=request, headers={**HEADERS, "Sec-Fetch-Site": "cross-site"}
            ).status_code
            == 403
        )
        assert (
            client.post(endpoint, json=payload(message="............"), headers=HEADERS).status_code
            == 422
        )
        assert (
            client.post(endpoint, content=b"x" * (128 * 1024 + 1), headers=HEADERS).status_code
            == 413
        )
        response = client.post(endpoint, json=request, headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["decision"]["intents"][0]["id"] == "OPEN_SETUP"
        assert client.post(endpoint, json=request, headers=HEADERS).json() == response.json()
        assert (
            client.post(endpoint, json={**request, "message": "Khác"}, headers=HEADERS).status_code
            == 409
        )
        assert len(calls) == 1
        for _ in range(3):
            assert client.post(endpoint, json=payload(), headers=HEADERS).status_code == 200
        assert client.post(endpoint, json=payload(), headers=HEADERS).status_code == 429
        for _ in range(8):
            clock[0] += 4.0
            assert client.post(endpoint, json=payload(), headers=HEADERS).status_code == 200
        limited = client.post(endpoint, json=payload(), headers=HEADERS)
        assert limited.status_code == 429
        assert int(limited.headers["Retry-After"]) > 0
