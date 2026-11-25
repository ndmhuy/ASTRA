"""Exercise the real THPT agents with explicit replay providers, never paid models."""

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion, ProviderError
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
    return {
        "status": "success",
        "gaps": [],
        "release_info": {"corpus_snapshot": "test-fixture"},
        "question_contexts": [
            {
                "question_id": q["question_id"],
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
                "text": f"PRIVATE_BANK_KEY {q['question_id']}",
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
        assert package["warnings"] and package["provenance"]["corpus_snapshot"] == "test-fixture"
        assert not package["approved"]
        assert len(providers["reviewer"].calls) == 1
        assert all("PRIVATE_BANK_KEY" not in json.dumps(call) for call in providers["solver"].calls)
        for call in providers["composer"].calls:
            assert len(call["reference_material"]) == 1
            assert call["reference_material"][0].startswith(f"[THPT_PART:{call['part']}]")
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
            json={"revision": package["revision"], "question": {"stem": "Tính $1+1$ (đã sửa)."}},
        )
        assert revised.status_code == 200
        assert not revised.json()["approved"]
        assert revised.json()["questions"][0]["stableId"] == "P1-1"
        assert client.get(export_url).status_code == 409
        assert client.post(f"/api/exams/{job}/approve", json=approval).status_code == 409
        assert (
            client.put(
                f"/api/exams/{job}/questions/1",
                json={"revision": package["revision"], "question": {"stem": "Stale edit"}},
            ).status_code
            == 409
        )
    # A new app process recovers the exact job and current revision without regeneration.
    restarted, _ = fixture_app(tmp_path)
    with TestClient(restarted) as client:
        assert client.get(f"/api/exams/{job}").json()["revision"] == package["revision"] + 1
        assert '"status": "completed"' in client.get(f"/api/exams/{job}/events").text


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
        app.state.ui_jobs.store.save(raw)
        result = client.post(
            f"/api/exams/{job}/questions/1/regenerate",
            json={"revision": package["revision"], "instruction": "Tạo lại câu này"},
        )
        assert result.status_code == 200, result.text
        revised = result.json()
        assert revised["questions"][0]["stableId"] == "P1-1"
        assert revised["questions"][0]["stem"] != package["questions"][0]["stem"]
        assert revised["questions"][1:] != []
        assert revised["revision"] == package["revision"] + 1
        assert not revised["approved"]
        assert len(providers["reviewer"].calls) == 1
        assert len(providers["solver"].calls) == 2
        assert all("PRIVATE_BANK_KEY" not in json.dumps(call) for call in providers["solver"].calls)
