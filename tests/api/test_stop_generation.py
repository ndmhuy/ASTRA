import asyncio
import json
import time
from threading import Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from exam_baseline.core.contracts import Completion
from exam_baseline.ui import jobs
from exam_baseline.ui.errors import UiError
from tests.api.test_ui_jobs import PAYLOAD, fixture_app, wait


def test_stop_question_regeneration_then_retry_discards_late_reply(tmp_path):
    app, providers = fixture_app(tmp_path)
    entered, release = Event(), Event()
    composer = providers["composer"]
    original = composer.complete

    async def compose(prompt):
        data = json.loads(prompt.user)
        if "question" not in data:
            return await original(prompt)
        if data["teacher_instruction"] == "first":
            entered.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                while not release.is_set():
                    await asyncio.sleep(0.01)
        repaired = {**data["question"], "stem": f"Tính $2+2$ ({data['teacher_instruction']})."}
        return Completion(text=json.dumps(repaired, ensure_ascii=False), model=composer.model)

    composer.complete = compose
    with TestClient(app) as client:
        try:
            workspace = _workspace(client)
            job = _start(client, workspace, "initial-question-paper")
            assert wait(client, job)["status"] == "completed"
            exam = f"/api/exams/{job}"
            original_paper = client.get(exam).json()
            binding = {key: original_paper[key] for key in ("revision", "contentHash")}
            assert client.post(
                exam + "/approve", json={**binding, "reviewer": "teacher"}
            ).is_success
            source = (tmp_path / job / "de_thi.tex").read_bytes()

            def start(instruction):
                result = client.post(
                    exam + "/questions/1/regenerate",
                    params={"workspace_id": workspace, "background": True},
                    json={"revision": binding["revision"], "instruction": instruction},
                )
                assert result.status_code == 202
                return result.json()["id"]

            old = start("first")
            assert entered.wait(5)
            manager = app.state.ui_jobs
            task = manager.question_tasks[(job, old)]
            url = f"{exam}/regenerations/{old}"
            assert client.get(url).json()["stage"] == "composer"
            assert client.post(url + "/stop").json()["status"] == "cancelled"
            assert client.post(url + "/stop").json()["status"] == "cancelled"
            paper = client.get(exam).json()
            assert paper["approved"] and paper["revision"] == binding["revision"]
            assert (tmp_path / job / "de_thi.tex").read_bytes() == source

            new = start("second")
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                receipt = client.get(f"{exam}/regenerations/{new}").json()
                if receipt["status"] != "pending":
                    break
                time.sleep(0.01)
            assert receipt["status"] == "completed", receipt
            assert not task.done()
            solved = len(providers["solver"].calls)
            release.set()
            deadline = time.monotonic() + 5
            while not task.done() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert task.done()
            assert client.get(url).json()["status"] == "cancelled"
            assert len(providers["solver"].calls) == solved
            final = client.get(exam).json()
            assert final["revision"] == binding["revision"] + 1 and not final["approved"]
            assert final["questions"][0]["stem"] == "Tính $2+2$ (second)."
            assert final["questions"][1:] == [
                {**question, "examRevision": final["revision"], "revisionCount": 1}
                for question in original_paper["questions"][1:]
            ]
            assert len(manager.store.list_versions(job)) == 2
        finally:
            release.set()


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
            stopped = client.post(old_url + "/stop", json={"executionVersion": 1})
            assert stopped.json()["status"] == "cancelled"
            assert interrupted.wait(5)
            assert (
                client.post(old_url + "/stop", json={"executionVersion": 1}).json()
                == stopped.json()
            )
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
            assert (
                client.post(f"/api/exams/{new}/stop", json={"executionVersion": 1}).json()["status"]
                == "completed"
            )
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
        assert (
            client.post(f"/api/exams/{job}/stop", json={"executionVersion": 1}).json()["status"]
            == "cancelled"
        )
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
        assert (
            client.post(f"/api/exams/{job}/stop", json={"executionVersion": 1}).json()["status"]
            == "cancelled"
        )
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
        assert (
            client.post(url + "/stop", json={"executionVersion": 1}).json()["status"] == "cancelled"
        )
        assert client.get(url + "/versions").status_code == 409
        assert app.state.ui_jobs.store.list_versions(replacement) == []
        assert {role: len(provider.calls) for role, provider in providers.items()} == before
    restarted, _ = fixture_app(tmp_path)
    with TestClient(restarted) as client:
        (saved,) = client.get("/api/workspaces").json()["workspaces"]
        assert saved["jobId"] == old and saved["jobStatus"] == "completed"
        assert saved["generationId"] == replacement and saved["generationStatus"] == "cancelled"


def test_continue_reuses_finished_part_in_same_job_and_rejects_stale_controls(tmp_path):
    app, providers = fixture_app(tmp_path)
    entered = Event()
    parts = []
    composer = providers["composer"]
    complete = composer.complete

    async def block_first_p2(prompt):
        part = json.loads(prompt.user)["part"]
        parts.append(part)
        if part == "P2" and not entered.is_set():
            entered.set()
            await asyncio.Future()
        return await complete(prompt)

    composer.complete = block_first_p2
    with TestClient(app) as client:
        workspace = _workspace(client)
        old = _start(client, workspace, "before-continue")
        assert entered.wait(5)
        url = f"/api/exams/{old}"
        assert (
            client.post(url + "/stop", json={"executionVersion": 1}).json()["status"] == "cancelled"
        )
        continued = client.post(url + "/resume", json={"executionVersion": 1})
        assert continued.status_code == 202
        new = continued.json()["jobId"]
        assert old == new
        assert continued.json()["executionVersion"] == 2
        assert client.post(url + "/resume", json={"executionVersion": 1}).json()["jobId"] == new
        assert wait(client, new)["status"] == "completed"
        assert parts == ["P1", "P2", "P2", "P3"]
        assert client.get(url + "/status").json()["status"] == "completed"
        assert client.post(url + "/pause", json={"executionVersion": 1}).status_code == 409
        assert len(app.state.ui_jobs.store.list_versions(old)) == 1
        assert client.get(f"/api/workspaces/{workspace}/versions").json()["currentJobId"] == new
