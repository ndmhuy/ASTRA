"""Mounted live-state Chat regression with synthetic jobs and a fenced fake provider.

No exams or real inference are created. A stale browser view deliberately disagrees
with the persisted Backend state to verify the shared read projection wins.
"""

import ipaddress
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

from scripts.agent_capability_smoke import stop_fixture_server

ROOT = Path(__file__).resolve().parents[1]
RECALL = "Nhắc giúp tôi cấu hình đã chọn trong form nhé"
DISCUSS = "Cảm ơn, vậy mình xem lại nội dung trước nhé"
BAD = "Kiểm tra ngữ nghĩa fixture hỏng"
GOOD = "Hãy liệt kê tài liệu fixture tiếp theo"
STATE = "Có vẻ đề đã xong, mình nên làm gì tiếp?"


def serve(port, directory):
    import uvicorn
    from fastapi.responses import JSONResponse

    from exam_baseline.api.app import create_app
    from exam_baseline.connection import SharedConnection
    from exam_baseline.ui.contracts import WorkspaceDraft

    original = socket.socket.connect

    def offline(sock, address):
        if (
            isinstance(address, tuple)
            and address[0] != "localhost"
            and not ipaddress.ip_address(address[0]).is_loopback
        ):
            raise AssertionError("Synthetic server forbids external connections")
        return original(sock, address)

    socket.socket.connect = offline
    path = Path(directory) / ".env"
    path.write_text(
        "EXAM_MODEL=nghi/claude-haiku-4.5\nANTHROPIC_API_KEY=fixture-key\nEXAM_BASE_URL=https://fixture.invalid/v1\n"
    )
    calls = []

    def provider(request):
        assert request.url.path == "/v1/messages" and request.headers["x-api-key"] == "fixture-key"
        prompt = json.loads(json.loads(request.content)["messages"][0]["content"])
        current = prompt["context"]["grounded"]["backend"]["current"]
        assert (current["subject"], current["count"], current["minutes"]) == ("Vật Lý", 28, 50)
        message = prompt["message"]
        calls.append({"message": message, "observedStatus": current["lifecycle"]})
        if message == BAD:
            frame = {
                "dialogueAct": "QUESTION",
                "goals": [
                    {"goal": "READ_PROGRESS", "parameters": {"subject": "invalid-cross-goal-slot"}}
                ],
            }
        elif message == DISCUSS:
            frame = {
                "dialogueAct": "CONVERSATION",
                "reply": "Bạn cứ xem lại nội dung, mình sẵn sàng hỗ trợ khi cần.",
                "goals": [],
            }
        elif message == RECALL:
            frame = {
                "dialogueAct": "QUESTION",
                "goals": [{"goal": "RECALL_REQUIREMENTS", "parameters": {"what": "format"}}],
            }
        elif message == GOOD:
            frame = {
                "dialogueAct": "REQUEST",
                "goals": [{"goal": "LIST_DOCUMENTS"}],
                "reply": "",
            }
        elif message == STATE:
            assert current["lifecycle"] == "completed"
            frame = {"dialogueAct": "QUESTION", "goals": [{"goal": "READ_PROGRESS"}]}
        else:
            raise AssertionError("Unexpected synthetic model request")
        return httpx.Response(
            200,
            json={
                "type": "message",
                "role": "assistant",
                "stop_reason": "tool_use",
                "content": [{"type": "tool_use", "name": "astra_output", "input": frame}],
            },
        )

    app = create_app(
        connection=SharedConnection(path, transport=httpx.MockTransport(provider)),
        ui_output_root=Path(directory) / "ui",
        workspace_dir=ROOT / "astra-frontend/dist",
    )
    fixture = {}

    @app.middleware("http")
    async def boundary(request, call_next):
        route = request.url.path
        if request.method == "POST" and route == "/fixture/init":
            workspace = str(uuid4())
            draft = WorkspaceDraft(
                revision=0, mode="template", title="Fixture Vật Lý", draft="", messages=[]
            )
            store = app.state.ui_jobs.store
            store.save_workspace(workspace, 0, draft.storage_content("revision"))
            job, _ = store.create(
                str(uuid4()),
                "fixture",
                {
                    "status": "running",
                    "revision": 1,
                    "approved": False,
                    "rawQuestions": [],
                    "executionVersion": 1,
                    "executionOwner": "fixture",
                    "executionLeaseUntil": time.time() + 3600,
                    "checkpointVersion": 1,
                    "request": {
                        "subject": "Vật Lý",
                        "itemCount": 28,
                        "durationMinutes": 50,
                        "grade": 12,
                        "formatId": "thpt-physics",
                        "prompt": "Synthetic form requirements",
                    },
                    "progress": {
                        "completedItems": 3,
                        "totalItems": 28,
                        "percent": 10,
                        "message": "Đang soạn câu hỏi",
                    },
                },
                workspace,
            )
            fixture.update(workspace=workspace, job=job["jobId"])
            return JSONResponse(fixture)
        if request.method == "POST" and route == "/fixture/complete":
            store = app.state.ui_jobs.store
            job = store.get(fixture["job"])
            job.update(
                status="completed",
                progress={"completedItems": 28, "totalItems": 28, "percent": 100},
            )
            store.save(job)
            return JSONResponse({"completed": True})
        if route == "/fixture/calls":
            return JSONResponse({"calls": calls})
        if request.method == "POST" and "/exams/" in route:
            raise AssertionError("This fixture never generates an exam")
        return await call_next(request)

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)


def observe(base):
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge" if os.name == "nt" else None, headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        ids = page.request.post(base + "/fixture/init").json()
        frozen = page.request.get(base + "/api/workspaces").json()
        # Deliberately stale form metadata, independent of the authoritative job.
        frozen["workspaces"][0]["jobMeta"] = {
            "subject": "Tiếng Anh",
            "itemCount": 40,
            "durationMinutes": 30,
        }
        errors, forbidden = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))

        def intercept(route):
            request = route.request
            path = urlsplit(request.url).path
            if not request.url.startswith(base + "/"):
                route.fulfill(status=200, body="")
            elif request.method == "POST" and "/exams/" in path:
                forbidden.append(path)
                route.abort()
            elif path == "/api/workspaces" and request.method == "GET":
                route.fulfill(json=frozen)
            elif path.endswith("/events"):
                route.fulfill(
                    content_type="text/event-stream", body=": deliberately stale client\n\n"
                )
            elif path.endswith("/status") and "/exams/" in path:
                route.fulfill(
                    json={
                        "jobId": ids["job"],
                        "status": "running",
                        "executionVersion": 1,
                        "completedItems": 3,
                        "totalItems": 40,
                        "percent": 10,
                        "stage": 1,
                        "stageName": "composer",
                        "estimatedSecondsLeft": 0,
                        "statusMessage": "Đang soạn câu hỏi",
                    }
                )
            else:
                route.continue_()

        page.route("**/*", intercept)
        page.goto(base)
        page.locator(".sidebar-exam").first.click()
        composer = page.get_by_role("textbox", name="Yêu cầu soạn đề", exact=True)

        def send(message, expected):
            composer.fill(message)
            composer.press("Enter")
            expect(page.get_by_text(expected, exact=False).last).to_be_visible(timeout=10000)
            expect(composer).to_be_enabled()
            page.wait_for_timeout(550)  # Respect the unchanged four-turn/two-second burst guard.
            return page.locator(".chat-history article").last.inner_text()

        send("mày đang tạo đề gì", "Đề Vật Lý THPT")
        send("mày tạo đề tới đâu rồi", "Đã lưu 3/28 câu")
        send("khi nào xong", "Chưa có ước lượng thời gian hoàn tất")
        send("cái app này làm được gì", "ASTRA giúp bạn soạn đề theo mẫu")
        recall = send(RECALL, "50 phút")
        assert "Vật Lý" in recall and "50 phút" in recall
        send("đề này đã soạn xong rồi", "Đã lưu 3/28 câu")
        assert (
            page.request.get(
                base + "/agent/workspace-state?workspace_id=" + ids["workspace"]
            ).json()["current"]["lifecycle"]
            == "running"
        )
        page.request.post(base + "/fixture/complete")
        send(STATE, "Đã soạn xong 28 câu")
        send(DISCUSS, "Bạn cứ xem lại nội dung")
        send(BAD, "Mình chưa xác định được thao tác từ câu này")
        expect(
            page.locator(".chat-history").get_by_text("Đã soạn xong 28 câu", exact=False).last
        ).to_be_visible()
        send(GOOD, "Chưa có tài liệu")
        calls = page.request.get(base + "/fixture/calls").json()["calls"]
        assert [c["message"] for c in calls] == [RECALL, STATE, DISCUSS, BAD, GOOD], calls
        assert (
            page.request.get(
                base + "/agent/workspace-state?workspace_id=" + ids["workspace"]
            ).json()["current"]["approved"]
            is False
        )
        assert len(page.request.get(base + "/api/workspaces").json()["workspaces"]) == 1
        assert not forbidden and not errors, (forbidden, errors)
        output = ROOT / "tmp/chat-live-state"
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output / "verified-state-chat.png"))
        browser.close()
    print(
        json.dumps(
            {
                "evidence": "MOUNTED_CHAT_LIVE_STATE_SYNTHETIC_FIXTURES",
                "cases": 10,
                "syntheticInterpretations": len(calls),
                "realInference": 0,
                "generatedExams": 0,
                "chatUsedBackendDespiteStaleUI": True,
                "schemaFailureDidNotBlockNextTurn": True,
            }
        )
    )


def main():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="astra-chat-state-") as directory:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "scripts.chat_live_state_smoke",
                "--serve",
                str(port),
                directory,
            ],
            cwd=ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        base = f"http://127.0.0.1:{port}"
        try:
            with httpx.Client(trust_env=False) as client:
                for _ in range(100):
                    try:
                        client.get(base + "/api/health", timeout=0.3).raise_for_status()
                        break
                    except httpx.TransportError:
                        time.sleep(0.1)
                else:
                    raise TimeoutError("Synthetic server did not start")
            observe(base)
        finally:
            stop_fixture_server(process)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--serve"]:
        serve(int(sys.argv[2]), sys.argv[3])
    else:
        main()
