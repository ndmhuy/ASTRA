"""Real local UI/job boundary; explicit synthetic HTTP completions, no live AI."""

import asyncio
import json
import threading
import time
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from exam_baseline.agent.contracts import VERSION, Decision
from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest
from tests.api.test_ui_jobs import PAYLOAD, retrieval, wait
from tests.thpt.test_generation import Scripted


def test_native_ui_uses_worker_wire_and_chat_stays_responsive(tmp_path, monkeypatch):
    for name, value in {
        "ASTRA_MAS_TRANSPORT": "worker",
        "ASTRA_MAS_FORWARDING_ENABLED": "true",
        "ASTRA_MAS_CALLER_TOKEN": "a" * 64,
        "ASTRA_MAS_WORKER_URL": "https://mas.example",
    }.items():
        monkeypatch.setenv(name, value)
    original_client = httpx.AsyncClient
    started, release = threading.Event(), threading.Event()
    observed = []
    scripted = {
        role: Scripted(role, False) for role in ("composer", "illustrator", "solver", "reviewer")
    }

    async def transport(request):
        assert str(request.url) == "https://mas.example/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer " + "a" * 64
        role = request.headers["X-Astra-MAS-Stage"]
        body = json.loads(request.content)
        observed.append(role)
        if role == "composer" and not started.is_set():
            started.set()
            while not release.is_set():
                await asyncio.sleep(0.01)
        result = await scripted[role].complete(
            CompletionRequest(
                body["messages"][0]["content"],
                body["messages"][1]["content"],
                body["response_format"]["json_schema"]["schema"],
            )
        )
        return httpx.Response(
            200,
            json={
                "id": "fixture",
                "model": body["model"],
                "choices": [{"finish_reason": "stop", "message": {"content": result.text}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            },
        )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(**kwargs, transport=httpx.MockTransport(transport)),
    )

    async def chat(_turn):
        return Decision(kind="answer", guidance="start")

    settings = Settings(
        _env_file=None,
        provider="worker_mas",
        model="gemini-fixture",
        base_url="https://mas.example/v1",
        token_limit_field="max_tokens",
    )
    app = create_app(
        settings, ui_output_root=tmp_path, rag_retriever=retrieval, agent_interpreter=chat
    )
    with TestClient(app) as client:
        try:
            health = client.get("/api/health").json()
            assert health["demoMode"] is False and health["providerConfigured"] is True
            response = client.post(
                "/api/exams/generate",
                json=PAYLOAD,
                headers={"Idempotency-Key": "worker-transport-fixture"},
            )
            assert response.status_code == 202
            job = response.json()["jobId"]
            assert started.wait(timeout=5)
            before = time.monotonic()
            reply = client.post(
                "/agent/turn",
                headers={"X-Astra-Agent": VERSION},
                json={
                    "schemaVersion": VERSION,
                    "clientMessageId": str(uuid4()),
                    "workspaceId": str(uuid4()),
                    "message": "synthetic concurrent chat",
                    "context": {"screen": "workspace", "setup": False},
                },
            )
            assert reply.status_code == 200 and time.monotonic() - before < 1
        finally:
            release.set()
        assert wait(client, job)["status"] == "completed"
        package = client.get(f"/api/exams/{job}").json()
        assert len(package["questions"]) == 22 and not package["approved"]
        assert observed.count("reviewer") == 1
        assert set(observed) == set(scripted)
        assert not app.state.ui_jobs.get(job)["report"].get("demo_mode", False)
