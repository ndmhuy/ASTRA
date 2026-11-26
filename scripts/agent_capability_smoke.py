"""Mounted React coverage for the 16 adapters outside the original smoke.

All semantic/business responses are explicit synthetic browser fixtures. The real
catalog, React handlers, confirmation gates and local transcript store are used.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]


def serve(port, directory):
    import uvicorn

    from exam_baseline.api.app import create_app
    from exam_baseline.config import Settings

    async def no_inference(turn):
        raise AssertionError("Browser fixture must intercept every model turn")

    app = create_app(
        Settings.for_offline(),
        agent_interpreter=no_inference,
        ui_output_root=Path(directory),
        workspace_dir=ROOT / "astra-frontend/dist",
    )
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)


def observe(base):
    from playwright.sync_api import expect, sync_playwright

    now = "2026-11-27T00:00:00.000Z"
    workspace, job, source = str(uuid4()), str(uuid4()), str(uuid4())
    question = {
        "id": 1,
        "stableId": "P1-01",
        "part": "P1",
        "examRevision": 1,
        "stem": "Tính 1+1.",
        "choices": {"A": "2", "B": "3", "C": "4", "D": "5"},
        "key": "A",
        "explanation": "Cộng.",
        "topic": "Cộng",
        "level": "NHAN_BIET",
        "status": "VERIFIED",
        "answerCheck": "matched",
    }
    preview = {
        "status": "failed",
        "revision": 1,
        "contentHash": "a" * 64,
        "sourceHash": "a" * 64,
        "compilerAvailable": True,
        "draft": True,
        "statusUrl": "",
        "pdfUrl": "",
        "logUrl": "",
    }
    package = {
        "examId": job,
        "title": "Fixture complete",
        "subject": "Toán Học",
        "grade": 12,
        "revision": 1,
        "contentHash": "a" * 64,
        "durationMinutes": 90,
        "approved": False,
        "blueprint": {"examType": "THPT_STANDARD"},
        "warnings": [],
        "questions": [question],
        "preview": preview,
    }
    session = {
        "id": workspace,
        "title": "Fixture complete",
        "mode": "template",
        "status": "complete",
        "createdAt": now,
        "messages": [
            {"id": source, "role": "user", "content": "Đề Toán THPT fixture", "timestamp": now}
        ],
        "questions": [question],
        "draft": "",
        "jobId": job,
        "previousCount": 1,
        "package": package,
        "preview": preview,
        "meta": {
            "title": "Fixture complete",
            "subject": "Toán Học",
            "duration": 90,
            "completedCount": 1,
            "totalCount": 1,
        },
        "conversation": {
            "schemaVersion": 1,
            "revision": 0,
            "updatedAt": now,
            "titleOrigin": "manual",
        },
        "notes": [
            {
                "id": str(uuid4()),
                "sourceId": source,
                "jobId": job,
                "number": 1,
                "part": "P1",
                "stableId": "P1-01",
                "instruction": "dễ hơn",
                "status": "awaiting_review",
            }
        ],
    }
    observed, writes = [], []
    decision = {"kind": "clarify", "intents": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge" if os.name == "nt" else None)
        page = browser.new_page(reduced_motion="reduce")
        page.clock.install()
        held = []
        page.add_init_script(
            'localStorage.setItem("astra.sessions.v1", '
            + json.dumps(json.dumps([session], ensure_ascii=False))
            + ");"
        )

        def semantic(route):
            turn = route.request.post_data_json
            if turn["message"] == "Late context fixture":
                held.append((route, turn))
                return
            route.fulfill(
                json={
                    "schemaVersion": "astra-intent-v1",
                    "clientMessageId": turn["clientMessageId"],
                    "decision": decision,
                }
            )

        def business(route):
            url = route.request.url
            if route.request.method == "POST":
                writes.append(url)
            if url.endswith("/questions/1/verify"):
                assert route.request.post_data_json == {"revision": 1}
                route.fulfill(json=package)
            elif "/preview" in url:
                preview.update(status="ready")
                route.fulfill(json=preview)
            elif url.endswith("/" + job):
                route.fulfill(json=package)
            else:
                raise AssertionError("Unexpected business request: " + url)

        page.route("**/agent/turn", semantic)
        page.route("**/api/exams/**", business)
        page.goto(base)
        page.locator("textarea").first.wait_for(timeout=12000)
        page.locator('.sidebar-exam[title="Fixture complete"]').click()
        composer = page.locator("textarea").first

        def run(intents, message, expected):
            nonlocal decision
            decision = {"kind": "task", "intents": intents}
            composer.fill(message)
            composer.press("Enter")
            if any(item["id"] == "CREATE_SESSION" for item in intents):
                expect(page.locator(".sidebar-exam-title")).to_have_count(2)
                page.wait_for_function(
                    "expected => JSON.parse(localStorage.getItem('astra.sessions.v1'))"
                    ".some(session => session.messages.some(message => "
                    "message.role === 'assistant' && message.content.includes(expected)))",
                    arg=expected,
                )
            else:
                expect(page.get_by_text(expected, exact=False).last).to_be_visible()
            observed.extend(item["id"] for item in intents)

        def one(name, args, message, expected):
            run([{"id": name, "args": args}], message, expected)

        one("SHOW_FORMATS", {}, "Thực hiện danh sách mẫu fixture", "Toán THPT: 22 câu")
        one("WARNINGS", {}, "Thực hiện đọc cảnh báo fixture", "Cảnh báo nguồn: 0")
        one(
            "FOCUS_SECTION",
            {"part": "P1"},
            "Thực hiện tới phần P1 fixture",
            "Đã cuộn đến phần thi yêu cầu.",
        )
        one("SCROLL_TOP", {}, "Thực hiện tới đầu trang fixture", "Đã cuộn lên đầu đề.")
        run(
            [{"id": "OPEN_EDITOR", "args": {"number": 1}}, {"id": "CLOSE_EDITOR", "args": {}}],
            "Thực hiện mở rồi đóng trình sửa câu 1 fixture",
            "Đã đóng trình chỉnh sửa.",
        )
        expect(page.get_by_role("dialog")).to_have_count(0)
        one("VERIFY_QUESTION", {"number": 1}, "Thực hiện kiểm chứng câu 1 fixture", "bằng bộ giải.")
        composer.fill("Xác nhận")
        composer.press("Enter")
        expect(page.get_by_text("hai đáp án khớp nhau", exact=False)).to_be_visible()
        composer.fill("Xác nhận")
        composer.press("Enter")
        expect(
            page.get_by_text("Hiện chưa có thao tác nào đang chờ xác nhận.", exact=True)
        ).to_be_visible()
        one(
            "REGENERATE_QUESTION",
            {"number": 1, "instruction": "đơn giản hơn"},
            "Thực hiện sinh lại câu 1 đơn giản hơn fixture",
            "Sinh lại câu 1",
        )
        page.clock.fast_forward(301000)
        composer.fill("Xác nhận")
        composer.press("Enter")
        expect(
            page.get_by_text("Xác nhận đã hết hiệu lực hoặc trạng thái đã thay đổi.", exact=False)
        ).to_be_visible()
        one(
            "REGENERATE_QUESTION",
            {"number": 1, "instruction": "đơn giản hơn"},
            "Thực hiện sinh lại câu 1 đơn giản hơn lần nữa fixture",
            "Sinh lại câu 1",
        )
        composer.fill("Hủy yêu cầu")
        composer.press("Enter")
        expect(
            page.get_by_text("Đã hủy yêu cầu trò chuyện đang chờ.", exact=True).last
        ).to_be_visible()
        one("APPLY_NOTES", {}, "Thực hiện áp dụng ghi chú fixture", "Áp dụng 1 ghi chú")
        composer.fill("Hủy yêu cầu")
        composer.press("Enter")
        expect(
            page.get_by_text("Đã hủy yêu cầu trò chuyện đang chờ.", exact=True).last
        ).to_be_visible()
        one("RETRY_PREVIEW", {}, "Thực hiện dựng lại bản in fixture", "Bản xem trước đã sẵn sàng.")
        one(
            "SET_DRAFT",
            {"text": "Nội dung bản nháp"},
            "Thực hiện điền Nội dung bản nháp fixture",
            "Đã đưa nội dung vào ô nhập.",
        )
        expect(composer).to_have_value("Nội dung bản nháp")
        one(
            "CHAT_MESSAGE",
            {"operation": "draft", "number": 1},
            "Thực hiện lấy tin nhắn 1 fixture",
            "Đã đưa tin nhắn vào ô nhập.",
        )
        expect(composer).to_have_value("Đề Toán THPT fixture")
        one(
            "DELETE_SESSION",
            {"title": "Fixture complete"},
            "Thực hiện xóa Fixture complete fixture",
            "Xóa “Fixture complete” khỏi tủ đề",
        )
        composer.fill("Hủy yêu cầu")
        composer.press("Enter")
        expect(
            page.get_by_text("Đã hủy yêu cầu trò chuyện đang chờ.", exact=True).last
        ).to_be_visible()
        one(
            "CREATE_SESSION",
            {},
            "Thực hiện workspace mới fixture",
            "Đã mở một không gian soạn đề mới.",
        )
        draft_title = page.locator(".sidebar-exam-title").first.inner_text()
        page.locator('.sidebar-exam[title="Fixture complete"]').click()
        composer.fill("Late context fixture")
        composer.press("Enter")
        for _ in range(100):
            if held:
                break
            page.wait_for_timeout(10)
        assert held, "Late-response fixture did not reach interpretation"
        page.locator(".sidebar-exam").filter(has=page.get_by_text(draft_title, exact=True)).click()
        pending_route, pending_turn = held.pop()
        pending_route.fulfill(
            json={
                "schemaVersion": "astra-intent-v1",
                "clientMessageId": pending_turn["clientMessageId"],
                "decision": {"kind": "task", "intents": [{"id": "OPEN_SETUP", "args": {}}]},
            }
        )
        expect(page.get_by_role("dialog")).to_have_count(0)
        one(
            "SELECT_FORMAT",
            {"format": "thpt-math"},
            "Thực hiện chọn mẫu Toán THPT fixture",
            "Đã chọn mẫu.",
        )
        page.keyboard.press("Escape")
        run(
            [{"id": "FORMAT_DETAILS", "args": {}}, {"id": "CLOSE_SETUP", "args": {}}],
            "Thực hiện chi tiết rồi đóng cấu hình fixture",
            "Đã đóng phần cấu hình.",
        )
        expect(page.get_by_role("dialog")).to_have_count(0)
        # HOME's receipt stays with its originating conversation after navigating away.
        decision = {"kind": "task", "intents": [{"id": "HOME", "args": {}}]}
        composer.fill("Thực hiện về trang bắt đầu fixture")
        composer.press("Enter")
        expect(page.get_by_role("button", name="Soạn từ mẫu", exact=True)).to_be_visible()
        observed.append("HOME")
        assert (
            len(writes) == 2
            and any("/verify" in url for url in writes)
            and any("/preview" in url for url in writes)
        )
        browser.close()
    print(
        json.dumps(
            {
                "evidence": "MOUNTED_REACT_SYNTHETIC_FIXTURES",
                "observedAdapters": sorted(set(observed)),
                "businessFixtureWrites": len(writes),
                "upstreamInference": 0,
            },
            ensure_ascii=True,
        )
    )


def main():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="astra-capability-") as directory:
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
                    raise TimeoutError("Capability fixture server did not start")
            observe(f"http://127.0.0.1:{port}")
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--serve"]:
        serve(int(sys.argv[2]), sys.argv[3])
    else:
        main()
