"""Check the six THPT formats through the UI API with an offline provider."""

import json
from collections import Counter
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion
from exam_baseline.thpt.content import choice_latex, content_latex, normalize_subject_content
from exam_baseline.thpt.contract_artifacts import (
    STUDENT,
    TEACHER,
    content_hash,
    profile,
    validators,
)
from tests.api.test_ui_jobs import wait

FORMATS = [
    ("thpt-physics", "Vật Lý", (18, 4, 6)),
    ("thpt-chemistry", "Hóa Học", (18, 4, 6)),
    ("thpt-biology", "Sinh Học", (18, 4, 6)),
    ("thpt-history", "Lịch Sử", (24, 4, 0)),
    ("thpt-geography", "Địa Lý", (18, 4, 6)),
    ("thpt-english", "Tiếng Anh", (40, 0, 0)),
]


def answer(id_):
    return {"P1": "A", "P2": "a: Đúng; b: Đúng; c: Đúng; d: Đúng", "P3": "1"}[id_[:2]]


def test_subject_notation_normalization_preserves_semantics():
    raw = "Biết Fe = 56; $V = 5 \\mathrm{lít}$ và $T_{khuôn} = 3 \text{ nm}$."
    expected = r"Biết $Fe = 56$; $V = 5 \text{lít}$ và $T_{\text{khuôn}} = 3 \text{ nm}$."
    fixed = normalize_subject_content(raw)
    assert fixed == expected
    assert content_latex(fixed)
    assert choice_latex(normalize_subject_content("C_4H_{11}N")) == r"$\mathrm{C_4H_{11}N}$"


class Replay:
    name = model = "offline-test"
    parameters = {}

    def __init__(self, role):
        self.role = role
        self.calls = []

    async def complete(self, prompt):
        data = json.loads(prompt.user)
        self.calls.append(data)
        if self.role == "composer":
            if "question" in data:
                result = {**data["question"], "stem": "Revised question from the same passage."}
            else:
                result = {
                    "questions": [self.question(slot["id"]) for slot in data["slots"]],
                    "passage": None,
                }
                group = data["group"]
                if isinstance(group, dict) and group["kind"] == "cloze":
                    first, last = group["range"]
                    result["passage"] = " ".join(
                        f"Blank ({n}) ____." for n in range(first, last + 1)
                    )
                elif isinstance(group, dict) and group["kind"] == "reading":
                    result["passage"] = "An original passage for the isolated API test."
        elif self.role == "solver":
            assert all("answer" not in q and "solution" not in q for q in data["questions"])
            assert "PRIVATE_REPLAY_KEY" not in prompt.user
            result = {
                "entries": [
                    dict(
                        question_id=q["id"],
                        answer=answer(q["id"]),
                        reasoning="Test evidence",
                        status="solved",
                    )
                    for q in data["questions"]
                ]
            }
        else:
            issues = ["P1-1 · Review the chronology."] if data["subject"] == "Lịch Sử" else []
            result = dict(
                decision="needs_revision" if issues else "approved",
                checked_ids=[q["id"] for q in data["questions"]],
                issues=issues,
            )
        return Completion(text=json.dumps(result), model="offline-test")

    @staticmethod
    def question(id_):
        return dict(
            id=id_,
            stem=(
                f"Test item {id_}. Ghi kết quả chính xác, không làm tròn."
                if id_.startswith("P3")
                else f"Test item {id_}."
            ),
            solution="PRIVATE_REPLAY_KEY",
            answer=None if id_.startswith("P2") else answer(id_),
            choices=dict(zip("ABCD", ["Yes", "No", "Maybe", "Neither"], strict=True))
            if id_.startswith("P1")
            else {},
            statements=[
                dict(text=f"Test statement {n}", solution="PRIVATE_REPLAY_KEY", answer=True)
                for n in range(4)
            ]
            if id_.startswith("P2")
            else [],
        )


@pytest.mark.parametrize(("format_id", "subject", "counts"), FORMATS)
def test_subject_review_preview_and_export(tmp_path, format_id, subject, counts):
    providers = {role: Replay(role) for role in ("composer", "solver", "reviewer")}
    app = create_app(
        Settings.for_offline(),
        ui_output_root=tmp_path,
        pipeline_providers=providers,
    )
    prompt = dict(
        formatId=format_id,
        subject=subject,
        grade=12,
        examType="THPT_STANDARD",
        durationMinutes=50,
        itemCount=sum(counts),
    )
    with TestClient(app) as client:
        formats = client.get("/api/exam-formats").json()["formats"]
        preset = next(fmt for fmt in formats if fmt["id"] == format_id)
        assert [s["count"] for s in preset["sections"]] == [n for n in counts if n]
        assert (
            sum(
                section["count"] * section.get("pointsPerQuestion", 1)
                for section in preset["sections"]
            )
            == preset["totalScore"]
            == 10
        )
        assert (
            client.post("/api/exam-formats/evaluate", json={**prompt, "itemCount": 22}).status_code
            == 422
        )
        assert (
            client.post(
                "/api/exam-formats/evaluate", json={**prompt, "subject": "Toán Học"}
            ).status_code
            == 422
        )
        preview = client.post("/api/exam-formats/evaluate", json=prompt).json()
        assert preview["retrievalMatrix"] is None
        assert len(preview["request"]["slots"]) == sum(counts)
        response = client.post(
            "/api/exams/generate", json=prompt, headers={"Idempotency-Key": format_id}
        )
        job = response.json()["jobId"]
        assert wait(client, job)["status"] == "completed", client.get(
            f"/api/exams/{job}/status"
        ).json()
        package = client.get(f"/api/exams/{job}").json()
        assert package["subject"] == subject
        assert package["durationMinutes"] == 50
        assert all(q["answerCheck"] == "matched" for q in package["questions"])
        assert Counter(q["part"] for q in package["questions"]) == {
            f"P{i}": count for i, count in enumerate(counts, 1) if count
        }
        assert not package["approved"]
        spec = profile(format_id)
        if spec:
            paper = package["studentPaper"]
            key = json.loads((tmp_path / job / TEACHER).read_text(encoding="utf-8"))
            assert paper == json.loads((tmp_path / job / STUDENT).read_text(encoding="utf-8"))
            for validator, artifact in zip(validators(), (paper, key), strict=True):
                validator.validate(artifact)
            assert paper["formatId"] == spec["formatId"]
            assert "PRIVATE_REPLAY_KEY" not in json.dumps(paper)
            assert paper["contentHash"] == content_hash(paper) == package["contentHash"]
            assert all(paper[name] == key[name] for name in ("examId", "revision", "contentHash"))
            assert len(key["entries"]) == sum(counts)
            assert any(e.get("explanation") for e in key["entries"])
        else:
            assert "studentPaper" not in package
            assert not (tmp_path / job / STUDENT).exists()

        if format_id == "thpt-history":
            assert len(providers["reviewer"].calls) == 1
            assert "subject_review_issue" in {w["code"] for w in package["warnings"]}
        if format_id == "thpt-english":
            assert [p["questionRange"] for p in package["passages"]] == [
                [6, 10],
                [11, 20],
                [21, 28],
                [29, 34],
                [35, 40],
            ]
            assert package["questions"][5]["passageId"] == "E2"
            assert "passageId" not in package["questions"][0]
            assert package["studentPaper"]["passages"][0]["questionRange"] == [1, 5]
            revision = package["revision"]
            checked = client.post(
                f"/api/exams/{job}/questions/6/verify", json={"revision": revision}
            )
            assert checked.status_code == 200
            assert providers["solver"].calls[-1]["passage"] == package["passages"][0]["text"]
            changed = client.post(
                f"/api/exams/{job}/questions/6/regenerate", json={"revision": revision}
            )
            assert changed.status_code == 200, changed.text
            package = changed.json()
            assert package["revision"] == revision + 1
            assert providers["solver"].calls[-1]["passage"] == package["passages"][0]["text"]
            assert len(providers["solver"].calls[-1]["questions"]) == 1
        raw_tex = (tmp_path / job / "de_thi.tex").read_text("utf-8")
        assert f"Môn thi: {subject.upper()}" in raw_tex
        assert "50 phút" in raw_tex
        assert "NĂM 2026" in raw_tex
        assert "Thí sinh không được sử dụng tài liệu." in raw_tex
        for index, count in enumerate(counts, 1):
            marker = f"% LECTURING-PART: P{index}"
            assert (marker in raw_tex) == bool(count)
            if count:
                heading = raw_tex.split(marker + "\n", 1)[1].splitlines()[0]
                assert f"đến câu {count}." in heading
                if index == 3:
                    assert "Phiếu trả lời trắc nghiệm" in heading
        assert "Trả lời:" not in raw_tex
        assert "PRIVATE_REPLAY_KEY" not in raw_tex
        export_url = f"/api/exams/{job}/export"
        export_params = {"type": "STUDENT_EXAM", "format": "tex"}
        assert client.get(export_url, params=export_params).status_code == 409
        approval = client.post(
            f"/api/exams/{job}/approve",
            json={
                "revision": package["revision"],
                "contentHash": package["contentHash"],
                "reviewer": "Test teacher",
            },
        )
        assert approval.status_code == 200, approval.text
        assert client.get(export_url, params=export_params).text == raw_tex
        if spec:
            for kind, name in (("STUDENT_EXAM", STUDENT), ("TEACHER_KEY", TEACHER)):
                downloaded = client.get(export_url, params={"type": kind, "format": "json"})
                assert downloaded.status_code == 200
                assert name in downloaded.headers["content-disposition"]
                assert downloaded.json() == json.loads((tmp_path / job / name).read_text("utf-8"))
            old_hash = package["contentHash"]
            edited = client.put(
                f"/api/exams/{job}/questions/1",
                json={"revision": package["revision"], "question": {"stem": "Revised test stem."}},
            )
            assert edited.status_code == 200, edited.text
            updated = edited.json()
            assert updated["revision"] == package["revision"] + 1
            assert updated["contentHash"] != old_hash
            assert updated["studentPaper"]["contentHash"] == updated["contentHash"]
            updated_key = json.loads((tmp_path / job / TEACHER).read_text("utf-8"))
            assert updated_key["contentHash"] == updated["contentHash"]
            assert not updated["approved"]


def test_contract_artifacts_follow_restored_and_forked_versions(tmp_path):
    providers = {role: Replay(role) for role in ("composer", "solver", "reviewer")}
    app = create_app(Settings.for_offline(), ui_output_root=tmp_path, pipeline_providers=providers)
    workspace_id, destination_id = str(uuid4()), str(uuid4())
    workspace_url = f"/api/workspaces/{workspace_id}"
    with TestClient(app) as client:
        assert (
            client.put(
                workspace_url,
                json={
                    "revision": 0,
                    "mode": "custom",
                    "title": "Lịch sử",
                    "draft": "",
                    "messages": [],
                },
            ).status_code
            == 200
        )
        generated = client.post(
            f"/api/exams/generate?workspace_id={workspace_id}",
            json={
                "formatId": "thpt-history",
                "subject": "Lịch Sử",
                "grade": 12,
                "examType": "THPT_STANDARD",
                "durationMinutes": 50,
                "itemCount": 28,
            },
            headers={"Idempotency-Key": "contract-history"},
        )
        job_id = generated.json()["jobId"]
        assert wait(client, job_id)["status"] == "completed"
        url = f"/api/exams/{job_id}"
        initial = client.get(url).json()
        revision = initial["revision"]
        edited = client.put(
            f"{url}/questions/1",
            json={
                "revision": revision,
                "question": {"stem": "Revised stem for history."},
            },
        )
        assert edited.status_code == 200, edited.text
        assert (
            client.get(f"{url}/versions/{revision}").json()["studentPaper"]
            == initial["studentPaper"]
        )
        restored = client.post(
            f"{url}/versions/{revision}/restore",
            json={
                "revision": edited.json()["revision"],
            },
        )
        assert restored.status_code == 200, restored.text
        message = client.get(f"{workspace_url}/changes").json()["messages"][0]
        branched = client.post(
            f"{workspace_url}/branch",
            json={
                "messageId": message["id"],
                "destinationId": destination_id,
            },
        )
        assert branched.status_code == 200, branched.text
        fork = next(
            item
            for item in client.get("/api/workspaces").json()["workspaces"]
            if item["id"] == destination_id
        )
        for package in (restored.json(), client.get(f"/api/exams/{fork['jobId']}").json()):
            paper = package["studentPaper"]
            key = json.loads((tmp_path / package["examId"] / TEACHER).read_text("utf-8"))
            assert paper["examId"] == f"exam-{package['examId']}" == key["examId"]
            assert paper["revision"] == package["revision"] == key["revision"]
            assert paper["contentHash"] == content_hash(paper) == key["contentHash"]
            assert paper["sections"] == initial["studentPaper"]["sections"]
            assert not package["approved"]
