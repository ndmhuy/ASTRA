"""Real SQLite/files with deterministic providers; no real AI or HTTP transport."""

import json
import time
from threading import Event

import pytest
from fastapi.testclient import TestClient

from exam_baseline.agent.contracts import Decision
from exam_baseline.core.checkpoints import response_checkpoint
from exam_baseline.core.contracts import ProviderError
from exam_baseline.thpt.models import Illustrations
from exam_baseline.ui.errors import UiError
from exam_baseline.ui.generation_state import ExecutionLost, GenerationState
from exam_baseline.ui.storage import JobStore
from tests.api.test_agent_turn import HEADERS, payload
from tests.api.test_stop_generation import _start, _workspace
from tests.api.test_ui_jobs import fixture_app, wait


def until(client, job_id, status):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        current = client.get(f"/api/exams/{job_id}/status").json()
        if current["status"] == status:
            return current
        time.sleep(0.01)
    pytest.fail(f"Did not observe {status}: {current}")


@pytest.mark.parametrize("abandoned", [False, True])
def test_pause_inflight_persists_response_and_restart_resumes_same_job_without_repetition(
    tmp_path, abandoned
):
    async def interpret(_turn):
        return Decision(kind="answer", guidance="capabilities")

    app, providers = fixture_app(tmp_path, agent_interpreter=interpret)
    entered, release = Event(), Event()
    composer = providers["composer"]
    complete = composer.complete

    async def hold_p2(prompt):
        import asyncio

        if json.loads(prompt.user)["part"] == "P2":
            entered.set()
            while not release.is_set():
                await asyncio.sleep(0.01)
        return await complete(prompt)

    composer.complete = hold_p2
    with TestClient(app) as client:
        job_id = _start(client, _workspace(client), "pause-and-restore")
        assert entered.wait(5)
        url = f"/api/exams/{job_id}"
        try:
            receipt = client.post(url + "/pause", json={"executionVersion": 1})
            assert receipt.status_code == 202 and receipt.json()["status"] == "pausing"
            assert client.get("/api/health").status_code == 200
            assert client.post("/agent/turn", json=payload(), headers=HEADERS).status_code == 200
            assert len(composer.calls) == 1  # Only P1 has returned yet.
        finally:
            release.set()
        paused = until(client, job_id, "paused")
        assert paused["completedItems"] == 16
        assert paused["completedOperations"] == 2
        assert [call["part"] for call in composer.calls] == ["P1", "P2"]
        assert app.state.ui_jobs.store.list_versions(job_id) == []
        saved = client.get("/api/workspaces").json()["workspaces"][0]["generationState"]
        assert saved["status"] == "paused" and saved["completedItems"] == 16
        assert saved["completedOperations"] == 2
        assert client.post("/agent/turn", json=payload(), headers=HEADERS).status_code == 200
    if abandoned:
        # Simulate the durable record left by a killed executor, with actual response files.
        store = app.state.ui_jobs.store
        store.save(
            {
                **store.get(job_id),
                "status": "running",
                "executionOwner": "dead-process",
                "executionLeaseUntil": time.time() - 1,
            }
        )
    restarted, next_pool = fixture_app(tmp_path)
    with TestClient(restarted) as client:
        assert client.get(url + "/status").json()["status"] == (
            "interrupted" if abandoned else "paused"
        )
        assert not any(provider.calls for provider in next_pool.values())
        first = client.post(url + "/resume", json={"executionVersion": 1})
        duplicate = client.post(url + "/resume", json={"executionVersion": 1})
        assert first.status_code == duplicate.status_code == 202
        assert first.json()["jobId"] == duplicate.json()["jobId"] == job_id
        assert first.json()["executionVersion"] == 2
        assert client.post(url + "/pause", json={"executionVersion": 1}).status_code == 409
        assert wait(client, job_id)["status"] == "completed"
        assert [call["part"] for call in next_pool["composer"].calls] == ["P3"]
        with restarted.state.ui_jobs.store.connect() as db:
            assert db.execute("SELECT count(*) FROM jobs").fetchone()[0] == 1
        assert len(restarted.state.ui_jobs.store.list_versions(job_id)) == 1


def test_an_old_paused_job_cannot_resume_over_a_replacement_workspace_job(tmp_path):
    import asyncio

    app, pool = fixture_app(tmp_path)
    with TestClient(app) as client:
        app.state.ui_jobs.capacity = asyncio.Semaphore(0)
        workspace = _workspace(client)
        first = _start(client, workspace, "old-paused")
        assert (
            client.post(f"/api/exams/{first}/pause", json={"executionVersion": 1}).json()["status"]
            == "paused"
        )
        second = _start(client, workspace, "replacement")
        stale = client.post(f"/api/exams/{first}/resume", json={"executionVersion": 1})
        assert stale.status_code == 409 and stale.json()["error"]["code"] == "stale_generation"
        assert client.get(f"/api/exams/{second}/status").json()["status"] == "queued"
        assert not any(provider.calls for provider in pool.values())


def test_sqlite_lease_fences_duplicate_executors_abandoned_jobs_and_late_checkpoint_writes(
    tmp_path,
):
    store = JobStore(tmp_path / "jobs.sqlite3")
    clock = [100.0]
    state = GenerationState(store, clock=lambda: clock[0])
    job, _ = store.create(
        "fixture",
        "input-hash",
        {
            "status": "queued",
            "executionVersion": 1,
            "checkpointVersion": 1,
            "executionLeaseUntil": 130.0,
            "progress": {"completedItems": 0, "statusMessage": "Queued"},
        },
    )
    job_id = job["jobId"]
    assert state.claim(job_id, 1, "first-owner")
    assert not state.claim(job_id, 1, "second-owner")
    state.recover()
    assert store.get(job_id)["status"] == "queued"  # A live queue lease is not abandoned.
    clock[0] = 131.0
    state.recover()
    assert store.get(job_id)["status"] == "interrupted"
    resumed, schedule = state.control(job_id, 1, "resume")
    assert schedule and resumed["executionVersion"] == 2
    assert state.claim(job_id, 2, "second-owner")
    path = tmp_path / job_id / "_generation/_internal/checkpoints/fixture.json"
    saved = response_checkpoint("operation", Illustrations())
    with pytest.raises(ExecutionLost):
        state.persist(job_id, 1, "first-owner", path, saved)
    assert not path.exists()
    state.persist(job_id, 2, "second-owner", path, saved)
    assert path.is_file()
    with pytest.raises(UiError, match="Phiên chạy"):
        state.control(job_id, 1, "pause")


def test_pausing_queued_work_makes_no_provider_calls_and_requires_versioned_control(tmp_path):
    import asyncio

    app, pool = fixture_app(tmp_path)
    with TestClient(app) as client:
        app.state.ui_jobs.capacity = asyncio.Semaphore(0)
        job_id = _start(client, _workspace(client), "pause-in-queue")
        url = f"/api/exams/{job_id}"
        assert client.post(url + "/pause").status_code == 422
        response = client.post(url + "/pause", json={"executionVersion": 1})
        assert response.json()["status"] == "paused"
        assert not any(provider.calls for provider in pool.values())


def test_pause_interrupts_retry_backoff_and_retry_after_survives_restart(tmp_path):
    app, pool = fixture_app(tmp_path)
    attempts = []

    async def unavailable(prompt):
        attempts.append(prompt)
        raise ProviderError(
            "provider_unavailable", "fake503", http_status=503, retry_after_seconds=5
        )

    pool["composer"].complete = unavailable
    with TestClient(app) as client:
        job_id = _start(client, _workspace(client), "pause-retry")
        url = f"/api/exams/{job_id}"
        until(client, job_id, "retrying")
        assert (
            client.post(url + "/pause", json={"executionVersion": 1}).json()["status"] == "pausing"
        )
        assert until(client, job_id, "paused")["retry"]["phase"] == "waiting"
        assert len(attempts) == 1
    restarted, next_pool = fixture_app(tmp_path)
    with TestClient(restarted) as client:
        result = client.post(url + "/resume", json={"executionVersion": 1})
        assert result.status_code == 429
        assert not any(provider.calls for provider in next_pool.values())


def test_bounded_provider_failures_pause_and_manual_retry_finishes_same_job(tmp_path):
    app, pool = fixture_app(tmp_path)
    original = pool["composer"].complete
    failures = []

    async def unavailable(prompt):
        failures.append(prompt)
        raise ProviderError("provider_unavailable", "fake503", http_status=503)

    pool["composer"].complete = unavailable
    with TestClient(app) as client:
        job_id = _start(client, _workspace(client), "recover-provider")
        state = until(client, job_id, "paused")
        assert len(failures) == 2 and state["error"]["code"] == "provider_unavailable"
        assert not pool["solver"].calls
        pool["composer"].complete = original
        response = client.post(f"/api/exams/{job_id}/retry", json={"executionVersion": 1})
        assert response.json()["jobId"] == job_id
        assert wait(client, job_id)["status"] == "completed"
        assert len(pool["composer"].calls) == 3
