"""Run the built ASTRA app over local HTTP with a semantic provider fixture."""

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


def serve(port: int, runs: str):
    import uvicorn

    from exam_baseline.agent.contracts import Decision, Intent
    from exam_baseline.api.app import create_app
    from exam_baseline.config import Settings

    async def interpret(turn):
        if turn.message == "Cho cô vào nơi thiết lập mẫu":
            return Decision(kind="task", intents=[Intent(id="OPEN_SETUP", args={})])
        if turn.message == "Mở danh sách rồi thu gọn thanh điều hướng giúp cô":
            return Decision(
                kind="task",
                intents=[
                    Intent(id="LIST_SESSIONS", args={}),
                    Intent(id="SET_SIDEBAR", args={"collapsed": True}),
                ],
            )
        return Decision(kind="clarify")

    app = create_app(
        Settings(_env_file=None, provider="mock", model="mock-fixture-v1"),
        agent_interpreter=interpret,
        workspace_dir=ROOT / "astra-frontend" / "dist",
        ui_output_root=Path(runs),
    )
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)


def observe(base_url: str):
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as playwright:
        channel = "msedge" if os.name == "nt" else None
        browser = playwright.chromium.launch(channel=channel)
        page = browser.new_page(reduced_motion="reduce")
        business_writes: list[str] = []
        agent_calls: list[str] = []

        def record(request):
            if request.method == "POST" and "/api/exams/" in request.url:
                business_writes.append(request.url)
            if request.url.endswith("/agent/turn"):
                agent_calls.append(request.url)

        page.on("request", record)
        page.goto(base_url)
        composer = page.locator("textarea").first
        composer.wait_for(timeout=12000)
        composer.fill("Chào em")
        composer.press("Enter")
        expect(page.get_by_text("Em chào thầy cô!", exact=False)).to_be_visible()
        expect(page.get_by_role("dialog")).to_have_count(0)
        assert not agent_calls

        composer.fill("Cho cô vào nơi thiết lập mẫu")
        composer.press("Enter")
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.get_by_text("Đã mở phần cấu hình mẫu đề.", exact=True)).to_be_visible()
        assert len(agent_calls) == 1 and not business_writes
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog")).to_have_count(0)
        composer.fill("Mở danh sách rồi thu gọn thanh điều hướng giúp cô")
        composer.press("Enter")
        expect(page.get_by_role("button", name="Mở rộng thanh điều hướng").first).to_be_visible()
        composer.fill("Tới đâu rồi?")
        composer.press("Enter")
        expect(page.get_by_text("Đề vẫn ở bản nháp", exact=False)).to_be_visible()
        assert len(agent_calls) == 2 and not business_writes
        run_workflows(page, composer, business_writes)
        browser.close()
    print(
        "Mounted React: greeting and same-origin fixture navigation, catalog intake, "
        "fixture lifecycle, notes and approval/export gates observed."
    )


def run_workflows(page, composer, business_writes):
    import re

    from playwright.sync_api import expect

    def say(text):
        composer.fill(text)
        composer.press("Enter")

    starts = []
    job = str(uuid4())
    finished = False
    approved = False
    digest = "a" * 64
    pkg = {
        "examId": job,
        "title": "Đề thử fixture",
        "subject": "Toán Học",
        "grade": 12,
        "revision": 1,
        "contentHash": digest,
        "durationMinutes": 90,
        "approved": False,
        "blueprint": {"examType": "THPT_STANDARD"},
        "warnings": [],
        "questions": [
            {
                "id": 1,
                "stableId": "P1-01",
                "examRevision": 1,
                "part": "P1",
                "stem": "Tính 1+1.",
                "choices": {"A": "2", "B": "3", "C": "4", "D": "5"},
                "key": "A",
                "explanation": "Cộng.",
                "topic": "Phép cộng",
                "level": "NHAN_BIET",
                "status": "VERIFIED",
                "answerCheck": "matched",
            }
        ],
        "preview": {
            "status": "ready",
            "revision": 1,
            "contentHash": digest,
            "sourceHash": digest,
            "compilerAvailable": True,
            "draft": True,
            "statusUrl": "",
            "pdfUrl": f"/api/exams/{job}/fixture.pdf",
            "logUrl": "",
        },
    }

    def exam_http(route):
        nonlocal approved
        url = route.request.url
        if url.endswith("/generate"):
            starts.append(route.request.post_data_json)
            route.fulfill(status=202, json={"jobId": job, "status": "queued"})
        elif url.endswith("/status"):
            route.fulfill(
                json={
                    "stage": 5 if finished else 2,
                    "stageName": "composer",
                    "percent": 100 if finished else 25,
                    "estimatedSecondsLeft": 0,
                    "completedItems": int(finished),
                    "totalItems": 1,
                    "statusMessage": "Đang soạn thử",
                    "status": "completed" if finished else "running",
                }
            )
        elif url.endswith("/events"):
            route.abort()
        elif url.endswith("/" + job):
            route.fulfill(json={**pkg, "approved": approved})
        elif url.endswith("/fixture.pdf"):
            route.fulfill(content_type="application/pdf", body="%PDF-1.4")
        elif url.endswith("/approve"):
            approved = True
            route.fulfill(json={**pkg, "approved": True})
        elif "/export?" in url:
            route.fulfill(content_type="application/json", body="{}")
        else:
            route.abort()

    page.route("**/api/exams/**", exam_http)
    say("Chọn V-ACT và xem chi tiết")
    dialog = page.get_by_role("dialog")
    expect(dialog.get_by_text("120 câu · 150 phút")).to_be_visible()
    expect(dialog.locator("input:checked")).to_have_count(1)
    expect(dialog.locator(".is-selected")).to_contain_text("V-ACT")
    page.keyboard.press("Escape")

    say("Tạo đề THPT 15 câu, 45 phút")
    expect(page.get_by_text("cố định 22 câu, 90 phút", exact=False)).to_be_visible()
    assert not starts
    say("Tạo đề Toán THPT")
    expect(
        dialog.get_by_text("Bấm “Tạo đề thi” để xác nhận gửi yêu cầu.", exact=False)
    ).to_be_visible()
    assert not starts
    dialog.get_by_role("button", name="Tạo đề thi").click()
    expect(page.get_by_text("Máy chủ đã nhận công việc tạo đề", exact=False)).to_be_visible()
    assert len(starts) == 1 and starts[0]["formatId"] == "thpt-math"
    assert starts[0]["uploadedFiles"] == []
    assert "Chào em" not in starts[0]["prompt"] and "15 câu" not in starts[0]["prompt"]
    say("Tới đâu rồi?")
    expect(page.get_by_text("Cập nhật gần nhất", exact=False)).to_be_visible()
    say("Sửa câu 1 dễ hơn")
    expect(page.get_by_text("Đã lưu ghi chú cho Câu 1", exact=False)).to_be_visible()
    say("À thôi câu 1 giữ nguyên")
    expect(page.get_by_text("Đã bỏ ghi chú", exact=False)).to_be_visible()
    say("Sửa câu 1 rõ hơn")
    expect(page.get_by_text("Đã lưu ghi chú cho Câu 1", exact=False)).to_have_count(2)
    finished = True
    expect(page.get_by_text("Có ghi chú chỉnh sửa", exact=False)).to_be_visible()
    say("Xem ghi chú")
    expect(page.get_by_text("rõ hơn (chờ duyệt)", exact=False)).to_be_visible()
    say("Xem đáp án câu 1")
    expect(page.get_by_role("button", name="Xem đáp án")).to_have_attribute("aria-pressed", "true")
    say("Mở chỉnh sửa câu 1")
    expect(dialog.get_by_role("textbox", name="Đề bài")).to_be_visible()
    page.keyboard.press("Escape")
    say("Xem trước PDF")
    expect(page.frame_locator("iframe").locator("body")).to_have_count(1)
    say("Phê duyệt")
    expect(page.get_by_text("Thầy cô hãy tự mở và kiểm tra PDF", exact=False)).to_be_visible()
    assert not approved
    page.get_by_role("button", name="Mở xem trước PDF để duyệt").click()
    expect(page.get_by_role("button", name="Đã kiểm tra, phê duyệt bản này")).to_be_enabled()
    say("Phê duyệt")
    expect(page.get_by_text("Phê duyệt phiên bản 1", exact=False)).to_be_visible()
    say("Xác nhận")
    expect(page.get_by_text("Đã phê duyệt phiên bản hiện tại.")).to_be_visible()
    assert approved
    say("Xuất JSON")
    expect(page.get_by_text("Tải tệp JSON của phiên bản 1", exact=False)).to_be_visible()
    with page.expect_download() as download:
        say("Xác nhận")
    assert download.value.suggested_filename == "dap_an.json"
    assert len(starts) == 1 and len(business_writes) == 2
    expect(page.get_by_text(re.compile("Đã yêu cầu trình duyệt tải tệp"))).to_be_visible()


def main():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="astra-agent-") as runs:
        process = subprocess.Popen(
            [sys.executable, __file__, "--serve", str(port), runs],
            cwd=ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            with httpx.Client(trust_env=False) as client:
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError("Agent smoke server exited")
                    try:
                        client.get(base + "/api/health", timeout=0.3).raise_for_status()
                        break
                    except httpx.TransportError:
                        time.sleep(0.1)
                else:
                    raise TimeoutError("Agent smoke server did not start")
            observe(base)
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--serve"]:
        serve(int(sys.argv[2]), sys.argv[3])
    else:
        main()
