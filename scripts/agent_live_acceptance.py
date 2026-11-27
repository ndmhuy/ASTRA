"""One deliberately selected REAL browser turn. No routes, fixtures or retries.

Run only under a separately authorized, server-enforced live budget. Synthetic
teacher messages and observed predictions are saved separately from oracle data.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/live-chat"
HEALTH = "https://astra-ai-proxy.letranhoanglong2227.workers.dev/health"
CASES = {
    "intake": (
        "Cô đang muốn chuẩn bị một bài thi thử tốt nghiệp cho học sinh, em giúp cô bắt đầu với.",
        "PREPARE_EXAM",
        {"family": "thpt"},
        "Ask subject; no modal or generation",
    ),
    "subject": (
        "Môn Toán nhé.",
        "local contextual subject",
        {"family": "thpt", "subject": "math"},
        "Select THPT Mathematics and open existing setup; zero inference",
    ),
    "recall": (
        "Nhắc lại giúp cô môn và kỳ thi mình vừa thống nhất lúc nãy với.",
        "RECALL_REQUIREMENTS",
        {},
        "Recall THPT Mathematics from stored state; no mutation",
    ),
    "unsupported": (
        "Cô đổi ý rồi, thay Toán bằng môn Hóa cho kỳ thi tốt nghiệp này được chứ?",
        "PREPARE_EXAM",
        {"family": "thpt", "subject": "chemistry"},
        "Truthfully unsupported; no substitution or generation",
    ),
    "switch": (
        "Bỏ hướng tốt nghiệp vừa rồi, cô muốn chuyển sang bài đánh giá năng lực "
        "của ĐHQG TP.HCM; khoan tạo đề nhé.",
        "PREPARE_EXAM",
        {"family": "vact"},
        "Switch to V-ACT setup, clear obsolete THPT subject; no generation",
    ),
    "information": (
        "Nếu cô muốn tải bản Word thì cần thao tác thế nào, cô chỉ đang hỏi cách làm thôi.",
        "APPLICATION_GUIDANCE",
        {},
        "Explain operation/preconditions; no export, navigation or generation",
    ),
    "navigation": (
        "Đưa cô trở lại màn hình bắt đầu để cô xem lại các lựa chọn nhé.",
        "RETURN_HOME",
        {},
        "Actual supported home navigation with receipt; no generation",
    ),
    "outside": (
        "Tối nay cô nên nấu món gì với nấm và đậu phụ?",
        "OUT_OF_SCOPE",
        {},
        "No forced exam workflow or mutation",
    ),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--result-suffix", default="")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    message, goal, slots, outcome = CASES[args.case]
    target = OUT / f"{args.case}{args.result_suffix}.json"
    if target.exists():
        raise SystemExit("Result exists: inspect it; never blindly repeat a live turn.")
    before = httpx.get(HEALTH, timeout=15).json()
    if before["quota"]["diagnostic"]["used"] >= 8 and args.case != "subject":
        raise SystemExit("Automation allowance exhausted")
    result = {
        "case": args.case,
        "message": message,
        "expected": {
            "goal": goal,
            "slots": slots,
            "outcome": outcome,
            "prohibited": "generation, approval, export; unrequested mutation",
        },
        "healthBefore": before,
        "responses": [],
        "businessWrites": [],
    }
    # Expectations exist on disk before any model request.
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    state = OUT / "browser-state.json"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge")
        context = browser.new_context(
            storage_state=str(state) if state.exists() else None,
            reduced_motion="reduce",
            viewport={"width": 1440, "height": 1000},
        )
        page = context.new_page()

        def record_request(request):
            if request.method != "GET" and "/api/" in request.url:
                result["businessWrites"].append({"method": request.method, "url": request.url})

        def record_response(response):
            if response.url.endswith("/agent/turn"):
                result["responses"].append({"status": response.status, "body": response.json()})

        page.on("request", record_request)
        page.on("response", record_response)
        page.goto(args.base_url)
        if args.case != "intake":
            original = json.loads((OUT / "intake.json").read_text(encoding="utf-8"))["storedState"][
                0
            ]["id"]
            saved = page.evaluate("() => JSON.parse(localStorage.getItem('astra.sessions.v1'))")
            title = next(item["title"] for item in saved if item["id"] == original)
            page.locator("button.sidebar-exam").filter(
                has=page.locator(".sidebar-exam-title", has_text=title)
            ).click()
        composer = page.locator("textarea.composer-textarea").first
        composer.wait_for(timeout=15000)
        composer.fill(message)
        started = time.perf_counter()
        composer.press("Enter")
        result["immediatePending"] = (
            page.get_by_role("status").filter(has_text="Đang đọc yêu cầu").count() > 0
        )
        page.wait_for_function(
            "() => {const t=document.querySelector('textarea.composer-textarea'); "
            "return t && !t.disabled && !t.value}",
            timeout=45000,
        )
        page.wait_for_timeout(100)
        result["visibleElapsedMs"] = round((time.perf_counter() - started) * 1000)
        result["assistant"] = page.locator(".chat-message-row.is-assistant").all_inner_texts()
        result["dialogs"] = page.get_by_role("dialog").all_inner_texts()
        result["uiText"] = page.locator("body").inner_text()
        result["storedState"] = page.evaluate(
            "() => JSON.parse(localStorage.getItem('astra.sessions.v1'))"
        )
        page.screenshot(path=str(OUT / f"{args.case}.png"), full_page=True)
        # Escape preserves the actual modal safety contract and permits the next turn.
        if result["dialogs"]:
            page.keyboard.press("Escape")
        context.storage_state(path=str(state))
        browser.close()
    result["healthAfter"] = httpx.get(HEALTH, timeout=15).json()
    result["remoteAttempts"] = (
        result["healthAfter"]["quota"]["diagnostic"]["used"] - before["quota"]["diagnostic"]["used"]
    )
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "case",
                    "visibleElapsedMs",
                    "immediatePending",
                    "responses",
                    "assistant",
                    "dialogs",
                    "businessWrites",
                    "remoteAttempts",
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
