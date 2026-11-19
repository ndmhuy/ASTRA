# End-to-end UI acceptance

2026-11-19, real headless Chrome + Vite React application. Interpretation HTTP and Backend responses are fixture-controlled. No Gemini call or generation job was run.

Observed browser trace (`astra-frontend/tests/browserActions.mjs`):

1. Restore a synthetic completed workspace in isolated browser LocalStorage and select it using the real sidebar.
2. Submit “Tôi muốn xem đáp án” in the real composer. HTTP fixture returns `ui.exam.view_mode {mode:review}`. React changes the pressed tab and displays the answer label.
3. Submit “Quay lại đề”. React returns to paper mode.
4. Submit “Cho xem đáp án câu này”. Review then focus execute; answer remains visible, question focus class appears, task completes with two successful receipts.
5. Submit the setup intake instruction. Open-setup waits for the actual modal catalog request, configure selects the supported format and instruction draft. Two receipts succeed; task ends `awaiting_confirmation`. No generate request occurs.

Result: **PASS**. Four input turns, real React handlers, observed visible state, persisted receipts, zero page exceptions, zero inference calls.

Commands:

```powershell
npm install --prefix tmp/browser-tooling playwright-core --no-audit --no-fund --ignore-scripts
node astra-frontend/tests/browserActions.mjs
npm --prefix astra-frontend test
npm --prefix astra-frontend run lint
npm --prefix astra-frontend run build
.\.venv-agent-ui\Scripts\python.exe -m pytest tests/test_agent_ui_service.py -q
```

Focused frontend tests: 22 passed. Agent tests: 37 passed. Build/lint and Ruff passed. Browser tooling lives in ignored tmp. Python Playwright installation stalled and was stopped; the smaller Node playwright-core installation succeeded and used installed Chrome.

Limits: new confirmation-bound save/approval/export/delete adapters are built and preconditions tested, but all have not been exercised in Chrome. No live paraphrase accuracy is claimed for this change; live Gemini must be evaluated separately if desired. Tests prove dispatch/React behavior rather than treating a successful model HTTP response as execution.
