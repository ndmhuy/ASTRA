"""Mounted React regressions for exam intake; synthetic responses, zero inference.

Reuse the existing no-inference server. Every business/model route is intercepted;
generation and external network requests are forbidden. No exam is generated.
"""

import copy
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from agent_capability_smoke import serve, stop_fixture_server

ROOT = Path(__file__).resolve().parents[1]


def observe(base):
    from playwright.sync_api import expect, sync_playwright

    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="msedge" if os.name == "nt" else None, headless=True
        )
        cases = [
            ("draft", "soạn đề tiếng anh THPT cho tao", "Tiếng Anh", False, None),
            ("completed", "tạo đề toán thpt mới", "Toán Học", True, None),
            ("completed", "soạn đề tiếng anh THPT cho tao", "Tiếng Anh", True, None),
            ("paused", "tạo đề toán thpt mới", "Toán Học", True, None),
            ("running", "tạo đề toán thpt mới", "Toán Học", True, None),
            ("failed", "tạo đề toán thpt mới", "Toán Học", True, None),
            (
                "draft",
                "Chuẩn bị giúp cô bài kiểm tra tiếng Anh chuẩn tốt nghiệp",
                "Tiếng Anh",
                False,
                "compatible",
            ),
            (
                "draft",
                "Tạo một bài kiểm tra Toán theo mẫu tốt nghiệp fixture",
                None,
                False,
                "conflicting",
            ),
            ("completed", "Đừng tạo đề mới", None, False, "negated"),
            ("completed", "Tạo đề toán THPT mới được không?", None, False, "question"),
            ("draft", "Soạn đề SAT như năm trước fixture", None, False, "unavailable"),
            (
                "draft",
                "Nhờ cấu hình Toán THPT chủ đề Hàm số nâng cao có $x^2$ fixture",
                "Toán Học",
                False,
                "evolving",
            ),
            ("draft", "Danh sách tài liệu fixture", None, False, "documents"),
            ("running", "Tới đâu rồi?", None, False, "toggle-status"),
            (
                "draft",
                "Luyện SAT Math 15 câu, 25 phút, không dùng web fixture",
                None,
                False,
                "no-web-practice",
            ),
            ("draft", "Luyện SAT theo file đính kèm fixture", None, False, "attached-practice"),
            (
                "completed",
                "Luyện SAT Math 15 câu 25 phút không dùng web fixture",
                None,
                True,
                "no-web-practice",
            ),
        ]
        for state, message, subject, fresh, model in cases:
            context = browser.new_context(reduced_motion="reduce")
            page = context.new_page()
            workspace, job = str(uuid4()), str(uuid4())
            progress = dict(
                jobId=job,
                status=state,
                executionVersion=1,
                checkpointVersion=1,
                stage=2,
                stageName="composer",
                percent=40,
                completedItems=16,
                totalItems=22,
                estimatedSecondsLeft=0,
                statusMessage=state,
                resumeAvailable=state == "paused",
            )
            source = dict(
                id=workspace,
                revision=1,
                mode="custom",
                title="Đề cũ phải giữ nguyên",
                createdAt="2026-11-28T00:00:00Z",
                draft="",
                messages=[],
                jobId=None if state == "draft" else job,
                jobStatus=None if state == "draft" else state,
                generationId=None if state == "draft" else job,
                generationStatus=None if state == "draft" else state,
                generationState=None if state == "draft" else progress,
                jobMeta=dict(subject="Tiếng Anh", durationMinutes=50, itemCount=40),
            )
            entries = {workspace: copy.deepcopy(source)}
            if model == "attached-practice":
                entries[workspace]["inputDocuments"] = [
                    {
                        "schema_version": "input-document-v1",
                        "id": str(uuid4()),
                        "filename": "fixture.txt",
                        "kind": "supplementary",
                        "size": 30,
                        "sha256": "a" * 64,
                        "characters": 30,
                        "preview": "Synthetic fixture preview",
                    }
                ]
            counters = dict(interpretations=0, evaluations=0, generation=0)
            errors, forbidden = [], []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))

            def route_request(
                route,
                *,
                forbidden=forbidden,
                counters=counters,
                model=model,
                message=message,
                entries=entries,
                source=source,
                progress=progress,
                job=job,
            ):
                request = route.request
                path = urlsplit(request.url).path
                if urlsplit(request.url).hostname in {"fonts.googleapis.com", "fonts.gstatic.com"}:
                    # Suppress existing external font assets; no external request is sent.
                    route.fulfill(content_type="text/css", body="")
                elif not request.url.startswith(base + "/"):
                    forbidden.append(request.url)
                    route.abort()
                elif path == "/agent/turn":
                    counters["interpretations"] += 1
                    if model is None or model == "toggle-status":
                        forbidden.append("unexpected interpretation: " + message)
                        route.abort()
                        return
                    turn = request.post_data_json
                    if model == "unavailable":
                        route.fulfill(
                            json={
                                "schemaVersion": "astra-intent-v1",
                                "clientMessageId": turn["clientMessageId"],
                                "decision": {
                                    "kind": "temporarily_unavailable",
                                    "intents": [],
                                    "reasonCode": "schema",
                                },
                            }
                        )
                        return
                    params = {"family": "thpt", "subject": "Tiếng Anh"}
                    second = {"subject": "Toán Học"} if model == "conflicting" else params
                    if model == "question":
                        params = second = {"family": "thpt", "subject": "Toán Học"}
                    goals = [
                        {"goal": "PREPARE_EXAM", "parameters": params},
                        {"goal": "REQUEST_GENERATION", "parameters": second},
                    ]
                    if model == "evolving":
                        goals = [
                            {
                                "goal": "PREPARE_EXAM",
                                "parameters": {
                                    "family": "thpt",
                                    "subject": "Toán Học",
                                    "topic": "Hàm số",
                                    "difficulty": "Nâng cao",
                                    "requirements": "Giữ nguyên $x^2$",
                                },
                            }
                        ]
                    if model == "documents":
                        goals = [{"goal": "LIST_DOCUMENTS", "parameters": {}}]
                    if model == "no-web-practice":
                        goals = [
                            {
                                "goal": "PREPARE_PRACTICE",
                                "parameters": {
                                    "topic": "SAT Math",
                                    "count": 15,
                                    "minutes": 25,
                                    "sourcePreference": "no_web",
                                },
                            }
                        ]
                    if model == "attached-practice":
                        goals = [
                            {
                                "goal": "PREPARE_PRACTICE",
                                "parameters": {
                                    "topic": "SAT Math",
                                    "sourcePreference": "attachments",
                                },
                            }
                        ]
                    route.fulfill(
                        json={
                            "schemaVersion": "astra-semantic-v3",
                            "clientMessageId": turn["clientMessageId"],
                            "sourceContract": "astra-semantic-v3",
                            "frame": {
                                "schemaVersion": "astra-semantic-v3",
                                "dialogueAct": "QUESTION"
                                if model in {"question", "documents"}
                                else "REQUEST",
                                "goals": goals,
                                "constraints": ["NO_EXECUTION"]
                                if model == "negated"
                                else ["NO_WEB"]
                                if model == "no-web-practice"
                                else [],
                            },
                        }
                    )
                elif path == "/agent/research":
                    forbidden.append("Unexpected research request")
                    route.abort()
                elif path == "/api/exam-formats/evaluate":
                    counters["evaluations"] += 1
                    payload = request.post_data_json
                    route.fulfill(
                        json={
                            "status": "validated",
                            "formatId": payload["formatId"],
                            "formatVersion": payload["formatVersion"],
                        }
                    )
                elif path.startswith("/api/workspaces"):
                    if request.method == "PUT":
                        identifier = path.rsplit("/", 1)[1]
                        payload = request.post_data_json
                        previous = entries.get(identifier, {})
                        revision = previous.get("revision", 0) + 1
                        entries[identifier] = {
                            **previous,
                            **payload,
                            "id": identifier,
                            "revision": revision,
                            "createdAt": source["createdAt"],
                        }
                        route.fulfill(json={"revision": revision})
                    elif path == "/api/workspaces":
                        route.fulfill(json={"workspaces": list(entries.values())})
                    elif path.endswith("/changes"):
                        route.fulfill(json={"messages": [], "milestones": []})
                    else:
                        forbidden.append(path)
                        route.abort()
                elif path.startswith("/api/exams/"):
                    if path.endswith("/preview"):
                        # Existing completed-exam preview is local rendering, not inference.
                        route.fulfill(
                            json={
                                "status": "failed",
                                "revision": 1,
                                "contentHash": "a" * 64,
                                "compilerAvailable": False,
                            }
                        )
                    elif path.endswith("/evaluate") and request.method == "POST":
                        counters["evaluations"] += 1
                        route.fulfill(json={"status": "validated"})
                    elif request.method != "GET":
                        counters["generation"] += 1
                        forbidden.append(path)
                        route.abort()
                    elif path.endswith("/status"):
                        route.fulfill(json=progress)
                    elif path.endswith("/events"):
                        route.fulfill(
                            content_type="text/event-stream",
                            body="data: " + json.dumps(progress) + "\n\n",
                        )
                    else:
                        route.fulfill(
                            json={
                                "examId": job,
                                "title": source["title"],
                                "subject": "Tiếng Anh",
                                "grade": 12,
                                "revision": 1,
                                "contentHash": "a" * 64,
                                "durationMinutes": 50,
                                "approved": False,
                                "warnings": [],
                                "questions": [],
                                "blueprint": {"examType": "THPT_STANDARD"},
                            }
                        )
                else:
                    route.continue_()

            page.route("**/*", route_request)
            page.goto(base)
            page.locator('.sidebar-exam[title="Đề cũ phải giữ nguyên"]').click()
            composer = page.get_by_role("textbox", name="Yêu cầu soạn đề", exact=True)
            if model == "toggle-status":
                page.get_by_role("button", name="Tuỳ chọn", exact=True).click()
                page.get_by_role("checkbox", name="Tìm kiếm trên mạng", exact=False).check()
            composer.fill(message)
            composer.press("Enter")
            if subject:
                card = page.get_by_role("region", name="Cấu hình đề thi từ yêu cầu")
                expect(card).to_be_visible()
                selected = "thpt-english" if subject == "Tiếng Anh" else "thpt-math"
                expect(card.get_by_role("combobox", name="Chọn mẫu đề")).to_have_value(selected)
                expect(card.get_by_role("button", name="Tạo đề ngay", exact=True)).to_be_enabled()
                expect(page.get_by_role("dialog")).to_have_count(0)
                if model == "evolving":
                    expect(card.get_by_label("Chủ đề trọng tâm")).to_have_value("Hàm số")
                    expect(card.get_by_label("Mức độ / phân bố câu hỏi")).to_have_value("Nâng cao")
                    expect(card.get_by_label("Yêu cầu bổ sung")).to_have_value("Giữ nguyên $x^2$")
                    card.get_by_role("combobox", name="Chọn mẫu đề").select_option("thpt-biology")
                    expect(card.get_by_label("Chủ đề trọng tâm")).to_have_value("")
                    expect(card.get_by_label("Mức độ / phân bố câu hỏi")).to_have_value("Nâng cao")
                    expect(card.get_by_label("Yêu cầu bổ sung")).to_have_value("Giữ nguyên $x^2$")
                    composer.fill("Xác nhận")
                    composer.press("Enter")
                    expect(
                        page.get_by_text(
                            "Hiện chưa có thao tác nào đang chờ xác nhận", exact=False
                        ).last
                    ).to_be_visible()
                    card.get_by_role("button", name="Mở cấu hình", exact=True).click()
                    expect(page.get_by_role("dialog")).to_contain_text("Giữ nguyên $x^2$")
            elif model == "no-web-practice":
                expect(
                    page.get_by_role("region", name="Cấu hình đề thi từ yêu cầu")
                ).to_contain_text("15 câu")
                expect(page.get_by_text("Không tìm mạng", exact=False).last).to_be_visible()
            else:
                expected = (
                    "chưa thống nhất"
                    if model == "conflicting"
                    else "có 22 câu"
                    if model == "question"
                    else "Phản hồi AI chưa khớp định dạng"
                    if model == "unavailable"
                    else "Chưa có tài liệu"
                    if model == "documents"
                    else "chưa hỗ trợ tài liệu đính kèm"
                    if model == "attached-practice"
                    else "Đã lưu 16/22 câu"
                    if model == "toggle-status"
                    else "có điều kiện hoặc mâu thuẫn"
                )
                expect(page.get_by_text(expected, exact=False).last).to_be_visible()
                expect(page.get_by_role("dialog")).to_have_count(0)
                expect(page.get_by_role("region", name="Cấu hình đề thi từ yêu cầu")).to_have_count(
                    0
                )
            assert len(entries) == (2 if fresh else 1), (state, message, entries)
            if fresh:
                # Model-resolved creation transfers the turn after interpretation;
                # wait for the observed, serialized draft saves to finish.
                for _ in range(100):
                    if not entries[workspace]["messages"]:
                        break
                    page.wait_for_timeout(10)
                # Typing/clearing the composer legitimately saves a new draft revision.
                # It must not alter the old exam, checkpoint, title or transcript.
                for key in source.keys() - {"revision", "messages"}:
                    assert entries[workspace][key] == source[key], (state, key)
                child = next(value for key, value in entries.items() if key != workspace)
                assert not child.get("jobId") and not child.get("generationId")
                assert child["messages"][0]["content"] == message
                assert child["messages"][0].get("examVersion") is None
                assert not entries[workspace]["messages"], "Old transcript must remain unchanged"
            assert counters["interpretations"] == (
                1 if model and model != "toggle-status" else 0
            ), counters
            assert counters["evaluations"] == 0, counters
            assert counters["generation"] == 0 and not forbidden and not errors, (forbidden, errors)
            results.append(
                {"state": state, "subject": subject, "freshWorkspace": fresh, **counters}
            )
            context.close()
        browser.close()
    print(
        json.dumps(
            {
                "evidence": "MOUNTED_REACT_SYNTHETIC_FIXTURES",
                "cases": results,
                "realInference": 0,
                "generatedExams": 0,
            }
        )
    )


def main():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="astra-agent-v3-") as directory:
        process = subprocess.Popen(
            [sys.executable, __file__, "--serve", str(port), directory],
            cwd=ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            with httpx.Client(trust_env=False) as client:
                for _ in range(100):
                    try:
                        client.get(
                            f"http://127.0.0.1:{port}/api/health", timeout=0.3
                        ).raise_for_status()
                        break
                    except httpx.TransportError:
                        time.sleep(0.1)
                else:
                    raise TimeoutError("No-inference fixture server did not start")
            observe(f"http://127.0.0.1:{port}")
        finally:
            stop_fixture_server(process)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--serve"]:
        serve(int(sys.argv[2]), sys.argv[3])
    else:
        main()
