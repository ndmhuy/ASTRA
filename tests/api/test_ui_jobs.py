"""Exercise the real THPT agents with explicit replay providers, never paid models."""

import json
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion, ProviderError
from exam_baseline.thpt.rag import DEFAULT_CORPUS_REF
from rag_workflow import retrieve_exam_context
from tests.paths import ROOT
from tests.thpt.test_generation import Scripted

PAYLOAD = {
    "formatId": "thpt-math",
    "formatVersion": "1",
    "subject": "Toán Học",
    "grade": 12,
    "examType": "THPT_STANDARD",
    "durationMinutes": 90,
    "itemCount": 22,
    "prompt": "Đề luyện tập",
    "uploadedFiles": [],
}


def retrieval(matrix):
    def evidence(question):
        return f"PRIVATE_BANK_KEY question_id={question['question_id']} |"

    return {
        "status": "success",
        "gaps": [],
        "release_info": {"corpus_snapshot": "test-fixture"},
        "question_contexts": [
            {
                "question_id": q["question_id"],
                "status": "ready_with_warnings",
                "requested": {
                    **q,
                    "statement_levels": q.get("statement_levels"),
                },
                "curriculum_knowledge": [
                    {"unit_id": uid} for uid in q.get("curriculum_unit_ids", [])
                ],
                "reference_material_text": evidence(q),
                "warnings": [
                    {"code": "teacher_review_pending", "message": "Synthetic test evidence"}
                ],
            }
            for q in matrix["questions"]
        ],
        "mas_intake_rag": [
            {
                "id": f"rag-{q['question_id']}",
                "question_id": q["question_id"],
                "subject": "Toán",
                "locator": "synthetic-fixture",
                "role": "content_support",
                "source_version": "test-fixture",
                "topic_ids": ["test-fixture-topic"],
                "text": evidence(q),
            }
            for q in matrix["questions"]
        ],
    }


def fixture_app(root, **kwargs):
    providers = {
        role: Scripted(role, False) for role in ("composer", "illustrator", "solver", "reviewer")
    }
    app = create_app(
        Settings.for_offline().model_copy(update={"latex_cache_dir": Path(root) / "_tex-cache"}),
        pipeline_providers=providers,
        ui_output_root=root,
        rag_retriever=kwargs.get("retriever", retrieval),
    )
    return app, providers


def wait(client, job):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        status = client.get(f"/api/exams/{job}/status").json()
        if status["status"] in {"completed", "failed"}:
            return status
        time.sleep(0.01)
    raise AssertionError("Job did not reach a terminal state")


def test_workspaces_share_drafts_link_existing_jobs_and_reject_stale_saves(tmp_path):
    app, _ = fixture_app(tmp_path)
    workspace_url = f"/api/workspaces/{uuid4()}"
    workspace_id = workspace_url.rsplit("/", 1)[-1]
    draft = {
        "schema_version": 1,
        "revision": 0,
        "mode": "custom",
        "title": "Đề nháp",
        "draft": "  Nội dung nháp\n",
        "messages": [
            {"id": "one", "role": "user", "content": "Toán", "timestamp": "2026-11-27T09:00:00Z"}
        ],
    }
    with TestClient(app) as client:
        assert client.put(workspace_url, json=draft).json() == {"revision": 1}
        assert client.put(workspace_url, json=draft).json() == {"revision": 1}
        saved = client.get("/api/workspaces").json()["workspaces"][0]
        assert saved["draft"] == draft["draft"] and saved["messages"] == draft["messages"]
        assert saved["jobId"] is None

        update = {**draft, "revision": 1, "draft": "Draft from a second browser"}
        assert client.put(workspace_url, json=update).json() == {"revision": 2}
        conflict = client.put(workspace_url, json={**draft, "revision": 1, "draft": "Stale update"})
        assert conflict.status_code == 409

        url = f"/api/exams/generate?workspace_id={workspace_id}"
        headers = {"Idempotency-Key": "workspace-job"}
        started = client.post(url, json=PAYLOAD, headers=headers)
        assert started.status_code == 202
        job = started.json()["jobId"]
        assert client.post(url, json=PAYLOAD, headers=headers).json()["jobId"] == job
        assert wait(client, job)["status"] == "completed"

    restarted, _ = fixture_app(tmp_path)
    with TestClient(restarted) as client:
        (saved,) = client.get("/api/workspaces").json()["workspaces"]
        assert saved["id"] == workspace_id and saved["jobId"] == job
        assert saved["jobStatus"] == "completed" and saved["draft"] == update["draft"]
        assert client.get(f"/api/exams/{job}").json()["questions"]
        assert client.delete(workspace_url).status_code == 204
        assert client.get("/api/workspaces").json()["workspaces"] == []
        assert client.put(workspace_url, json=draft).status_code == 404
        assert client.get(f"/api/exams/{job}").status_code == 200


def test_retrieval_agents_teacher_approval_export_edit_and_reconnect(tmp_path):
    app, providers = fixture_app(tmp_path)
    with TestClient(app) as client:
        catalog = client.get("/api/exam-formats").json()["formats"][0]
        assert [s["count"] for s in catalog["sections"]] == [12, 4, 6]
        assert client.post("/api/exam-formats/evaluate", json=PAYLOAD).status_code == 200
        started = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "first"}
        )
        assert started.status_code == 202
        job = started.json()["jobId"]
        repeated = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "first"}
        )
        assert repeated.json()["jobId"] == job
        assert wait(client, job)["status"] == "completed"
        package = client.get(f"/api/exams/{job}").json()
        assert len(package["questions"]) == 22
        assert package["questions"][12]["questionType"] == "true_false"
        assert package["questions"][16]["questionType"] == "short_answer"
        assert package["questions"][0]["answerCheck"] == "matched"
        assert package["questions"][12]["answerCheck"] == "needs_recheck"
        assert package["warnings"] and package["provenance"]["corpus_snapshot"] == "test-fixture"
        assert not package["approved"]
        assert len(providers["reviewer"].calls) == 1
        assert all("PRIVATE_BANK_KEY" not in json.dumps(call) for call in providers["solver"].calls)
        for call in providers["composer"].calls:
            assert call["reference_material"] == [
                f"PRIVATE_BANK_KEY question_id={slot['id']} |" for slot in call["slots"]
            ]
        export_url = f"/api/exams/{job}/export?type=STUDENT_EXAM&format=tex"
        assert client.get(export_url).status_code == 409
        approval = {
            "revision": package["revision"],
            "contentHash": package["contentHash"],
            "reviewer": "fixture-teacher",
        }
        assert client.post(f"/api/exams/{job}/approve", json=approval).status_code == 200
        student = client.get(export_url)
        assert student.status_code == 200 and "Cộng trực tiếp" not in student.text
        assert student.text.count(r"\textbf{Câu ") == 22
        revised = client.put(
            f"/api/exams/{job}/questions/1",
            json={
                "revision": package["revision"],
                "question": {"stem": "Tính $1+1$ (đã sửa).", "key": "B"},
            },
        )
        assert revised.status_code == 200
        new_package = revised.json()
        assert not new_package["approved"]
        first, second = new_package["questions"][:2]
        assert first["stableId"] == "P1-1"
        assert first["answerCheck"] == "needs_recheck"
        assert first["solverKey"] is None
        assert second["answerCheck"] == "matched"
        assert len(providers["solver"].calls) == 1
        assert client.get(export_url).status_code == 409
        assert client.post(f"/api/exams/{job}/approve", json=approval).status_code == 409
        assert (
            client.put(
                f"/api/exams/{job}/questions/1",
                json={"revision": package["revision"], "question": {"stem": "Stale edit"}},
            ).status_code
            == 409
        )
        approved = client.post(
            f"/api/exams/{job}/approve",
            json={
                **approval,
                "revision": new_package["revision"],
                "contentHash": new_package["contentHash"],
            },
        )
        assert approved.status_code == 200
        assert approved.json()["questions"][0]["answerCheck"] == "needs_recheck"

        verify_url = f"/api/exams/{job}/questions/1/verify"
        assert client.post(verify_url, json={"revision": package["revision"]}).status_code == 409
        checked = client.post(verify_url, json={"revision": new_package["revision"]})
        assert checked.status_code == 200, checked.text
        verified_package = checked.json()
        assert verified_package["revision"] == new_package["revision"]
        assert verified_package["approved"]
        assert verified_package["questions"][0]["answerCheck"] == "mismatched"
        assert verified_package["questions"][0]["status"] == "FLAGGED"
        assert verified_package["questions"][0]["solverKey"] == "A"
        assert verified_package["questions"][0]["writerKey"] == "B"
        assert verified_package["questions"][1] == second
        assert len(providers["solver"].calls) == 2 and len(providers["reviewer"].calls) == 1
        solver_input = providers["solver"].calls[-1]["questions"]
        assert len(solver_input) == 1 and solver_input[0]["id"] == "P1-1"
        assert solver_input[0]["stem"] == first["stem"]
    # A new app process recovers the exact job and current revision without regeneration.
    restarted, _ = fixture_app(tmp_path)
    with TestClient(restarted) as client:
        loaded = client.get(f"/api/exams/{job}").json()
        assert loaded["revision"] == package["revision"] + 1
        assert loaded["questions"][0]["answerCheck"] == "mismatched"
        assert '"status": "completed"' in client.get(f"/api/exams/{job}/events").text


def test_legacy_edits_ignore_old_solver_answers(tmp_path):
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "legacy-edits"}
        ).json()["jobId"]
        assert wait(client, job)["status"] == "completed"
        raw = app.state.ui_jobs.get(job)
        raw.pop("solverResultsVersion")
        raw["manualEdits"] = ["P1-1", "P1-2"]
        app.state.ui_jobs.store.save(raw)

        package = client.get(f"/api/exams/{job}").json()
        assert [q["solverKey"] for q in package["questions"][:3]] == [None, None, "A"]
        checked = client.post(
            f"/api/exams/{job}/questions/1/verify", json={"revision": package["revision"]}
        )
        assert checked.status_code == 200, checked.text
        questions = checked.json()["questions"]
        assert [q["answerCheck"] for q in questions[:3]] == ["matched", "needs_recheck", "matched"]
        assert questions[1]["solverKey"] is None


def test_topic_prompt_uses_pinned_slot_evidence_in_web_job(tmp_path, monkeypatch):
    if subprocess.run(
        ["git", "cat-file", "-e", DEFAULT_CORPUS_REF], cwd=ROOT, capture_output=True
    ).returncode:
        pytest.skip("Fetch the pinned corpus to run the web integration test")
    monkeypatch.chdir(ROOT)
    app, providers = fixture_app(
        tmp_path,
        retriever=lambda matrix: retrieve_exam_context(
            matrix, ref=DEFAULT_CORPUS_REF, repo=ROOT
        ).to_dict(),
    )
    scoped = {**PAYLOAD, "prompt": "Tạo đề Toán THPT\nChuyên đề: đạo hàm và tích phân lớp 11-12"}
    with TestClient(app) as client:
        preview = client.post("/api/exam-formats/evaluate", json=scoped)
        assert preview.status_code == 200, preview.text
        spec = preview.json()["retrievalMatrix"]
        assert len(spec["questions"]) == 22
        assert all(slot["curriculum_unit_ids"] for slot in spec["questions"])

        response = client.post(
            "/api/exams/generate", json=scoped, headers={"Idempotency-Key": "scoped"}
        )
        assert response.status_code == 202
        job_id = response.json()["jobId"]
        assert (status := wait(client, job_id))["status"] == "completed", status
        package = client.get(f"/api/exams/{job_id}").json()
        assert len(package["questions"]) == 22
        assert package["provenance"]["corpus_snapshot"] == DEFAULT_CORPUS_REF
        for call in providers["composer"].calls:
            assert call["reference_exam"] == ""
            assert len(call["reference_material"]) == len(call["slots"])
            for slot, evidence in zip(call["slots"], call["reference_material"], strict=True):
                assert f"question_id={slot['id']} |" in evidence
        assert len(providers["reviewer"].calls) == 1

        outside = {**PAYLOAD, "prompt": "Chuyên đề: số phức lớp 12"}
        rejected = client.post(
            "/api/exams/generate", json=outside, headers={"Idempotency-Key": "outside"}
        )
        assert rejected.status_code == 422
        assert rejected.json()["error"]["code"] == "retrieval_gap"


def test_invalid_scope_idempotency_conflict_and_retrieval_gaps(tmp_path):
    app, providers = fixture_app(
        tmp_path,
        retriever=lambda matrix: {
            "status": "gap",
            "gaps": [{"code": "missing_topic", "message": "No source"}],
            "question_contexts": [],
            "mas_intake_rag": [],
        },
    )
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/exams/generate",
                json={**PAYLOAD, "itemCount": 40},
                headers={"Idempotency-Key": "bad"},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/exams/generate",
                json={**PAYLOAD, "uploadedFiles": ["file.pdf"]},
                headers={"Idempotency-Key": "file"},
            ).status_code
            == 422
        )
        job = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "gap"}
        ).json()["jobId"]
        assert wait(client, job)["status"] == "failed"
        assert not any(provider.calls for provider in providers.values())
        conflict = client.post(
            "/api/exams/generate",
            json={**PAYLOAD, "prompt": "different"},
            headers={"Idempotency-Key": "gap"},
        )
        assert conflict.status_code == 409
        assert client.get("/api/exams/not-a-uuid/status").status_code == 422


def test_spending_guard_failure_reaches_the_teacher_without_http_unknown(tmp_path):
    app, providers = fixture_app(tmp_path)

    async def exhausted(_):
        raise ProviderError("spend_limit_exceeded", "ASTRA đã đạt trần 5 USD.")

    providers["composer"].complete = exhausted
    with TestClient(app) as client:
        job = client.post(
            "/api/exams/generate",
            json=PAYLOAD,
            headers={"Idempotency-Key": "budget"},
        ).json()["jobId"]
        result = wait(client, job)
        assert result["status"] == "failed"
        assert result["error"]["code"] == "spend_limit_exceeded"
        assert "5 USD" in result["error"]["message"]
        assert "unknown" not in result["error"]["message"]


def test_tampered_student_artifact_cannot_be_approved(tmp_path):
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "tamper"}
        ).json()["jobId"]
        assert wait(client, job)["status"] == "completed"
        pkg = client.get(f"/api/exams/{job}").json()
        (Path(tmp_path) / job / "de_thi.tex").write_text("changed", encoding="utf-8")
        response = client.post(
            f"/api/exams/{job}/approve",
            json={
                "revision": pkg["revision"],
                "contentHash": pkg["contentHash"],
                "reviewer": "teacher",
            },
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "artifact_changed"


def test_targeted_regeneration_keeps_ids_invalidates_approval_and_has_no_second_reviewer(tmp_path):
    app, providers = fixture_app(tmp_path)
    composer = providers["composer"]
    original_complete = composer.complete

    async def complete(prompt):
        data = json.loads(prompt.user)
        if "question" not in data:
            return await original_complete(prompt)
        composer.calls.append(data)
        question = {**data["question"], "stem": "Tính $2+2$ (tạo lại)."}
        return Completion(text=json.dumps(question, ensure_ascii=False), model=composer.model)

    composer.complete = complete
    with TestClient(app) as client:
        job = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "repair"}
        ).json()["jobId"]
        assert wait(client, job)["status"] == "completed"
        package = client.get(f"/api/exams/{job}").json()
        # Old stored jobs may contain a missing figure, rejected by the new validator.
        # Regeneration must replace the bad target before validating the other questions.
        raw = app.state.ui_jobs.get(job)
        raw["rawQuestions"][0]["stem"] = "Dựa vào bảng biến thiên như sau."
        raw["solutions"]["entries"] = [
            entry for entry in raw["solutions"]["entries"] if entry["question_id"] != "P1-2"
        ]
        previous = {s["question_id"]: s for s in raw["solutions"]["entries"]}
        app.state.ui_jobs.store.save(raw)
        result = client.post(
            f"/api/exams/{job}/questions/1/regenerate",
            json={"revision": package["revision"], "instruction": "Tạo lại câu này"},
        )
        assert result.status_code == 200, result.text
        revised = result.json()
        assert revised["questions"][0]["stableId"] == "P1-1"
        assert revised["questions"][0]["stem"] != package["questions"][0]["stem"]
        assert revised["questions"][1]["answerCheck"] == "needs_recheck"
        saved = app.state.ui_jobs.get(job)["solutions"]["entries"]
        assert {s["question_id"]: s for s in saved if s["question_id"] != "P1-1"} == {
            key: value for key, value in previous.items() if key != "P1-1"
        }
        last_solve = providers["solver"].calls[-1]
        assert [q["id"] for q in last_solve["questions"]] == ["P1-1"]
        assert last_solve["questions"][0]["stem"] == revised["questions"][0]["stem"]
        assert revised["revision"] == package["revision"] + 1
        assert not revised["approved"]
        assert len(providers["reviewer"].calls) == 1
        assert len(providers["solver"].calls) == 2
        assert all("PRIVATE_BANK_KEY" not in json.dumps(call) for call in providers["solver"].calls)
