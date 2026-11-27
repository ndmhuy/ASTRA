"""Real upload UI + HTTP + replay agents. No paid model, approval or export.

Run after npm run build: python scripts/input_documents_smoke.py
Artifacts: runs/input-documents-smoke/ (synthetic inputs, screenshots and private jobs).
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUTPUT = ROOT / "runs" / "input-documents-smoke"
URL = "http://127.0.0.1:8017"


def create_smoke_app():
    from exam_baseline.api.app import create_app
    from exam_baseline.config import Settings
    from tests.api.test_ui_jobs import retrieval
    from tests.thpt.test_generation import Scripted

    providers = {
        role: Scripted(role, False) for role in ("composer", "illustrator", "solver", "reviewer")
    }
    return create_app(
        Settings.for_offline(),
        ui_output_root=OUTPUT / "jobs",
        pipeline_providers=providers,
        rag_retriever=retrieval,
        workspace_dir=ROOT / "astra-frontend" / "dist",
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sample = OUTPUT / "sample.txt"
    matrix = OUTPUT / "matrix.csv"
    invalid = OUTPUT / "broken.pdf"
    sample.write_text("SYNTHETIC_SAMPLE: original quadratic function exercise.", encoding="utf-8")
    matrix.write_text("topic,level\nSYNTHETIC_MATRIX,TH", encoding="utf-8")
    invalid.write_bytes(b"not a PDF")
    with (OUTPUT / "server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "scripts.input_documents_smoke:create_smoke_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "8017",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError("Smoke server exited; see server.log")
                try:
                    if httpx.get(URL + "/api/health", timeout=1).is_success:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.1)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="chrome", headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                generated = []
                page.on(
                    "request",
                    lambda request: (
                        generated.append(request.post_data_json)
                        if "/api/exams/generate" in request.url and request.method == "POST"
                        else None
                    ),
                )
                page.goto(URL)
                page.get_by_role("button", name="Soạn từ mẫu", exact=True).click()
                modal = page.get_by_role("dialog")
                picker = modal.get_by_label("Chọn tài liệu đầu vào")
                expect(picker).to_be_enabled()
                modal.get_by_label("Loại tài liệu tải lên").select_option("sample_exam")
                picker.set_input_files(str(sample))
                expect(modal.get_by_text("Đề mẫu · sample.txt", exact=False)).to_be_visible()
                modal.get_by_label("Loại tài liệu tải lên").select_option("matrix")
                picker.set_input_files(str(matrix))
                expect(modal.get_by_text("Ma trận · matrix.csv", exact=False)).to_be_visible()
                modal.locator("summary").filter(has_text="matrix.csv").click()
                expect(modal.get_by_text("topic,level", exact=False)).to_be_visible()
                picker.set_input_files(str(invalid))
                expect(modal.get_by_role("alert")).to_contain_text("Không đọc được tài liệu")
                expect(modal.get_by_text("Đề mẫu · sample.txt", exact=False)).to_be_visible()
                page.screenshot(path=str(OUTPUT / "upload-desktop.png"), full_page=True)
                modal.get_by_role("button", name="Bỏ đính kèm sample.txt").click()
                expect(modal.get_by_text("Đề mẫu · sample.txt", exact=False)).to_have_count(0)
                modal.get_by_role("button", name="Tạo đề thi", exact=True).click()
                page.wait_for_function(
                    "() => document.body.textContent.includes('Đề đã sẵn sàng') || "
                    "document.querySelectorAll('.question-card').length > 0",
                    timeout=30000,
                )
                assert generated and len(generated[-1]["uploadedFiles"]) == 1
                document_id = generated[-1]["uploadedFiles"][0]
                page.reload()
                page.get_by_role("button", name=re.compile("Đề thi Toán Học 22 câu")).first.click()
                expect(page.get_by_text("Ma trận · matrix.csv", exact=False)).to_be_visible(
                    timeout=15000
                )
                page.screenshot(path=str(OUTPUT / "workspace-desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                page.screenshot(path=str(OUTPUT / "workspace-mobile.png"), full_page=True)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                # Also cover the landing chat attachment path and partial subject intake.
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.get_by_role("button", name="Tạo đề mới", exact=True).click()
                chat_picker = page.get_by_label("Chọn tài liệu đầu vào")
                expect(chat_picker).to_be_enabled()
                chat_picker.set_input_files([str(sample), str(matrix)])
                expect(page.get_by_text("Tài liệu thêm · matrix.csv", exact=False)).to_be_visible()
                page.get_by_role("textbox", name="Yêu cầu soạn đề").fill("Toán THPT")
                page.get_by_role("button", name="Gửi yêu cầu").click()
                chat_modal = page.get_by_role("dialog")
                expect(
                    chat_modal.get_by_text("Tài liệu thêm · matrix.csv", exact=False)
                ).to_be_visible()
                chat_modal.get_by_role("button", name="Tạo đề thi", exact=True).click()
                page.wait_for_function(
                    "() => document.querySelectorAll('.question-card').length > 0", timeout=30000
                )
                assert len(generated) == 2 and len(generated[-1]["uploadedFiles"]) == 2
                assert document_id not in generated[-1]["uploadedFiles"]
                page.screenshot(path=str(OUTPUT / "chat-upload-desktop.png"), full_page=True)
                browser.close()
                print(
                    json.dumps(
                        {
                            "status": "passed",
                            "document_id": document_id,
                            "generation_requests": len(generated),
                            "screenshots": str(OUTPUT),
                            "mode": "synthetic retrieval and replay model responses",
                        },
                        indent=2,
                    )
                )
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    main()
