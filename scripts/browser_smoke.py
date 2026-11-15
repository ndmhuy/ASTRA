"""Optional UI check: python scripts/browser_smoke.py [--screenshots DIRECTORY].

Requires the separately installed Playwright test library and Chrome.
The application itself has no external dependencies.
"""

import argparse
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_workflow.app import create_server
from rag_workflow.existing_corpus import load_existing_corpus
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--existing-corpus", action="store_true")
    args = parser.parse_args()
    if args.existing_corpus:
        documents, info = load_existing_corpus()
        server = create_server(0, documents, info)
    else:
        server = create_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1050})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_port}")
            page.locator(".result-card").first.wait_for()
            if args.existing_corpus:
                assert page.locator("#count").inner_text() == str(len(documents))
                page.locator("#collection-kind").select_option("exam")
                page.wait_for_function(
                    "document.querySelector('#timing').textContent.startsWith('5 results')"
                )
                assert "ocr-draft" in page.locator(".card-top").first.inner_text()
                assert "Câu " in page.locator(".card-top").first.inner_text()
                page.get_by_role("button", name="Read full document").first.click()
                page.locator("#document-dialog").wait_for(state="visible")
                assert "Grade mapping unknown" in page.locator("#doc-meta").inner_text()
                page.get_by_role("button", name="Close source document").click()
                page.locator("#query").fill("tìm tài liệu về")
                page.locator("#search-button").click()
                page.get_by_text("No documents retrieved", exact=True).wait_for()
                assert page.locator(".result-card").count() == 0
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                assert not errors, errors
                browser.close()
                print(
                    "PASS: existing corpus counts, unified & exam search, source provenance, gap and mobile layout; no JavaScript errors."
                )
                return
            assert page.locator(".result-card").count() == 2
            assert not page.locator("#collection-kind").is_visible()
            assert "Demo note" in page.locator(".card-top").first.inner_text()
            for selector in ("h1", ".result-card h3", ".result-card p"):
                font = page.locator(selector).first.evaluate("e => getComputedStyle(e).fontFamily")
                assert "Segoe UI" in font and "Georgia" not in font
            assert "Định luật Ohm và điện trở" in page.locator(".result-card h3").first.inner_text()
            page.locator("#compare-button").click()
            page.locator(".compare-col").first.wait_for()
            assert page.locator(".compare-col").count() == 3
            page.locator("#eval-panel summary").click()
            page.locator("#run-eval").click()
            page.locator("#eval-summary .eval-table").wait_for()
            assert "HYBRID" in page.locator("#eval-summary").inner_text()
            page.locator("#search-button").click()
            page.locator(".result-card").first.wait_for()
            if args.screenshots:
                args.screenshots.mkdir(parents=True, exist_ok=True)
                page.screenshot(
                    path=str(args.screenshots / "astra-rag-desktop.png"), full_page=True
                )
            page.get_by_role("button", name="Read full document").first.click()
            page.locator("#document-dialog").wait_for(state="visible")
            assert "I = U/R" in page.locator("#doc-text").inner_text()
            page.get_by_role("button", name="Close source document").click()
            page.locator(".examples button").nth(1).click()
            page.get_by_role("heading", name="Cấp số cộng", exact=True).wait_for()
            page.locator("#query").fill("Physics grade 11 chapter 9")
            page.locator("#search-button").click()
            page.get_by_text("No documents retrieved", exact=True).wait_for()
            assert page.locator(".result-card").count() == 0
            page.get_by_role("button", name="Add a document").click()
            page.locator("#import-title").fill("My vector note")
            page.locator("#import-subject").select_option("toan")
            page.locator("#import-grade").select_option("10")
            page.locator("#import-chapter").fill("7")
            page.locator("#import-content").fill(
                "Original vector note. <script>window.bad = true</script>"
            )
            page.locator("#permission").check()
            page.get_by_role("button", name="Add to collection").click()
            page.get_by_text("Document added", exact=True).wait_for()
            page.locator("#query").fill("vector note")
            page.locator("#search-button").click()
            page.get_by_role("heading", name="My vector note", exact=True).wait_for()
            assert page.locator(".result-card").count() == 1
            assert page.evaluate("window.bad === undefined")
            page.set_viewport_size({"width": 390, "height": 844})
            page.locator(".examples button").first.click()
            page.get_by_role("heading", name="Chu kì và tần số dao động").wait_for()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / "astra-rag-mobile.png"), full_page=True)
            assert not errors, errors
            browser.close()
            print(
                "PASS: search, source dialog, examples, empty state, import, safe text rendering and mobile layout; no JavaScript errors."
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
