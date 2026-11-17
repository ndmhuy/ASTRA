# Connected THPT UI

The integration branch combines `main` (`f6b7ea8`) with `uiux2` (`7897b79`).
The first supported engine is **Toán THPT**, using the original locked template:
12 MCQ, 4 true/false questions with four statements each, and 6 short answers.
VACT, other subjects, uploads and the M2 chatbot controller are not enabled by this adapter.
The detailed setup still opens a custom workspace directly; free text becomes Composer requirements.

## Run locally

Run from the repository root in PowerShell. Keep your existing `.env` and model key private.

```powershell
.\.venv-win\Scripts\python.exe -m pip install -e ".[dev]" -c requirements-tested.txt
git fetch --no-tags origin 8b8fb7b09182b3d9d1eee0b95818027f52ab004d
.\.venv-win\Scripts\python.exe -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd astra-frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

Open the URL Vite prints. Its `/api` proxy forwards to the backend on port 8000.
The frontend defaults to API mode. `.env.example` documents `VITE_SERVICE_MODE=api`
and `VITE_API_BASE_URL=/api`; no model key belongs in any `VITE_*` variable.
`ASTRA_API_PROXY_TARGET` can select another backend for local testing.

Backend settings:

- Existing `EXAM_PROVIDER=chat_completions`, model, key and compatible endpoint configure inference.
- `EXAM_UI_OUTPUT_ROOT=runs/ui` stores SQLite receipts and per-job artifacts.
- `EXAM_RAG_CORPUS_REF` defaults to the pinned commit above.
- `EXAM_RAG_PACK_DIR` optionally selects a portable pack exported by `rag_workflow.profile_pack`.

No corpus history is merged into application code. The release loader verifies its manifest/hashes.
Use one backend worker. This local job runner is not a distributed queue.

## Teacher workflow

1. Choose **Soạn từ mẫu**, or open **Soạn chi tiết** and then choose its generation setup.
2. The backend catalog supplies the authoritative 22-question, 90-minute format.
3. Start generation. Progress reports real RAG/Composer/Illustrator/Solver/Reviewer stages.
4. Inspect all three question types, source warnings and proposed answers.
5. Click **Đã kiểm tra, phê duyệt bản này** to approve the exact revision/content hash.
6. Download the student `.tex` or separate teacher answer `.json`.
7. Editing or regenerating a question preserves its stable ID and invalidates approval.

Native TikZ source remains editable in the exam. The browser exposes its source rather than
pretending to render TikZ. Compile `.tex` with XeLaTeX/LuaLaTeX to inspect the final figures.
PDF/DOCX export from this locked-template path is not implemented; the UI does not offer it.
The older generic exporter and CLI flows are unchanged.

## Backend contract

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Service and provider configuration status, without credentials |
| `GET /api/exam-formats` | Versioned format catalog and capabilities |
| `POST /api/exam-formats/evaluate` | Validate scope and return the resolved THPT/RAG matrices |
| `POST /api/exams/generate` | Start or recover a job using a required `Idempotency-Key` header |
| `GET /api/exams/{jobId}/status` | Recoverable progress, terminal state and structured errors |
| `GET /api/exams/{jobId}/events` | SSE current snapshots; reconnecting receives current state |
| `GET /api/exams/{jobId}` | Structured questions, revision/hash, source warnings and provenance |
| `PUT /api/exams/{jobId}/questions/{id}` | Validated edit with expected exam revision |
| `POST /api/exams/{jobId}/questions/{id}/regenerate` | Targeted Composer repair, illustration and independent Solver check |
| `POST /api/exams/{jobId}/approve` | Human approval bound to revision and content hash |
| `GET /api/exams/{jobId}/export?type=STUDENT_EXAM&format=tex` | Reviewed student LaTeX |
| `GET /api/exams/{jobId}/export?type=TEACHER_KEY&format=json` | Reviewed teacher answers |

See `/docs` for exact request schemas. A passing-scope request is in
`examples/ui/thpt_request.json`. Stable IDs are `P1-1..12`, `P2-1..4`, `P3-1..6`;
the UI's numeric ID is only a per-job display/edit address.

Missing/unsupported scope is HTTP 422. Reusing an idempotency key for different input,
stale edits/approval, changed artifacts or an unapproved export is HTTP 409.
Generation failures remain inspectable through the job status and private report.
After a server restart, interrupted jobs become explicit failures; they are not silently
regenerated. Completed jobs/approvals persist. Browser workspaces/job IDs survive reload
in local storage; deleting a workspace removes its local state, not the server artifact.

## RAG and agent boundaries

`ui/jobs.py` resolves the matrix, calls the pinned RAG release, then passes the rich
`mas_intake_rag` handoff through `intake.encode_thpt_retrieval` into the native THPT engine.
The adapter keeps the original RAG metadata, grade prerequisites, warnings and gaps.
It binds every returned question ID exactly once and groups full evidence by part.
Composer receives only its own section's evidence. Solver receives student content and
drawings, never reference answers, RAG text or Composer keys.

The catalog explicitly selects `fallback_with_warning` for RAG's three-level NB/TH/VD
scheme. A VDC request stays VDC in MAS; RAG's fallback warning remains visible.
Retrieval gaps stop generation. Research corpus data is not marked teacher-approved.
Reviewer runs once during initial generation. User-requested regeneration does not run
a second Reviewer, and always returns to human review.

## Checks

```powershell
.\.venv-win\Scripts\python.exe -m pytest -q
.\.venv-win\Scripts\python.exe -m ruff check src tests scripts/ui_browser_smoke.py
.\.venv-win\Scripts\python.exe -m rag_workflow.eval --acceptance --corpus-ref 8b8fb7b09182b3d9d1eee0b95818027f52ab004d --out runs/ui-rag-acceptance.json
cd astra-frontend
npm.cmd test
npm.cmd run lint
npm.cmd run build
```

For the browser check, install `requirements-browser.txt` and Chrome, then run from the root:

```powershell
.\.venv-win\Scripts\python.exe scripts/ui_browser_smoke.py
```

This uses real pinned RAG and native agents with **explicit replay model responses**.
It checks teacher approval, student export, editing and local workspace restoration.
It does not measure model accuracy. Add `--live` only to use the configured external model.
Live mode sends retrieved context to that provider and stops at pending human review;
it does not automate approval or export of the generated exam.
Screenshots, logs and receipts stay under ignored `runs/ui-smoke/`.
