"""Run the built ASTRA app with a semantic fixture. Use --intake-only for chat intake."""

import multiprocessing
import os
import socket
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]


def serve(port: int, runs: str):
    import uvicorn

    from exam_baseline.agent.semantics import normalize_frame
    from exam_baseline.api.app import create_app
    from exam_baseline.config import Settings

    async def interpret(turn):
        # Synthetic provider fixture: these strings are test inputs, never runtime routing.
        fixtures = {
            "Cho cô vào nơi thiết lập mẫu": {
                "dialogueAct": "REQUEST",
                "goals": [{"goal": "OPEN_CONFIGURATION"}],
            },
            "Mở danh sách rồi thu gọn thanh điều hướng giúp cô": {
                "dialogueAct": "REQUEST",
                "goals": [
                    {"goal": "FIND_CONVERSATIONS"},
                    {"goal": "SET_NAVIGATION", "parameters": {"collapsed": True}},
                ],
            },
            "Điền đề bài câu 1 là Tính 2+2.": {
                "dialogueAct": "REQUEST",
                "goals": [
                    {
                        "goal": "FILL_EDITOR",
                        "parameters": {"number": 1, "field": "stem", "value": "Tính 2+2."},
                    }
                ],
            },
            "Tạo đề thi thử tốt nghiệp": {
                "dialogueAct": "REQUEST",
                "goals": [{"goal": "PREPARE_EXAM", "parameters": {"family": "thpt"}}],
            },
            "Hướng dẫn cô soạn đề Sinh THPT": {
                "dialogueAct": "QUESTION",
                "goals": [
                    {
                        "goal": "INSPECT_FORMAT",
                        "parameters": {"family": "thpt", "subject": "Sinh Học"},
                    }
                ],
            },
            "Cô muốn tạo đề Toán THPT 15 câu, 45 phút": {
                "dialogueAct": "REQUEST",
                "goals": [
                    {
                        "goal": "REQUEST_GENERATION",
                        "parameters": {"family": "thpt", "subject": "Toán Học"},
                    }
                ],
            },
            "Đừng tạo đề, chỉ xem cấu trúc": {
                "dialogueAct": "QUESTION",
                "goals": [{"goal": "INSPECT_FORMAT"}],
                "constraints": ["NO_GENERATION"],
            },
        }
        return normalize_frame(fixtures.get(turn.message, {"dialogueAct": "AMBIGUOUS"}))

    app = create_app(
        Settings(_env_file=None, provider="mock", model="mock-fixture-v1"),
        agent_interpreter=interpret,
        workspace_dir=ROOT / "astra-frontend" / "dist",
        ui_output_root=Path(runs),
    )
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)


def observe(base_url: str, intake_only: bool = False):
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as playwright:
        channel = "msedge" if os.name == "nt" else None
        browser = playwright.chromium.launch(channel=channel)
        business_writes: list[str] = []
        agent_calls: list[str] = []

        def record(request):
            if request.method == "POST" and "/api/exams/" in request.url:
                business_writes.append(request.url)
            if request.url.endswith("/agent/turn"):
                agent_calls.append(request.url)

        if not intake_only:
            page = browser.new_page(reduced_motion="reduce")
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
            expect(
                page.get_by_role("button", name="Mở rộng thanh điều hướng").first
            ).to_be_visible()
            composer.fill("Tới đâu rồi?")
            composer.press("Enter")
            expect(page.get_by_text("Đề vẫn ở bản nháp", exact=False)).to_be_visible()
            assert len(agent_calls) == 2 and not business_writes
            run_workflows(page, composer, business_writes)
            # Keep the second browser flow outside the shared loopback burst window.
            page.wait_for_timeout(2100)
        product = browser.new_page(reduced_motion="reduce")
        product.on("request", record)
        product.goto(base_url)
        product.locator("textarea").first.wait_for(timeout=12000)
        before = len(business_writes)
        calls_before_intake = len(agent_calls)
        for text, expected in [
            ("Hướng dẫn cô soạn đề Sinh THPT", "Sinh Học THPT có 28 câu"),
            ("Tạo đề thi thử tốt nghiệp", "Thầy cô muốn ôn thi tốt nghiệp môn nào?"),
            ("sinh", "Đã chọn mẫu. Sinh Học THPT có 28 câu"),
        ]:
            editor = product.locator("textarea").first
            editor.fill(text)
            editor.press("Enter")
            expect(product.get_by_text(expected, exact=False).first).to_be_visible()
        expect(product.get_by_role("dialog")).to_be_visible()
        assert (
            len(agent_calls) == calls_before_intake + 2
        )  # Subject answer is contextual, zero inference.
        expect(product.locator(".sidebar-exam-title").first).to_have_text(
            "Đề thi thử Sinh Học THPT"
        )
        product.keyboard.press("Escape")
        expect(product.get_by_role("dialog")).to_have_count(0)
        editor = product.locator("textarea").first
        editor.fill("Đừng tạo đề, chỉ xem cấu trúc")
        editor.press("Enter")
        expect(product.get_by_role("dialog")).to_have_count(0)
        expect(product.get_by_text("Sinh Học THPT có 28 câu", exact=False)).to_have_count(3)

        product.locator('input[type="file"]').set_input_files(
            {"name": "bitwise.pdf", "mimeType": "application/pdf", "buffer": b"%PDF-fixture"}
        )
        editor.fill("tạo đề từ đây (môn: tin học)")
        editor.press("Enter")
        expect(product.get_by_text("ASTRA chưa thể đọc tệp đính kèm.", exact=False)).to_be_visible()
        assert len(agent_calls) == calls_before_intake + 3
        assert len(business_writes) == before

        home = browser.new_page(reduced_motion="reduce")
        home.on("request", record)
        home.goto(base_url)
        home.route("**/api/exam-formats", lambda route: route.abort(), times=1)
        home_composer = home.locator("textarea").first
        home_composer.fill("Mở cấu hình")
        home_composer.press("Enter")
        preset = home.get_by_role("dialog", name="Thiết lập đề theo yêu cầu")
        expect(preset.get_by_role("alert")).to_contain_text("Không kết nối được máy chủ")
        preset.get_by_role("button", name="Tải lại danh sách mẫu đề").click()
        expect(preset.get_by_role("alert")).to_have_count(0)
        expect(preset.get_by_text("Đề thi THPT Quốc gia")).to_be_visible()
        assert len(agent_calls) == calls_before_intake + 3
        assert len(business_writes) == before

        math = browser.new_page(reduced_motion="reduce")
        math.on("request", record)
        math.goto(base_url)
        starts = []

        def submit(route):
            starts.append(route.request.post_data_json)
            route.fulfill(status=202, json={"jobId": str(uuid4()), "status": "queued"})

        math.route("**/api/exams/generate*", submit)
        math_composer = math.locator("textarea").first
        math_composer.fill("Cô muốn tạo đề Toán THPT 15 câu, 45 phút")
        math_composer.press("Enter")
        expect(math.get_by_text("Toán THPT có 22 câu, 90 phút.", exact=False)).to_contain_text(
            "Nhắn “Đồng ý”"
        )
        assert len(agent_calls) == calls_before_intake + 4 and not starts
        math_composer.fill("ok")
        math_composer.press("Enter")
        math_setup = math.get_by_role("dialog")
        expect(
            math_setup.get_by_text("Bấm “Tạo đề thi” để xác nhận gửi yêu cầu.", exact=False)
        ).to_be_visible()
        assert len(agent_calls) == calls_before_intake + 4 and len(business_writes) == before
        if screenshot := os.environ.get("ASTRA_CHAT_SMOKE_SCREENSHOT"):
            math.screenshot(path=screenshot)
        math_setup.get_by_role("button", name="Tạo đề thi").click()
        expect(math.get_by_text("Máy chủ đã nhận công việc tạo đề", exact=False)).to_be_visible()
        assert len(starts) == 1 and len(business_writes) == before + 1
        assert (starts[0]["formatId"], starts[0]["itemCount"], starts[0]["durationMinutes"]) == (
            "thpt-math",
            22,
            90,
        )
        assert starts[0]["uploadedFiles"] == [] and "15 câu" not in starts[0]["prompt"]
        browser.close()
    print(
        "Mounted React passed: catalog retry, Biology intake, PDF rejection and Math confirmation."
    )


def run_workflows(page, composer, business_writes):
    import re

    from playwright.sync_api import expect

    def say(text):
        composer.fill(text)
        composer.press("Enter")

    starts = []
    drafts = {}
    job = str(uuid4())
    generated_workspace = None
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
        nonlocal approved, generated_workspace
        request_url = urlsplit(route.request.url)
        path = request_url.path
        if path.endswith("/generate"):
            generated_workspace = parse_qs(request_url.query).get("workspace_id", [None])[0]
            starts.append(route.request.post_data_json)
            route.fulfill(status=202, json={"jobId": job, "status": "queued"})
        elif path.endswith("/status"):
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
        elif path.endswith("/events"):
            route.abort()
        elif path.endswith("/" + job):
            route.fulfill(json={**pkg, "approved": approved})
        elif path.endswith("/questions/1") and route.request.method == "PUT":
            request = route.request.post_data_json
            assert request["revision"] == pkg["revision"]
            assert request["question"]["stableId"] == "P1-01"
            approved = False
            pkg["revision"] = 2
            pkg["contentHash"] = "b" * 64
            pkg["questions"][0].update(stem=request["question"]["stem"], examRevision=2)
            pkg["preview"].update(revision=2, contentHash=pkg["contentHash"])
            route.fulfill(json={**pkg, "approved": approved})
        elif path.endswith("/fixture.pdf"):
            route.fulfill(content_type="application/pdf", body="%PDF-1.4")
        elif path.endswith("/approve"):
            approved = True
            route.fulfill(json={**pkg, "approved": True})
        elif path.endswith("/export"):
            route.fulfill(content_type="application/json", body="{}")
        else:
            route.abort()

    def save_draft(route):
        if route.request.method != "PUT":
            route.fallback()
            return
        workspace_id = urlsplit(route.request.url).path.rsplit("/", 1)[-1]
        draft = route.request.post_data_json
        revision = draft["revision"] + 1
        drafts[workspace_id] = {**draft, "revision": revision}
        route.fulfill(json={"revision": revision})

    page.route("**/api/exams/**", exam_http)
    page.route("**/api/workspaces/*", save_draft)
    say("Chọn V-ACT và xem chi tiết")
    dialog = page.get_by_role("dialog")
    expect(dialog.get_by_text("120 câu · 150 phút")).to_be_visible()
    expect(dialog.locator("input:checked")).to_have_count(1)
    expect(dialog.locator(".is-selected")).to_contain_text("V-ACT")
    page.keyboard.press("Escape")

    say("Tạo đề V-ACT")
    expect(
        dialog.get_by_text("Bấm “Tạo đề thi” để xác nhận gửi yêu cầu.", exact=False)
    ).to_be_visible()
    expect(dialog.locator(".is-selected")).to_contain_text("V-ACT")
    assert not starts
    page.keyboard.press("Escape")

    say("Đổi tên đoạn chat thành Ôn Toán tháng 12")
    expect(page.get_by_text("Đã đổi tên cuộc trò chuyện", exact=False)).to_be_visible()
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
    expect(page.get_by_text("Đề thử fixture", exact=True).first).to_be_visible()
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
    expect(page.get_by_role("button", name="Ôn Toán tháng 12", exact=True)).to_be_visible()
    say("Xuất JSON")
    expect(page.get_by_text("Tải tệp JSON của phiên bản 1", exact=False)).to_be_visible()
    with (
        page.expect_download() as download,
        page.expect_response(
            lambda response: (
                response.ok
                and response.request.method == "PUT"
                and "/api/workspaces/" in response.url
                and any(
                    message["content"] == "Đã yêu cầu trình duyệt tải tệp."
                    for message in response.request.post_data_json["messages"]
                )
            )
        ),
    ):
        say("Xác nhận")
    assert download.value.suggested_filename == "dap_an.json"
    assert len(starts) == 1 and len(business_writes) == 2
    expect(page.get_by_text(re.compile("Đã yêu cầu trình duyệt tải tệp"))).to_be_visible()

    def workspace_list(route):
        response = route.fetch()
        payload = response.json()
        workspaces = {workspace["id"]: workspace for workspace in payload["workspaces"]}
        for workspace_id, draft in drafts.items():
            workspace = workspaces.setdefault(
                workspace_id,
                {"id": workspace_id, "createdAt": datetime.now(timezone.utc).isoformat()},
            )
            workspace.update(draft)
        if generated_workspace:
            workspaces[generated_workspace].update(jobId=job, jobStatus="completed")
        payload["workspaces"] = list(workspaces.values())
        route.fulfill(response=response, json=payload)

    page.route("**/api/workspaces", workspace_list)
    page.reload()
    composer.wait_for(timeout=12000)
    say("Mở chat Ôn Toán tháng 12")
    expect(page.get_by_text("Đã yêu cầu trình duyệt tải tệp.", exact=True)).to_be_visible()
    say("Cô đã chọn dạng đề nào?")
    expect(page.get_by_text("Mẫu gần nhất là Toán THPT", exact=False)).to_be_visible()
    assert len(starts) == 1
    say("Điền đề bài câu 1 là Tính 2+2.")
    expect(dialog.get_by_role("textbox", name="Đề bài")).to_have_value("Tính 2+2.")
    assert pkg["revision"] == 1
    dialog.get_by_role("button", name="Lưu thay đổi").click()
    expect(dialog).to_have_count(0)
    expect(page.locator(".question-stem").first).to_contain_text("Tính 2+2.")
    assert pkg["revision"] == 2
    say("Xuất JSON")
    expect(page.get_by_text("Phiên bản hiện tại cần được phê duyệt", exact=False)).to_be_visible()

    page.get_by_role("button", name="Tạo đề mới").click()
    page.get_by_role("button", name="Soạn từ mẫu").click()
    dialog.get_by_text("120 câu · 150 phút").click()
    dialog.get_by_role("button", name="Tạo đề thi").click()
    expect(dialog).to_have_count(0)
    expect(page.get_by_text("Đề thử fixture", exact=True).first).to_be_visible()
    assert [item["formatId"] for item in starts] == ["thpt-math", "vact"]


def main():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="astra-agent-") as runs:
        process = multiprocessing.get_context("spawn").Process(target=serve, args=(port, runs))
        process.start()
        try:
            with httpx.Client(trust_env=False) as client:
                for _ in range(100):
                    if not process.is_alive():
                        raise RuntimeError("Agent smoke server exited")
                    try:
                        client.get(base + "/api/health", timeout=0.3).raise_for_status()
                        break
                    except httpx.TransportError:
                        time.sleep(0.1)
                else:
                    raise TimeoutError("Agent smoke server did not start")
            observe(base, intake_only="--intake-only" in sys.argv[1:])
        finally:
            process.terminate()
            process.join(timeout=10)


if __name__ == "__main__":
    main()
