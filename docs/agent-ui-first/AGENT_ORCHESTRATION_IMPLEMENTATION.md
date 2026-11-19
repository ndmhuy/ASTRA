# UI action orchestration implementation

React owns application state and all business services. Gemini receives compact state and registry-owned argument contracts, and returns up to four typed proposals. The existing task controller validates/executes each step, captures fresh context after observed receipts and persists the resulting task in the workspace store.

Added adapters cover editor fill/save/regenerate/close, preview retry, approval, export, local workspace deletion, chat draft/branch/retract and task cancellation. Existing setup, generation and note handlers are retained. No Backend business code changed.

Consequential actions use `ui.action.prepare`: React stores exact capability/params, workspace, revision and content hash. Model-provided confirmation IDs are stripped. Only a new explicit teacher confirmation attaches the pending ID. A visible floating confirmation control remains accessible over dialogs; cancellation clears it. Existing Backend preview/revision/artifact gates still run.

Development console emits `[ASTRA action turn]` with turn/action/capability IDs, receipt statuses, error codes, observed versions and final task outcome. It omits teacher text, credentials and business payloads.

The provider receives explicit mappings for answer view (`review`), paper and PDF, actual session IDs, exam revision and availability hints. Execution remains default-deny with authoritative React validation. Missing prerequisite differs from an absent product operation.

Bounds: maximum four actions per turn, duplicate receipt cache, loop detection, stop on partial failure, fresh interpretation context and cross-workspace observation checks. Automatic model replanning is not implemented; failed tasks require a new teacher turn. The existing replan constant is not evidence of an implemented replan loop.

Run from the repository root:

```powershell
.\.venv-agent-ui\Scripts\python.exe -m uvicorn astra_agent_ui.app:app --host 127.0.0.1 --port 8010
.\.venv-agent-ui\Scripts\python.exe -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000
npm --prefix astra-frontend run dev -- --host 127.0.0.1 --port 5173
```

Use separate shells, then open http://127.0.0.1:5173. Local Gemini configuration is preserved. Sending chat in Gemini mode invokes the model; the acceptance script intercepts that boundary and incurs no inference.
