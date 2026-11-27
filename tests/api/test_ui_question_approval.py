"""Verify per-question approval persistence, invalidation, conflict handling, and P2 notes."""

from fastapi.testclient import TestClient

from tests.api.test_ui_jobs import PAYLOAD, fixture_app, wait


def test_question_approval_persists_resets_on_edit_and_rejects_stale_revision(tmp_path):
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "q-approve-1"}
        ).json()["jobId"]
        assert wait(client, job)["status"] == "completed"

        package = client.get(f"/api/exams/{job}").json()
        assert len(package["questions"]) == 22
        assert all(q["questionApproval"] is None for q in package["questions"])

        # Approve matched question 1 without a reason.
        approved_q1 = client.post(
            f"/api/exams/{job}/questions/1/approve",
            json={"revision": package["revision"], "reviewer": "Cô Lan"},
        )
        assert approved_q1.status_code == 200, approved_q1.text
        q1 = approved_q1.json()["questions"][0]
        assert q1["questionApproval"]["reviewer"] == "Cô Lan"
        assert q1["questionApproval"]["approvedAt"]

        # Approve matched question 2 as well so we can verify unaffected items stay approved.
        approved_q2 = client.post(
            f"/api/exams/{job}/questions/2/approve",
            json={"revision": package["revision"], "reviewer": "Cô Lan"},
        )
        assert approved_q2.status_code == 200, approved_q2.text

        # Stale revision returns 409 conflict.
        assert (
            client.post(
                f"/api/exams/{job}/questions/3/approve",
                json={"revision": package["revision"] + 99, "reviewer": "Cô Lan"},
            ).status_code
            == 409
        )

        # Reload via GET persists both question approvals.
        reloaded = client.get(f"/api/exams/{job}").json()
        assert reloaded["questions"][0]["questionApproval"]["reviewer"] == "Cô Lan"
        assert reloaded["questions"][1]["questionApproval"]["reviewer"] == "Cô Lan"

        # Editing question 1 returns question 1 to unapproved, while question 2 stays approved.
        edited = client.put(
            f"/api/exams/{job}/questions/1",
            json={
                "revision": reloaded["revision"],
                "question": {"stem": "Câu hỏi đã chỉnh sửa sau khi duyệt."},
            },
        )
        assert edited.status_code == 200, edited.text
        edited_pkg = edited.json()
        assert edited_pkg["questions"][0]["questionApproval"] is None
        assert edited_pkg["questions"][0]["answerCheck"] == "needs_recheck"
        assert edited_pkg["questions"][1]["questionApproval"]["reviewer"] == "Cô Lan"

        # Approving a needs_recheck question requires an explicit reason.
        missing_reason = client.post(
            f"/api/exams/{job}/questions/1/approve",
            json={"revision": edited_pkg["revision"], "reviewer": "Cô Lan"},
        )
        assert missing_reason.status_code == 422
        assert missing_reason.json()["error"]["code"] == "approval_reason_required"

        # With a reason, it saves both the decision and the original verification snapshot.
        forced = client.post(
            f"/api/exams/{job}/questions/1/approve",
            json={
                "revision": edited_pkg["revision"],
                "reviewer": "Cô Lan",
                "reason": "Đã kiểm tra lại đáp án thủ công sau khi sửa.",
            },
        )
        assert forced.status_code == 200, forced.text
        forced_q1 = forced.json()["questions"][0]["questionApproval"]
        assert forced_q1["reason"] == "Đã kiểm tra lại đáp án thủ công sau khi sửa."
        assert forced_q1["originalCheck"]["answerCheck"] == "needs_recheck"


def test_p2_mismatched_question_surfaces_statement_letters_and_requires_reason(tmp_path):
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "p2-mismatch"}
        ).json()["jobId"]
        assert wait(client, job)["status"] == "completed"

        raw_job = app.state.ui_jobs.get(job)
        p2_index = next(i for i, q in enumerate(raw_job["rawQuestions"]) if q["id"] == "P2-1")
        p2_raw = raw_job["rawQuestions"][p2_index]
        p2_raw["statements"] = [
            {**stmt, "answer": idx in (0, 2)} for idx, stmt in enumerate(p2_raw["statements"])
        ]
        # Solver disagrees on statements b and d (writer: T, F, T, F vs solver: T, T, T, T).
        for entry in raw_job["solutions"]["entries"]:
            if entry["question_id"] == "P2-1":
                entry["answer"] = "a) Đúng, b) Đúng, c) Đúng, d) Đúng"
                entry["status"] = "solved"
        app.state.ui_jobs.store.save(raw_job)

        pkg = client.get(f"/api/exams/{job}").json()
        p2_question = pkg["questions"][p2_index]
        assert p2_question["answerCheck"] == "mismatched"
        assert p2_question["mismatchedStatements"] == ["b", "d"]
        assert "b, d" in p2_question["auditNotes"]

        no_reason = client.post(
            f"/api/exams/{job}/questions/{p2_index + 1}/approve",
            json={"revision": pkg["revision"], "reviewer": "Thầy Minh"},
        )
        assert no_reason.status_code == 422

        with_reason = client.post(
            f"/api/exams/{job}/questions/{p2_index + 1}/approve",
            json={
                "revision": pkg["revision"],
                "reviewer": "Thầy Minh",
                "reason": "Ý b và d đúng theo đề gốc, Solver hiểu nhầm giả thiết.",
            },
        )
        assert with_reason.status_code == 200, with_reason.text
        approval = with_reason.json()["questions"][p2_index]["questionApproval"]
        assert approval["originalCheck"]["answerCheck"] == "mismatched"
        assert approval["originalCheck"]["solverKey"] == "a) Đúng, b) Đúng, c) Đúng, d) Đúng"
