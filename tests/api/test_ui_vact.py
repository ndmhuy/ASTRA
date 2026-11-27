"""Exercise V-ACT UI catalog, evaluate, generation package, edit, approve, and export."""

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion
from exam_baseline.vact import template

VACT_PAYLOAD = {
    "formatId": "vact",
    "formatVersion": "1",
    "subject": "Tổng hợp",
    "grade": 12,
    "examType": "DGNL_DHQG",
    "durationMinutes": 150,
    "itemCount": 120,
    "prompt": "Đề luyện tập V-ACT chuẩn",
    "uploadedFiles": [],
}


def _wait(client, job_id):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        status = client.get(f"/api/exams/{job_id}/status").json()
        if status["status"] in {"completed", "failed"}:
            return status
        time.sleep(0.01)
    raise AssertionError("V-ACT job did not reach a terminal state")


async def _offline_vact_runner(request, output: Path, progress):
    progress("composer", "TV_1_10", 1)
    progress("illustrator", "drawings_0", 1)
    progress("solver", "TV_1_10", 1)
    progress("reviewer", None, 1)

    passages = []
    questions = []
    solver_entries = []
    for batch in template.batches():
        for group in batch.groups:
            if group.shared:
                passage = {
                    "id": group.id,
                    "heading": f"Ngữ cảnh {group.id}",
                    "text": "Dữ kiện mẫu phục vụ kiểm thử cấu trúc V-ACT với giá trị $1, 2, 3$.",
                    "table": None,
                }
                if group.id == "g97_99":
                    passage["table"] = {
                        "columns": ["Năm", "Thị phần"],
                        "rows": [["2015", "$20\\%$"], ["2025", "$35\\%$"]],
                    }
                passages.append(passage)
            for num in range(group.start, group.end + 1):
                qid = f"q{num}"
                questions.append(
                    {
                        "id": qid,
                        "stem": f"Câu hỏi kiểm thử số {num}: giá trị $1+1$ là?",
                        "choices": {"A": "$2$", "B": "$3$", "C": "$4$", "D": "$5$"},
                        "answer": "A",
                        "solution": "Lời giải mẫu nội bộ.",
                        "passage_id": group.id if group.shared else None,
                        "illustration_request": (
                            "Vẽ đoạn thẳng từ (0,0) đến (1,1)." if num == 1 else None
                        ),
                    }
                )
                solver_entries.append(
                    {
                        "question_id": qid,
                        "answer": "A",
                        "reasoning": "Giải độc lập mẫu.",
                        "status": "solved",
                    }
                )

    output.mkdir(parents=True, exist_ok=True)
    rev_dir = output / "_internal" / "revision_1"
    rev_dir.mkdir(parents=True, exist_ok=True)
    (rev_dir / "illustrations.json").write_text(
        json.dumps(
            {
                "drawings": [
                    {
                        "question_id": "q1",
                        "latex": r"\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (output / "dap_an_va_loi_giai.json").write_text(
        json.dumps(
            {
                "status": "pending_human_review",
                "revision": 1,
                "composer": questions,
                "passages": passages,
                "independent_solver": {"entries": solver_entries},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {"execution_status": "completed", "revision": 1}


def test_vact_catalog_evaluate_generate_package_edit_approve_and_export(tmp_path):
    settings = Settings.for_offline().model_copy(
        update={"latex_cache_dir": Path(tmp_path) / "_tex-cache"}
    )
    calls = {"composer": [], "solver": []}

    class Composer:
        async def complete(self, prompt):
            data = json.loads(prompt.user)
            calls["composer"].append(data)
            assert data["question"]["id"] == data["slot"]["id"] == "q97"
            assert data["group_kind"] == "data_set"
            assert data["passage"]["table"]["columns"] == ["Năm", "Thị phần"]
            question = {
                **data["question"],
                "answer": "B",
                "stem": "Thị phần tăng bao nhiêu điểm phần trăm?",
                "choices": {"A": "$10$", "B": "$15$", "C": "$20$", "D": "$35$"},
                "solution": "Thị phần tăng $35-20=15$ điểm phần trăm.",
            }
            if data["teacher_instruction"] == "Đổi đoạn đọc":
                question["passage_id"] = "g100_102"
            return Completion(text=json.dumps(question), model="offline-vact-composer")

    class Solver:
        name = model = "offline-vact-solver"
        parameters = {}

        async def complete(self, prompt):
            data = json.loads(prompt.user)
            calls["solver"].append(data)
            assert data["question_ids"] == ["q97"]
            assert len(data["questions"]) == 1
            assert data["questions"][0]["passage_id"] == "g97_99"
            assert {"answer", "solution"}.isdisjoint(data["questions"][0])
            assert [passage["id"] for passage in data["passages"]] == ["g97_99"]
            assert data["passages"][0]["table"]["columns"] == ["Năm", "Thị phần"]
            result = dict(
                entries=[
                    dict(question_id="q97", answer="B", reasoning="Giải độc lập.", status="solved"),
                ]
            )
            return Completion(text=json.dumps(result), model=self.model)

    app = create_app(
        settings,
        ui_output_root=tmp_path,
        ui_runner=_offline_vact_runner,
        pipeline_providers={"composer": Composer(), "solver": Solver()},
    )
    with TestClient(app) as client:
        catalog = client.get("/api/exam-formats").json()["formats"]
        assert [item["id"] for item in catalog[:2]] == ["thpt-math", "vact"]
        vact = catalog[1]
        assert vact["examType"] == "DGNL_DHQG"
        assert vact["durationMinutes"] == 150
        assert vact["totalQuestions"] == 120
        assert [s["count"] for s in vact["sections"]] == [30, 30, 30, 12, 18]

        evaluated = client.post("/api/exam-formats/evaluate", json=VACT_PAYLOAD)
        assert evaluated.status_code == 200
        eval_body = evaluated.json()
        assert eval_body["formatId"] == "vact"
        assert len(eval_body["request"]["slots"]) == 120
        assert eval_body["retrievalMatrix"] is None

        started = client.post(
            "/api/exams/generate", json=VACT_PAYLOAD, headers={"Idempotency-Key": "vact-1"}
        )
        assert started.status_code == 202
        job_id = started.json()["jobId"]
        terminal = _wait(client, job_id)
        assert terminal["status"] == "completed"
        assert terminal["completedItems"] == 120
        assert terminal["totalItems"] == 120

        pkg = client.get(f"/api/exams/{job_id}").json()
        assert pkg["totalScore"] is None
        assert pkg["durationMinutes"] == 150
        assert len(pkg["questions"]) == 120
        assert len(pkg["passages"]) == 21
        assert pkg["preview"]["status"] in {"not_requested", "unavailable"}
        assert pkg["hasDrawings"] is True
        assert pkg["questions"][0]["part"] == "TV"
        assert pkg["questions"][0]["drawingLatex"].startswith(r"\begin{tikzpicture}")
        assert pkg["questions"][30]["part"] == "TA"
        assert "Questions 31-35" in pkg["questions"][30]["groupInstruction"]
        assert pkg["questions"][96]["passageId"] == "g97_99"
        table_passage = next(p for p in pkg["passages"] if p["id"] == "g97_99")
        assert table_passage["table"]["columns"] == ["Năm", "Thị phần"]

        edited = client.put(
            f"/api/exams/{job_id}/questions/1",
            json={"revision": pkg["revision"], "question": {"stem": "Câu 1 đã chỉnh sửa: $2+2=$?"}},
        )
        assert edited.status_code == 200
        edited_pkg = edited.json()
        assert edited_pkg["revision"] == 2
        assert edited_pkg["questions"][0]["stem"] == "Câu 1 đã chỉnh sửa: $2+2=$?"
        assert edited_pkg["questions"][0]["answerCheck"] == "needs_recheck"
        assert edited_pkg["questions"][0]["solverKey"] is None
        checked = client.post(
            f"/api/exams/{job_id}/questions/97/verify", json={"revision": edited_pkg["revision"]}
        )
        assert checked.status_code == 200, checked.text
        assert checked.json()["questions"][96]["answerCheck"] == "mismatched"

        regenerate_url = f"/api/exams/{job_id}/questions/97/regenerate"
        request_data = {"revision": edited_pkg["revision"], "stableId": "q97"}
        wrong_target = client.post(regenerate_url, json={**request_data, "stableId": "q98"})
        assert wrong_target.json()["error"]["code"] == "invalid_question_id"
        assert not calls["composer"]
        invalid = client.post(regenerate_url, json={**request_data, "instruction": "Đổi đoạn đọc"})
        assert invalid.status_code == 422, invalid.text
        assert len(calls["composer"]) == 2 and len(calls["solver"]) == 1
        regen = client.post(
            regenerate_url,
            json={**request_data, "instruction": "Nêu rõ đơn vị cần tính."},
        )
        assert regen.status_code == 200, regen.text
        regenerated = regen.json()
        assert regenerated["revision"] == edited_pkg["revision"] + 1
        assert regenerated["passages"] == edited_pkg["passages"]
        assert regenerated["questions"][96]["passageId"] == "g97_99"
        assert regenerated["questions"][96]["answerCheck"] == "matched"
        assert regenerated["questions"][97]["stem"] == edited_pkg["questions"][97]["stem"]
        assert regenerated["questions"][0]["drawingLatex"] == pkg["questions"][0]["drawingLatex"]
        assert len(calls["composer"]) == 3 and len(calls["solver"]) == 2

        approved = client.post(
            f"/api/exams/{job_id}/approve",
            json={
                "revision": regenerated["revision"],
                "contentHash": regenerated["contentHash"],
                "reviewer": "fixture-teacher",
            },
        )
        assert approved.status_code == 200
        assert approved.json()["approved"] is True

        tex_export = client.get(f"/api/exams/{job_id}/export?type=STUDENT_EXAM&format=tex")
        assert tex_export.status_code == 200
        assert "KỲ THI ĐÁNH GIÁ NĂNG LỰC" in tex_export.text
        assert "Câu 1 đã chỉnh sửa" in tex_export.text

        key_export = client.get(f"/api/exams/{job_id}/export?type=TEACHER_KEY&format=json")
        assert key_export.status_code == 200
        exported_json = key_export.json()
        assert len(exported_json["questions"]) == 120
        assert len(exported_json["passages"]) == 21


def test_demo_mode_runs_thpt_and_vact_without_providers_or_english_jargon(tmp_path):
    settings = Settings.for_offline().model_copy(
        update={
            "demo_mode": True,
            "latex_cache_dir": Path(tmp_path) / "_tex-cache",
        }
    )
    app = create_app(settings, ui_output_root=tmp_path)
    seen_statuses = []
    with TestClient(app) as client:
        orig_progress = app.state.ui_jobs.progress

        def capture_progress(job_id, role, part=None, revision=1):
            orig_progress(job_id, role, part, revision)
            seen_statuses.append(app.state.ui_jobs.status(job_id)["statusMessage"])

        app.state.ui_jobs.progress = capture_progress

        health = client.get("/api/health").json()
        assert health["demoMode"] is True

        thpt_payload = {
            "formatId": "thpt-math",
            "formatVersion": "1",
            "subject": "Toán Học",
            "grade": 12,
            "examType": "THPT_STANDARD",
            "durationMinutes": 90,
            "itemCount": 22,
            "prompt": "Đề chạy thử",
            "uploadedFiles": [],
        }
        thpt_job = client.post(
            "/api/exams/generate", json=thpt_payload, headers={"Idempotency-Key": "demo-thpt"}
        ).json()["jobId"]
        assert _wait(client, thpt_job)["status"] == "completed"
        thpt_pkg = client.get(f"/api/exams/{thpt_job}").json()
        assert len(thpt_pkg["questions"]) == 22
        assert "Human review" not in thpt_pkg["questions"][0]["auditNotes"]
        assert "[Bản mẫu" not in thpt_pkg["questions"][0]["stem"]
        assert "[Demo" not in thpt_pkg["questions"][0]["stem"]

        regen = client.post(
            f"/api/exams/{thpt_job}/questions/1/regenerate",
            json={"revision": thpt_pkg["revision"], "instruction": "Làm mới câu 1"},
        )
        assert regen.status_code == 200
        assert regen.json()["revision"] == 2

        vact_job = client.post(
            "/api/exams/generate", json=VACT_PAYLOAD, headers={"Idempotency-Key": "demo-vact"}
        ).json()["jobId"]
        assert _wait(client, vact_job)["status"] == "completed"
        vact_pkg = client.get(f"/api/exams/{vact_job}").json()
        assert len(vact_pkg["questions"]) == 120
        assert len(vact_pkg["passages"]) == 21
        assert "Human review" not in vact_pkg["questions"][0]["auditNotes"]
        assert "[Bản mẫu" not in vact_pkg["questions"][0]["stem"]
        assert "[Demo" not in vact_pkg["passages"][0]["text"]
        assert (tmp_path / vact_job / "de_thi.tex").is_file()

    assert seen_statuses
    forbidden = ("composer", "solver", "reviewer", "revision", "LOGIC_")
    for msg in seen_statuses:
        assert not any(bad in msg for bad in forbidden)


def test_unconfigured_provider_error_uses_friendly_vietnamese(tmp_path):
    settings = Settings.for_offline().model_copy(
        update={
            "demo_mode": False,
            "latex_cache_dir": Path(tmp_path) / "_tex-cache",
        }
    )
    app = create_app(settings, ui_output_root=tmp_path)
    with TestClient(app) as client:
        assert client.get("/api/health").json()["demoMode"] is False
        vact_job = client.post(
            "/api/exams/generate", json=VACT_PAYLOAD, headers={"Idempotency-Key": "no-prov"}
        ).json()["jobId"]
        terminal = _wait(client, vact_job)
        assert terminal["status"] == "failed"
        assert terminal["error"]["code"] == "provider_not_configured"
        assert "EXAM_PROVIDER" not in terminal["error"]["message"]
        assert "Demo" in terminal["error"]["message"]
