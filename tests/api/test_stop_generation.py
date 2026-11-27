import asyncio
import time
from threading import Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from exam_baseline.ui import jobs
from exam_baseline.ui.errors import UiError
from tests.api.test_ui_jobs import PAYLOAD, fixture_app, wait


def _workspace(client):
    workspace = str(uuid4())
    draft = {"title": "Stop fixture", "mode": "custom", "draft": "", "messages": [], "revision": 0}
    assert client.put(f"/api/workspaces/{workspace}", json=draft).is_success
    return workspace


def _start(client, workspace, key):
    result = client.post(
        "/api/exams/generate",
        params={"workspace_id": workspace},
        headers={"Idempotency-Key": key},
        json=PAYLOAD,
    )
    assert result.status_code == 202
    return result.json()["jobId"]


def test_stop_and_restart_discards_late_provider_result(tmp_path):
    app, providers = fixture_app(tmp_path)
    entered, interrupted, release = Event(), Event(), Event()
    composer = providers["composer"]
    complete = composer.complete

    async def slow_first(prompt):
        response = await complete(prompt)
        if not entered.is_set():
            entered.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                # Simulate a provider transport returning despite the cancelled await.
                interrupted.set()
                while not release.is_set():
                    await asyncio.sleep(0.01)
        return response

    composer.complete = slow_first
    with TestClient(app) as client:
        try:
            workspace = _workspace(client)
            old = _start(client, workspace, "first-generation")
            assert entered.wait(5)
            manager = app.state.ui_jobs
            old_task = manager.tasks[old]
            old_url = f"/api/exams/{old}"
            stopped = client.post(old_url + "/stop")
            assert stopped.json()["status"] == "cancelled"
            assert interrupted.wait(5)
            assert client.post(old_url + "/stop").json() == stopped.json()
            assert _start(client, workspace, "first-generation") == old
            new = _start(client, workspace, "new-generation")
            assert new != old
            assert wait(client, new)["status"] == "completed"
            before = {role: len(provider.calls) for role, provider in providers.items()}
            release.set()
            deadline = time.monotonic() + 5
            while not old_task.done() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert old_task.done()
            assert {role: len(provider.calls) for role, provider in providers.items()} == before
            assert client.get(old_url + "/status").json()["status"] == "cancelled"
            assert client.get(old_url).status_code == 409
            assert client.get(old_url + "/versions").status_code == 409
            assert manager.store.list_versions(old) == []
            assert "cancelled" in client.get(old_url + "/events").text
            assert not (tmp_path / old / "de_thi.tex").exists()
            assert client.get(f"/api/workspaces/{workspace}/versions").json()["currentJobId"] == new
            assert client.post(f"/api/exams/{new}/stop").json()["status"] == "completed"
            with pytest.raises(UiError, match="Phiên tạo đề đã kết thúc"):
                manager.store.save_version(
                    {**manager.get(old), "revision": 1, "status": "completed"}, b"late", "generated"
                )
        finally:
            release.set()


def test_stop_cancels_all_parallel_composer_calls(tmp_path, monkeypatch):
    resolve = jobs.resolve_request

    def parallel(*args, **kwargs):
        request, matrix = resolve(*args, **kwargs)
        return request.model_copy(update={"composer_concurrency": 3}), matrix

    monkeypatch.setattr(jobs, "resolve_request", parallel)
    app, providers = fixture_app(tmp_path)
    entered, interrupted = Event(), Event()
    started, cancelled = [], []

    async def blocked(prompt):
        started.append(prompt)
        if len(started) == 3:
            entered.set()
        try:
            await asyncio.Future()
        finally:
            cancelled.append(prompt)
            if len(cancelled) == 3:
                interrupted.set()

    providers["composer"].complete = blocked
    with TestClient(app) as client:
        job = _start(client, _workspace(client), "parallel")
        assert entered.wait(5)
        assert client.post(f"/api/exams/{job}/stop").json()["status"] == "cancelled"
        assert interrupted.wait(5)
        assert len(started) == len(cancelled) == 3
        assert all(not providers[role].calls for role in ("illustrator", "solver", "reviewer"))


def test_stop_at_publication_boundary_never_commits_prepared_result(tmp_path):
    app, _ = fixture_app(tmp_path)
    prepared, drained = Event(), Event()
    with TestClient(app) as client:
        manager = app.state.ui_jobs
        save_version = manager._save_version

        async def pause_before_save(job, change, **kwargs):
            prepared.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                try:
                    await save_version(job, change, **kwargs)
                finally:
                    drained.set()

        manager._save_version = pause_before_save
        workspace = _workspace(client)
        job = _start(client, workspace, "stop-before-save")
        assert prepared.wait(5)
        assert client.post(f"/api/exams/{job}/stop").json()["status"] == "cancelled"
        assert drained.wait(5)
        assert manager.store.list_versions(job) == []
        assert manager.store.workspace_job(workspace) is None
        assert not (tmp_path / job / "de_thi.tex").exists()


def test_stop_queued_replacement_keeps_existing_exam_after_restart(tmp_path):
    app, providers = fixture_app(tmp_path)
    with TestClient(app) as client:
        workspace = _workspace(client)
        old = _start(client, workspace, "published")
        assert wait(client, old)["status"] == "completed"
        before = {role: len(provider.calls) for role, provider in providers.items()}
        app.state.ui_jobs.capacity = asyncio.Semaphore(0)
        replacement = _start(client, workspace, "replacement")
        url = f"/api/exams/{replacement}"
        assert client.get(url + "/status").json()["status"] == "queued"
        assert client.post(url + "/stop").json()["status"] == "cancelled"
        assert client.get(url + "/versions").status_code == 409
        assert app.state.ui_jobs.store.list_versions(replacement) == []
        assert {role: len(provider.calls) for role, provider in providers.items()} == before
    restarted, _ = fixture_app(tmp_path)
    with TestClient(restarted) as client:
        (saved,) = client.get("/api/workspaces").json()["workspaces"]
        assert saved["jobId"] == old and saved["jobStatus"] == "completed"
        assert saved["generationId"] == replacement and saved["generationStatus"] == "cancelled"
