"""Exercise contract-driven THPT 2026 formats, live blind solver, XeLaTeX, and API fallback."""

from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion, ProviderError
from exam_baseline.pipeline.rendering.compiler import compile_document, find_compiler
from exam_baseline.thpt2026 import (
    CONTRACT_FORMAT_IDS,
    build_fallback_exam_data,
    profile_by_format_id,
    validate_contract_exam,
)
from tests.api.test_ui_jobs import PAYLOAD as THPT_MATH_PAYLOAD
from tests.api.test_ui_jobs import fixture_app, retrieval
from tests.api.test_ui_vact import VACT_PAYLOAD


def _wait(client: TestClient, job_id: str) -> dict:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        status = client.get(f"/api/exams/{job_id}/status").json()
        if status["status"] in {"completed", "failed"}:
            return status
        time.sleep(0.01)
    raise AssertionError(f"Job {job_id} did not reach a terminal state")


def _contract_payload(format_id: str, prompt: str = "Đề luyện tập chuẩn 2026") -> dict:
    profile = profile_by_format_id(format_id)
    assert profile is not None
    return {
        "formatId": format_id,
        "formatVersion": "1",
        "subject": profile["displayName"],
        "grade": 12,
        "examType": "THPT_STANDARD",
        "durationMinutes": profile["durationMinutes"],
        "itemCount": profile["totalQuestions"],
        "prompt": prompt,
        "uploadedFiles": [],
    }


def test_exam_formats_catalog_and_evaluate_for_all_contract_subjects(tmp_path):
    settings = Settings.for_offline().model_copy(
        update={"demo_mode": True, "latex_cache_dir": tmp_path / "_tex-cache"}
    )
    app = create_app(settings, ui_output_root=tmp_path)
    with TestClient(app) as client:
        catalog = client.get("/api/exam-formats").json()["formats"]
        ids = [item["id"] for item in catalog]
        assert ids[:2] == ["thpt-math", "vact"]
        assert len(catalog) == 8
        for format_id in CONTRACT_FORMAT_IDS:
            assert format_id in ids
            entry = next(item for item in catalog if item["id"] == format_id)
            profile = profile_by_format_id(format_id)
            assert entry["totalQuestions"] == profile["totalQuestions"]
            assert entry["durationMinutes"] == profile["durationMinutes"]
            assert entry["subjects"] == [profile["displayName"]]

            evaluated = client.post(
                "/api/exam-formats/evaluate",
                json=_contract_payload(format_id),
            )
            assert evaluated.status_code == 200
            assert evaluated.json()["formatId"] == format_id

        bad_duration = _contract_payload("thpt_chemistry_2026")
        bad_duration["durationMinutes"] = 90
        assert client.post("/api/exam-formats/evaluate", json=bad_duration).status_code == 422

        bad_count = _contract_payload("thpt_literature_2026")
        bad_count["itemCount"] = 10
        assert client.post("/api/exam-formats/evaluate", json=bad_count).status_code == 422

        bad_subject = _contract_payload("thpt_english_2026")
        bad_subject["subject"] = "Hóa học"
        assert client.post("/api/exam-formats/evaluate", json=bad_subject).status_code == 422


@pytest.mark.parametrize("format_id", CONTRACT_FORMAT_IDS)
def test_thpt2026_demo_generation_edit_approve_and_export(tmp_path, format_id):
    settings = Settings.for_offline().model_copy(
        update={"demo_mode": True, "latex_cache_dir": tmp_path / "_tex-cache"}
    )
    app = create_app(settings, ui_output_root=tmp_path)
    profile = profile_by_format_id(format_id)
    assert profile is not None

    with TestClient(app) as client:
        started = client.post(
            "/api/exams/generate",
            json=_contract_payload(format_id),
            headers={"Idempotency-Key": f"gen-{format_id}"},
        )
        assert started.status_code == 202
        job_id = started.json()["jobId"]
        assert _wait(client, job_id)["status"] == "completed"

        package = client.get(f"/api/exams/{job_id}").json()
        assert len(package["questions"]) == profile["totalQuestions"]
        assert package["subject"] == profile["displayName"]
        assert package["durationMinutes"] == profile["durationMinutes"]

        student_paper = package.get("studentPaper")
        assert student_paper is not None
        assert student_paper["schemaVersion"] == "astra-thpt-paper-v1"
        assert student_paper["formatId"] == format_id
        dumped_paper = json.dumps(student_paper, ensure_ascii=False)
        assert '"rubric"' not in dumped_paper

        raw_job = app.state.ui_jobs.get(job_id)
        assert (
            validate_contract_exam(profile, raw_job["rawQuestions"], raw_job.get("rawPassages"))
            == []
        )

        tex_source = (tmp_path / job_id / "de_thi.tex").read_text(encoding="utf-8")
        assert "ĐỀ LUYỆN TẬP TỐT NGHIỆP THPT 2026" in tex_source
        assert "Hướng dẫn chấm (" not in tex_source

        edit_payload = {
            "revision": package["revision"],
            "question": {"stem": "Câu 1 đã chỉnh sửa."},
        }
        edited = client.put(f"/api/exams/{job_id}/questions/1", json=edit_payload)
        assert edited.status_code == 200
        edited_pkg = edited.json()
        assert edited_pkg["revision"] == 2
        assert edited_pkg["questions"][0]["stem"] == "Câu 1 đã chỉnh sửa."

        approved = client.post(
            f"/api/exams/{job_id}/approve",
            json={
                "revision": edited_pkg["revision"],
                "contentHash": edited_pkg["contentHash"],
                "reviewer": "fixture-teacher",
            },
        )
        assert approved.status_code == 200
        assert approved.json()["approved"] is True

        exported_tex = client.get(f"/api/exams/{job_id}/export?type=STUDENT_EXAM&format=tex")
        assert exported_tex.status_code == 200
        assert "Câu 1 đã chỉnh sửa." in exported_tex.text

        exported_key = client.get(f"/api/exams/{job_id}/export?type=TEACHER_KEY&format=json")
        assert exported_key.status_code == 200
        assert len(exported_key.json()["questions"]) == profile["totalQuestions"]


@pytest.mark.parametrize("format_id", ["thpt_literature_2026", "thpt_chemistry_2026"])
def test_thpt2026_xelatex_compiles_valid_pdf(tmp_path, format_id):
    compiler = find_compiler()
    if compiler is None:
        pytest.skip("No local LaTeX compiler available")

    settings = Settings.for_offline().model_copy(
        update={
            "demo_mode": True,
            "latex_cache_dir": tmp_path / "_tex-cache",
        }
    )
    app = create_app(settings, ui_output_root=tmp_path)
    with TestClient(app) as client:
        job_id = client.post(
            "/api/exams/generate",
            json=_contract_payload(format_id),
            headers={"Idempotency-Key": f"compile-{format_id}"},
        ).json()["jobId"]
        assert _wait(client, job_id)["status"] == "completed"

    compile_document(
        tmp_path / job_id / "de_thi.tex",
        compiler=compiler,
        timeout=120,
        cache_directory=tmp_path / "_tex-cache",
    )
    pdf_path = tmp_path / job_id / "de_thi.pdf"
    assert pdf_path.is_file()
    assert len(PdfReader(pdf_path).pages) >= 1


class _FailingProvider:
    def __init__(self, code: str, message: str):
        self.name = "failing"
        self.model = "failing-model"
        self.parameters = {}
        self.code = code
        self.message = message
        self.calls = []

    async def complete(self, request):
        self.calls.append(request)
        raise ProviderError(self.code, self.message)


@pytest.mark.parametrize(
    ("format_key", "payload", "expected_count"),
    [
        ("thpt-math", THPT_MATH_PAYLOAD, 22),
        ("vact", VACT_PAYLOAD, 120),
        ("thpt_chemistry_2026", _contract_payload("thpt_chemistry_2026"), 28),
    ],
)
def test_fallback_exam_created_when_model_api_fails(tmp_path, format_key, payload, expected_count):
    failing = _FailingProvider("provider_rate_limited", "Upstream 429")
    providers = dict.fromkeys(("composer", "illustrator", "solver", "reviewer"), failing)
    app = create_app(
        Settings.for_offline().model_copy(
            update={"latex_cache_dir": tmp_path / "_tex-cache", "fallback_on_provider_error": True}
        ),
        pipeline_providers=providers,
        ui_output_root=tmp_path,
        rag_retriever=retrieval,
    )
    with TestClient(app) as client:
        job_id = client.post(
            "/api/exams/generate",
            json=payload,
            headers={"Idempotency-Key": f"fb-{format_key}"},
        ).json()["jobId"]
        terminal = _wait(client, job_id)
        assert terminal["status"] == "completed"

        package = client.get(f"/api/exams/{job_id}").json()
        assert len(package["questions"]) == expected_count
        assert package["fallback"]["used"] is True
        assert package["fallback"]["reasonCode"] == "provider_rate_limited"
        assert any(w["code"] == "fallback_used" for w in package["warnings"])
        assert (tmp_path / job_id / "de_thi.tex").is_file()


def test_fallback_can_be_disabled_and_spend_limit_is_never_bypassed(tmp_path):
    failing_rate = _FailingProvider("provider_rate_limited", "Rate limit")
    strict_app = create_app(
        Settings.for_offline().model_copy(
            update={
                "latex_cache_dir": tmp_path / "strict" / "_tex-cache",
                "fallback_on_provider_error": False,
            }
        ),
        pipeline_providers=dict.fromkeys(
            ("composer", "illustrator", "solver", "reviewer"), failing_rate
        ),
        ui_output_root=tmp_path / "strict",
        rag_retriever=retrieval,
    )
    with TestClient(strict_app) as client:
        job_id = client.post(
            "/api/exams/generate",
            json=_contract_payload("thpt_chemistry_2026"),
            headers={"Idempotency-Key": "strict-fail"},
        ).json()["jobId"]
        terminal = _wait(client, job_id)
        assert terminal["status"] == "failed"
        assert terminal["error"]["code"] == "provider_rate_limited"

    budget_app, providers = fixture_app(tmp_path / "budget")

    async def exhausted(_):
        raise ProviderError("spend_limit_exceeded", "ASTRA đã đạt trần 5 USD.")

    providers["composer"].complete = exhausted
    with TestClient(budget_app) as client:
        job_id = client.post(
            "/api/exams/generate",
            json=THPT_MATH_PAYLOAD,
            headers={"Idempotency-Key": "budget-guard"},
        ).json()["jobId"]
        terminal = _wait(client, job_id)
        assert terminal["status"] == "failed"
        assert terminal["error"]["code"] == "spend_limit_exceeded"


def test_thpt2026_live_blind_solver_never_receives_writer_keys(tmp_path):
    profile = profile_by_format_id("thpt_history_2026")
    assert profile is not None
    questions, passages, front_matter = build_fallback_exam_data(profile)

    secret_sentinel = "SECRET_WRITER_SOLUTION_SENTINEL"
    for item in questions:
        item["solution"] = f"{item['solution']} ({secret_sentinel})"

    class _FakeComposer:
        def __init__(self):
            self.calls = []

        async def complete(self, request):
            self.calls.append(request)
            payload = json.loads(request.user)
            sec_id = payload["section"]["id"]
            sec_questions = [q for q in questions if q["id"].startswith(sec_id + "-")]
            response = {
                "questions": sec_questions,
                "passages": passages,
                "front_matter": front_matter,
            }
            return Completion(text=json.dumps(response, ensure_ascii=False), model="fake-composer")

    class _FakeSolver:
        def __init__(self):
            self.calls = []

        async def complete(self, request):
            self.calls.append(request)
            entries = []
            for item in json.loads(request.user)["questions"]:
                q = next(orig for orig in questions if orig["id"] == item["id"])
                if q["type"] == "true_false":
                    ans = ", ".join(
                        f"{letter}) {'Đúng' if stmt['answer'] else 'Sai'}"
                        for letter, stmt in zip("abcd", q["statements"], strict=True)
                    )
                else:
                    ans = q["answer"]
                entries.append({"question_id": q["id"], "status": "solved", "answer": ans})
            return Completion(
                text=json.dumps({"entries": entries}, ensure_ascii=False), model="fake-solver"
            )

    composer = _FakeComposer()
    solver = _FakeSolver()
    providers = {
        "composer": composer,
        "illustrator": composer,
        "solver": solver,
        "reviewer": composer,
    }
    app = create_app(
        Settings.for_offline().model_copy(update={"latex_cache_dir": tmp_path / "_tex-cache"}),
        pipeline_providers=providers,
        ui_output_root=tmp_path,
    )
    with TestClient(app) as client:
        job_id = client.post(
            "/api/exams/generate",
            json=_contract_payload("thpt_history_2026"),
            headers={"Idempotency-Key": "live-history"},
        ).json()["jobId"]
        terminal = _wait(client, job_id)
        assert terminal["status"] == "completed"

        assert len(solver.calls) == 1
        assert secret_sentinel not in solver.calls[0].user
        assert secret_sentinel not in solver.calls[0].system

        package = client.get(f"/api/exams/{job_id}").json()
        assert len(package["questions"]) == 28
        assert all(q["answerCheck"] == "matched" for q in package["questions"])
