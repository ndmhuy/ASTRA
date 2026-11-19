# Zero-inference acceptance

From `D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first`:

1. Start Vite in one PowerShell: `npm --prefix astra-frontend run dev -- --host 127.0.0.1 --port 5173`.
2. Run `node astra-frontend/tests/browserActions.mjs` in another shell. This opens isolated headless Chrome, seeds synthetic local state, and intercepts Agent/business requests. Expected JSON reports answers/focus/editor/disclosure/cancel/unsupported/staleAbort passed, two setup receipts, liveCalls=0.
3. Run frontend tests and `python -m pytest tests/test_agent_ui_service.py -q` via `.venv-agent-ui`. These check target/source/negation/size/rate boundaries with fixtures.

For manual interactive viewing only, open http://127.0.0.1:5173. Do not send chat in the real configured Gemini mode during this zero-cost task. Do not click generation, regenerate or apply note.

To manually test deterministic demo chat without altering ignored configuration, launch a separate Agent shell with `$env:AGENT_MODE='offline'`, then `.\.venv-agent-ui\Scripts\python.exe -m uvicorn astra_agent_ui.app:app --host 127.0.0.1 --port 8010`. Ensure the port is free first. Offline is explicitly labelled and supports only its documented deterministic subset; this does not prove live Gemini interpretation. Close that process/shell afterward; do not overwrite `.env.local`.

The automatic browser fixture is the preferred no-cost check for the eight-turn flow. No generation is required to inspect answers/editor state in the isolated fixture workspace; real application empty workspaces correctly require an actual completed exam.
