"""Exercise the integrated teacher workflow against real HTTP servers.

Default: real pinned RAG and native THPT agents with explicit replay model providers.
--live: use the configured external model instead. No model key enters the browser.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def create_smoke_app():
    from exam_baseline.api.app import create_app
    from exam_baseline.config import Settings

    if os.environ.get("ASTRA_UI_SMOKE_LIVE") == "1":
        return create_app(ui_output_root=Path(os.environ["ASTRA_UI_SMOKE_ROOT"]))
    from exam_baseline.core.contracts import Completion
    from scripts.ui_pdf_smoke import TIKZ
    from tests.thpt.test_generation import Scripted

    providers = {
        role: Scripted(role, False) for role in ("composer", "illustrator", "solver", "reviewer")
    }
    compose = providers["composer"].complete

    async def compose_with_graph(prompt):
        completion = await compose(prompt)
        data = json.loads(completion.text)
        if json.loads(prompt.user)["part"] == "P1":
            data["questions"][2].update(
                stem="Cho đồ thị như hình vẽ. Hàm số nào được biểu diễn?",
                illustration_request="Draw y=x^2 with labeled x/y axes.",
                choices={"A": "$y=x^2$", "B": "$y=x$", "C": "$y=-x$", "D": "$y=-x^2$"},
                answer="A",
            )
        return Completion(text=json.dumps(data), model=completion.model)

    async def illustrate_graph(prompt):
        providers["illustrator"].calls.append(json.loads(prompt.user))
        return Completion(
            text=json.dumps({"drawings": [{"question_id": "P1-3", "latex": TIKZ}]}),
            model="offline-contract-fixture",
        )

    providers["composer"].complete = compose_with_graph
    providers["illustrator"].complete = illustrate_graph

    return create_app(
        Settings.for_offline(),
        ui_output_root=Path(os.environ["ASTRA_UI_SMOKE_ROOT"]),
        pipeline_providers=providers,
    )


def wait_server(url, process):
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError(f"Server exited before startup: {url}")
        try:
            if httpx.get(url, timeout=1).is_success:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise TimeoutError(url)


def main():
    from playwright.sync_api import expect, sync_playwright

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    output = ROOT / "runs" / "ui-smoke" / str(uuid4())
    output.mkdir(parents=True)
    env = {
        **os.environ,
        "ASTRA_UI_SMOKE_ROOT": str(output / "jobs"),
        "ASTRA_UI_SMOKE_LIVE": "1" if args.live else "0",
        "ASTRA_API_PROXY_TARGET": "http://127.0.0.1:8107",
        "VITE_SERVICE_MODE": "api",
    }
    no_window = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    processes = []
    try:
        with (
            (output / "api.log").open("w", encoding="utf-8") as api_log,
            (output / "ui.log").open("w", encoding="utf-8") as ui_log,
        ):
            api = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "scripts.ui_browser_smoke:create_smoke_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8107",
                ],
                cwd=ROOT,
                env=env,
                stdout=api_log,
                stderr=subprocess.STDOUT,
                creationflags=no_window,
            )
            processes.append(api)
            ui = subprocess.Popen(
                [
                    "node",
                    str(ROOT / "astra-frontend/node_modules/vite/bin/vite.js"),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "5179",
                    "--strictPort",
                ],
                cwd=ROOT / "astra-frontend",
                env=env,
                stdout=ui_log,
                stderr=subprocess.STDOUT,
                creationflags=no_window,
            )
            processes.append(ui)
            wait_server("http://127.0.0.1:8107/api/health", api)
            wait_server("http://127.0.0.1:5179", ui)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="chrome", headless=True)
                page = browser.new_page(
                    viewport={"width": 1440, "height": 1000}, reduced_motion="reduce"
                )
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto("http://127.0.0.1:5179")
                page.get_by_role("button", name="Soạn từ mẫu").wait_for()
                page.get_by_role("button", name="Soạn từ mẫu").click()
                expect(page.get_by_role("dialog")).to_contain_text("22 câu")
                expect(page.get_by_role("dialog")).to_contain_text("90 phút")
                page.get_by_role("button", name="Tạo đề thi", exact=True).click()
                approve = page.get_by_role("button", name="Đã kiểm tra, phê duyệt bản này")
                page.wait_for_function(
                    """() => [...document.querySelectorAll('button')].some(
                        button => button.textContent.includes('phê duyệt bản này'))
                        || !!document.querySelector('[role=alert]')""",
                    timeout=600000 if args.live else 30000,
                )
                if page.get_by_role("alert").count():
                    page.screenshot(path=str(output / "failed.png"), full_page=True)
                    print(
                        json.dumps(
                            {"status": "failed", "live_model": args.live, "output": str(output)}
                        )
                    )
                    raise RuntimeError(" / ".join(page.get_by_role("alert").all_text_contents()))
                expect(page.locator(".exam-question-card")).to_have_count(22)
                expect(page.get_by_role("button", name="Xuất LaTeX")).to_have_count(0)
                page.screenshot(path=str(output / "before-review.png"), full_page=True)
                if args.live:
                    browser.close()
                    print(
                        json.dumps(
                            {
                                "status": "passed",
                                "live_model": True,
                                "quality": "pending_human_review",
                                "output": str(output),
                            }
                        )
                    )
                    return
                # Approval now requires opening the current ready PDF in the UI.
                expect(approve).to_be_disabled()
                page.get_by_role("button", name="Xem trước PDF", exact=True).click()
                frame = page.locator('iframe[title="Student exam PDF preview"]')
                page.wait_for_function(
                    """() => document.querySelector('iframe[title="Student exam PDF preview"]')
                        || document.querySelector('.pdf-preview-error')""",
                    timeout=330000,
                )
                expect(frame).to_have_count(1)
                expect(approve).to_be_enabled()
                expect(page.locator(".pdf-preview-banner")).to_contain_text("human review required")
                first_pdf_url = urljoin(page.url, frame.get_attribute("src"))
                draft_pdf = httpx.get(first_pdf_url, timeout=30)
                assert draft_pdf.status_code == 200
                assert draft_pdf.headers["content-type"] == "application/pdf"
                (output / "draft.pdf").write_bytes(draft_pdf.content)
                # Chrome's native PDF plugin paints after the iframe/network load.
                page.wait_for_timeout(1500)
                page.screenshot(path=str(output / "pdf-before-review.png"), full_page=True)
                approve.click()
                with page.expect_download() as download:
                    page.get_by_role("button", name="Xuất PDF", exact=True).click()
                student_pdf = output / "student.pdf"
                download.value.save_as(student_pdf)
                assert student_pdf.read_bytes() == draft_pdf.content
                from pypdf import PdfReader

                pdf_reader = PdfReader(student_pdf)
                assert len(pdf_reader.pages) >= 1
                pdf_text = "\n".join(p.extract_text() for p in pdf_reader.pages)
                assert "KỲ THI TỐT NGHIỆP" in pdf_text
                assert "PRIVATE_BANK_KEY" not in pdf_text and "Cộng trực tiếp" not in pdf_text
                with page.expect_download() as download:
                    page.get_by_role("button", name="Xuất LaTeX").click()
                student_path = output / "student.tex"
                download.value.save_as(student_path)
                source = student_path.read_text("utf-8")
                assert source.count(r"\textbf{Câu ") == 22
                assert source.count(r"\begin{tikzpicture}") == 1
                assert "Cộng trực tiếp" not in source
                page.get_by_role("button", name="Xem đáp án", exact=True).click()
                page.locator(".question-review summary").first.click()
                page.get_by_role("button", name="Sửa câu hỏi", exact=True).first.click()
                dialog = page.get_by_role("dialog")
                dialog.get_by_label("Đề bài", exact=True).fill("Tính $1+1$ (giáo viên đã sửa).")
                dialog.get_by_role("button", name="Lưu thay đổi").click()
                expect(dialog).to_have_count(0)
                approve.wait_for()
                expect(page.get_by_role("button", name="Xuất LaTeX")).to_have_count(0)
                assert httpx.get(first_pdf_url, timeout=10).status_code == 409
                page.get_by_role("button", name="Xem trước PDF", exact=True).click()
                page.wait_for_function(
                    """() => document.querySelector('iframe[title="Student exam PDF preview"]')
                        || document.querySelector('.pdf-preview-error')""",
                    timeout=330000,
                )
                expect(frame).to_have_count(1)
                expect(approve).to_be_enabled()
                next_pdf_url = urljoin(page.url, frame.get_attribute("src"))
                assert next_pdf_url != first_pdf_url
                revised_pdf = httpx.get(next_pdf_url, timeout=30)
                assert revised_pdf.status_code == 200
                (output / "revised.pdf").write_bytes(revised_pdf.content)
                page.wait_for_timeout(1500)
                page.screenshot(path=str(output / "pdf-after-edit.png"), full_page=True)
                assert "giáo viên đã sửa" in "\n".join(
                    p.extract_text() for p in PdfReader(output / "revised.pdf").pages
                )
                page.reload()
                page.get_by_role("button", name="Soạn từ mẫu").wait_for()
                # Reload restores the workspace in the sidebar without another start call.
                assert (
                    page.evaluate("JSON.parse(localStorage.getItem('astra.sessions.v1')).length")
                    == 1
                )
                assert not errors, errors
                page.screenshot(path=str(output / "restored.png"), full_page=True)
                browser.close()
            receipt = {
                "status": "passed",
                "live_model": args.live,
                "rag": "real pinned release",
                "pdf": "real local TeX",
                "graph": "native TikZ",
                "pages": len(pdf_reader.pages),
                "old_preview_after_edit": 409,
                "output": str(output),
            }
            (output / "receipt.json").write_text(json.dumps(receipt, indent=2), "utf-8")
            print(json.dumps(receipt))
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    main()
