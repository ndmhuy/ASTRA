"""Run the built ASTRA app over local HTTP with a semantic provider fixture."""

import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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
        browser.close()
    print("Mounted React: greeting and same-origin fixture navigation observed; no exam writes.")


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
