"""Mounted onboarding/recovery against a synthetic provider, never real inference.

Fixture keys are saved only in an owned temporary directory. No exams are created.
Run after npm run build, using a Python environment with Playwright installed.
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

import httpx

from scripts.agent_capability_smoke import stop_fixture_server

ROOT = Path(__file__).resolve().parents[1]
BAD = "fixture-invalid-key"
GOOD = "fixture-valid-key"


def serve(port, directory):
    import uvicorn
    from fastapi.responses import JSONResponse

    from exam_baseline.api.app import create_app
    from exam_baseline.connection import SharedConnection

    original_connect = socket.socket.connect

    def offline_connect(sock, address):
        if isinstance(address, tuple):
            host = address[0]
            if host != "localhost" and not ipaddress.ip_address(host).is_loopback:
                raise AssertionError("Fixture forbids external connections")
        return original_connect(sock, address)

    socket.socket.connect = offline_connect
    calls = []

    def handle(request):
        calls.append(request)
        if request.headers["x-api-key"] == BAD:
            return httpx.Response(401, json={"error": {"message": "Synthetic auth rejection"}})
        assert request.headers["x-api-key"] == GOOD
        frame = {"dialogueAct": "REQUEST", "goals": [{"goal": "LIST_DOCUMENTS"}]}
        return httpx.Response(
            200,
            json={
                "type": "message",
                "role": "assistant",
                "stop_reason": "tool_use",
                "content": [{"type": "tool_use", "name": "astra_output", "input": frame}],
            },
        )

    connection = SharedConnection(Path(directory) / ".env", transport=httpx.MockTransport(handle))
    app = create_app(
        connection=connection,
        ui_output_root=Path(directory) / "ui",
        workspace_dir=ROOT / "astra-frontend/dist",
    )

    @app.middleware("http")
    async def count(request, call_next):
        if request.url.path == "/fixture/calls":
            return JSONResponse({"calls": len(calls)})
        return await call_next(request)

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)


def observe(base, directory, viewport):
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="msedge" if os.name == "nt" else None, headless=True
        )
        context = browser.new_context(viewport=viewport, reduced_motion="reduce")
        errors, forbidden = [], []
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))

        def route(request):
            url = request.request.url
            if not url.startswith(base + "/"):
                request.fulfill(status=200, body="")  # No remote font/network requests.
            elif request.request.method == "POST" and "/exams/" in url:
                forbidden.append(url)
                request.abort()
            else:
                request.continue_()

        page.route("**/*", route)
        page.goto(base)
        dialog = page.get_by_role("dialog", name="Một key, sẵn sàng cùng bạn soạn đề.")
        expect(dialog).to_be_visible()
        key = page.locator("#connection-key")
        expect(key).to_have_attribute("type", "password")
        page.keyboard.press("Escape")
        expect(dialog).to_be_visible()
        assert page.request.get(base + "/fixture/calls").json()["calls"] == 0
        assert not (Path(directory) / ".env").exists()
        output = ROOT / "tmp/local-connection"
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output / f"onboarding-{viewport['width']}.png"))
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        key.fill(BAD)
        dialog.get_by_role("button", name="Hiện API key", exact=True).click()
        expect(key).to_have_attribute("type", "text")
        dialog.get_by_role("button", name="Ẩn API key", exact=True).click()
        dialog.get_by_role("button", name="Lưu và vào ASTRA", exact=True).click()
        expect(dialog).not_to_be_visible()
        assert BAD in (Path(directory) / ".env").read_text()
        assert page.request.get(base + "/fixture/calls").json()["calls"] == 0
        assert BAD not in page.request.get(base + "/api/connection").text()
        page.reload()
        expect(page.get_by_role("button", name="API key đã lưu", exact=True)).to_be_visible()
        expect(dialog).not_to_be_visible()
        assert page.request.get(base + "/fixture/calls").json()["calls"] == 0

        # This is a fake Chat response only. Generation requests are blocked above.
        composer = page.get_by_role("textbox", name="Yêu cầu soạn đề", exact=True)
        message = "Danh sách tài liệu fixture"
        composer.fill(message)
        composer.press("Enter")
        expect(page.get_by_text("Dịch vụ AI từ chối API key.", exact=False).last).to_be_visible()
        expect(page.get_by_role("button", name="Kiểm tra kết nối AI", exact=True)).to_be_visible(
            timeout=10000
        )
        before = page.request.get(base + "/api/workspaces").json()["workspaces"]
        assert len(before) == 1 and any(
            item["content"] == message for item in before[0]["messages"]
        )
        page.get_by_role("button", name="Kiểm tra kết nối AI", exact=True).click()
        key.fill(GOOD)
        dialog.get_by_role("button", name="Lưu kết nối", exact=True).click()
        expect(dialog).not_to_be_visible()
        after = page.request.get(base + "/api/workspaces").json()["workspaces"]
        assert before[0]["messages"] == after[0]["messages"]
        composer.fill(message + " mới")
        composer.press("Enter")
        for _ in range(50):
            if page.request.get(base + "/fixture/calls").json()["calls"] == 2:
                break
            page.wait_for_timeout(100)
        assert page.request.get(base + "/fixture/calls").json()["calls"] == 2
        expect(page.get_by_text("Chưa có tài liệu", exact=False).last).to_be_visible()
        assert page.evaluate("!JSON.stringify(localStorage).includes('fixture-valid-key')")
        assert page.evaluate("!JSON.stringify(sessionStorage).includes('fixture-valid-key')")
        assert not forbidden and not errors, (forbidden, errors)
        browser.close()
    return {
        "viewport": viewport,
        "syntheticChatCalls": 2,
        "realInference": 0,
        "generatedExams": 0,
        "draftPreserved": True,
    }


def main():
    results = []
    for viewport in ({"width": 1440, "height": 1000}, {"width": 390, "height": 844}):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        with tempfile.TemporaryDirectory(prefix="astra-local-connection-") as directory:
            environment = {
                name: value
                for name, value in os.environ.items()
                if not name.startswith(("EXAM_", "ASTRA_"))
            }
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "scripts.local_connection_smoke",
                    "--serve",
                    str(port),
                    directory,
                ],
                cwd=ROOT,
                env=environment,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            base = f"http://127.0.0.1:{port}"
            try:
                with httpx.Client(trust_env=False) as client:
                    for _ in range(100):
                        try:
                            client.get(base + "/api/connection", timeout=0.3).raise_for_status()
                            break
                        except httpx.TransportError:
                            time.sleep(0.1)
                    else:
                        raise TimeoutError("Synthetic server did not start")
                results.append(observe(base, directory, viewport))
            finally:
                stop_fixture_server(process)
    print(json.dumps({"evidence": "MOUNTED_LOCAL_CONNECTION_SYNTHETIC_FIXTURES", "cases": results}))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--serve"]:
        serve(int(sys.argv[2]), sys.argv[3])
    else:
        main()
