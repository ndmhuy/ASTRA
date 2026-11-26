"""Actual FastAPI jobs and Agent routes; synthetic MAS runner, no upstream inference."""

import asyncio
import threading
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from exam_baseline.agent.contracts import Decision
from exam_baseline.agent.semantics import normalize_frame
from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import ProviderError
from tests.api.test_ui_jobs import PAYLOAD, retrieval


def test_chat_and_generation_failure_are_independent(tmp_path):
    entered, release = threading.Event(), threading.Event()
    chat_unavailable = False

    async def simulated_mas(request, output, progress):
        progress("composer")
        entered.set()
        for _ in range(500):
            if release.is_set():
                raise ProviderError("synthetic_mas_failure", "Synthetic isolated MAS failure")
            await asyncio.sleep(0.01)
        raise AssertionError("Test failed to release simulated MAS")

    async def interpret(turn):
        if chat_unavailable:
            return Decision(kind="temporarily_unavailable", reasonCode="quota")
        return normalize_frame(
            {"dialogueAct": "GUIDANCE", "goals": [{"goal": "APPLICATION_GUIDANCE"}]}
        )

    app = create_app(
        Settings.for_offline(),
        ui_output_root=tmp_path,
        ui_runner=simulated_mas,
        rag_retriever=retrieval,
        agent_interpreter=interpret,
    )
    with TestClient(app) as client:
        started = client.post(
            "/api/exams/generate",
            json=PAYLOAD,
            headers={"Idempotency-Key": "synthetic-concurrent-job"},
        )
        assert started.status_code == 202
        job = started.json()["jobId"]
        assert entered.wait(3)
        submitted = app.state.ui_jobs.get(job)["request"]

        def chat():
            return client.post(
                "/agent/turn",
                headers={
                    "X-Astra-Agent": "astra-intent-v1",
                    "X-Astra-Semantic": "astra-semantic-v1",
                },
                json={
                    "schemaVersion": "astra-intent-v1",
                    "clientMessageId": str(uuid4()),
                    "workspaceId": str(uuid4()),
                    "message": "Synthetic concurrent guidance",
                    "context": {"screen": "workspace", "setup": False, "status": "generating"},
                },
            )

        response = chat()
        assert response.status_code == 200
        assert response.json()["frame"]["goals"][0]["goal"] == "APPLICATION_GUIDANCE"
        assert not release.is_set()
        assert client.get(f"/api/exams/{job}/status").json()["status"] not in {
            "completed",
            "failed",
        }
        chat_unavailable = True
        assert chat().json()["decision"]["reasonCode"] == "quota"
        assert app.state.ui_jobs.get(job)["request"] == submitted
        assert client.get(f"/api/exams/{job}/status").json()["status"] != "failed"
        release.set()
        for _ in range(100):
            if client.get(f"/api/exams/{job}/status").json()["status"] == "failed":
                break
            time.sleep(0.01)
        else:
            raise AssertionError("Simulated MAS failure did not finish")
        chat_unavailable = False
        assert chat().json()["frame"]["dialogueAct"] == "GUIDANCE"
