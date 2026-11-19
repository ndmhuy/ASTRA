# ASTRA Agent + UI/UX + Backend Teammate Handoff

Date: 2026-11-19 (Asia/Bangkok)

This handoff packages the existing integrated ASTRA feature branch. It does not claim that live Gemini interpretation or a real Backend generation job has succeeded.

## A. Git information

| Item | Value |
|---|---|
| Repository | `https://github.com/ndmhuy/ASTRA.git` |
| Feature branch | `feat/agent-ui-first-merge` |
| Agent implementation SHA before this handoff commit | `e903f232ab6e7ee0124352508e8fd1210f847151` |
| Merged UI/UX + Backend baseline | `8f12fbb2e9c7b6adb43b20b1966b256da6f45586` |
| Branch relationship at packaging | baseline is an ancestor; feature was 7 commits ahead and 0 behind before the handoff commit |

The remote feature-branch tip is authoritative for the packaging commit itself. After checkout, record its full SHA with `git rev-parse HEAD`.

Fresh checkout:

```powershell
git clone https://github.com/ndmhuy/ASTRA.git
Set-Location ASTRA
git fetch origin feat/agent-ui-first-merge
git switch --track -c feat/agent-ui-first-merge origin/feat/agent-ui-first-merge
git rev-parse HEAD
```

Existing clone:

```powershell
git fetch origin
git switch feat/agent-ui-first-merge
git pull --ff-only
git rev-parse HEAD
```

Verify that the merged Backend/UI baseline is included and the three components are present:

```powershell
git merge-base --is-ancestor 8f12fbb2e9c7b6adb43b20b1966b256da6f45586 HEAD
if ($LASTEXITCODE -ne 0) { throw 'Merged baseline is not an ancestor' }

Test-Path astra-frontend/src/App.tsx
Test-Path astra-frontend/src/agent/executor.ts
Test-Path src/astra_agent_ui/app.py
Test-Path src/exam_baseline/ui/jobs.py
Test-Path src/exam_baseline/pipeline/orchestrator.py
```

Do not rebase or force-push this shared branch. Bring later teammate work together through an ordinary merge and review conflicts file by file.

## B. Environment setup

### Prerequisites

- Git for Windows.
- Python 3.10 or newer.
- Node.js and npm compatible with the committed frontend lock file.
- Optional local LaTeX compiler for PDF previews; source generation and API health do not require installing one immediately.
- A Gemini API key belonging to the individual teammate's own project. Verify model access and quota in that project before live inference.

Install dependencies from the repository root:

```powershell
py -m venv .venv-agent-ui
.\.venv-agent-ui\Scripts\python.exe -m pip install --upgrade pip
.\.venv-agent-ui\Scripts\python.exe -m pip install -e ".[agent,dev]"

Set-Location astra-frontend
npm ci
Set-Location ..
```

### Private local configuration

Create the two ignored files from the sanitized templates:

```powershell
Copy-Item .env.example .env
Copy-Item agent-service\.env.example agent-service\.env.local
```

The files are intentionally separate:

- Backend: `<repository>\.env`
- Agent: `<repository>\agent-service\.env.local`

Never put either key in React, a `VITE_*` variable, Git, screenshots, issue text, chat logs, or handoff archives.

Agent variables consumed by `src/astra_agent_ui/config.py`:

```dotenv
AGENT_HOST=127.0.0.1
AGENT_PORT=8010
AGENT_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
AGENT_MODE=gemini
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_API_KEY=<YOUR_OWN_GEMINI_KEY>
```

Backend variables consumed by `src/exam_baseline/config.py`:

```dotenv
EXAM_PROVIDER=chat_completions
EXAM_MODEL=gemini-3.1-flash-lite
EXAM_API_KEY=<YOUR_OWN_GEMINI_KEY>
EXAM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
EXAM_TIMEOUT_SECONDS=90
EXAM_MAX_OUTPUT_TOKENS=8192
EXAM_TOKEN_LIMIT_FIELD=max_tokens
EXAM_RESPONSE_FORMAT=json_schema
EXAM_SCHEMA_AS_TOOL=false
EXAM_STRUCTURED_OUTPUT_STRICT=false
```

The Agent and Backend may use keys from the same developer project, but each service loads its credential independently. Neither shares credentials through frontend state. Process environment variables override local-file values.

Before committing anything, verify the private files remain ignored and untracked:

```powershell
git check-ignore -v .env agent-service/.env.local
git ls-files --error-unmatch .env 2>$null
git ls-files --error-unmatch agent-service/.env.local 2>$null
```

Both `git ls-files --error-unmatch` commands must fail because the files must not be tracked.

## C. Starting ASTRA

Run each service in a separate PowerShell window from the same checkout.

### Backend MAS — port 8000

```powershell
Set-Location '<repository>'
.\.venv-agent-ui\Scripts\python.exe -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000
```

### Conversational Agent — port 8010

```powershell
Set-Location '<repository>'
.\.venv-agent-ui\Scripts\python.exe -m uvicorn astra_agent_ui.app:app --host 127.0.0.1 --port 8010
```

### React UI — port 5173

```powershell
Set-Location '<repository>\astra-frontend'
$env:VITE_SERVICE_MODE = 'api'
$env:ASTRA_API_PROXY_TARGET = 'http://127.0.0.1:8000'
$env:ASTRA_AGENT_PROXY_TARGET = 'http://127.0.0.1:8010'
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173/`.

Cost-free health checks do not prove that a model was called:

```powershell
Invoke-RestMethod http://127.0.0.1:5173/api/health
Invoke-RestMethod http://127.0.0.1:5173/agent/health
```

## D. Architecture

```text
Teacher
  -> React UI chat
  -> Agent session + Gemini interpretation
  <- typed answer or UI action proposal
  -> React capability/context validation
  -> React UI action executor
  -> existing App / ExamSessions handlers
  <- observed execution receipt

Teacher-confirmed React workflow
  -> existing ApiExamService
  -> Backend JobManager
  -> existing RAG + Composer + Illustrator + Solver + Reviewer pipeline
  <- job progress and result through existing APIs
```

The Agent does not call Backend business endpoints. It receives sanitized UI context and may propose only capabilities registered as callable and `available_real`. React remains the execution and authorization boundary. Generation remains behind the existing teacher-controlled setup dialog.

Key source locations:

- React Agent wiring: `astra-frontend/src/agent/` and `astra-frontend/src/App.tsx`
- UI session state and lifecycle: `astra-frontend/src/state/examSessions.ts`
- Existing Backend adapter: `astra-frontend/src/services/examService.ts`
- Agent service/provider: `src/astra_agent_ui/`
- Backend jobs: `src/exam_baseline/ui/jobs.py`
- Existing MAS agents/orchestration: `src/exam_baseline/pipeline/` and `src/exam_baseline/thpt/`
- Existing provider adapter: `src/exam_baseline/providers/chat_completions.py`
- Existing RAG workflow: `rag_workflow/` and Backend retrieval modules

## E. Current implementation status

| Area | Status | Evidence / limitation |
|---|---|---|
| Git integration | **VERIFIED** | Feature contains the merged baseline plus Agent/UI commits; no Backend rewrite. |
| Three local services | **VERIFIED** | React, Agent and Backend health/proxy connectivity was observed from one worktree. |
| React ↔ Agent | **VERIFIED OFFLINE/HTTP** | Session and interpretation endpoints, error envelopes and proxy work. |
| UI action validation/execution | **VERIFIED** | Default-deny registry, state-version checks, idempotency, observed receipts and prior browser setup flow. |
| React ↔ Backend | **VERIFIED CONNECTIVITY** | Real `ApiExamService`, health/catalog routes and existing job adapter are wired. |
| Agent Gemini schema conversion | **VERIFIED OFFLINE** | `response_schema`/`additionalProperties` defect was changed to `response_json_schema`; SDK request-layer regression passes without network. |
| Agent live Gemini interpretation | **NOT VERIFIED** | One authorized request after the schema fix returned Agent HTTP 502 after about 15 seconds. No Google response was confirmed. A transport/read timeout is possible but not proven because the catch-all currently suppresses the underlying exception. |
| Backend real generation | **NOT VERIFIED** | No complete live generation job was run during Agent packaging. Do not infer success from health/configuration. |
| Backend MAS implementation | **PRESENT / OFFLINE TESTED** | Existing Composer, Illustrator, Solver, Reviewer, RAG, validation, job, preview, approval and export code is preserved. |
| Official Application Knowledge document | **NOT PROVIDED** | Runtime help remains grounded in the verified UI capability registry. |

Unsupported Agent actions remain explicit: direct generation, direct Backend calls, workspace deletion, Word/DOCX export, V-ACT UI flow, upload, web search, stable question focus, conversational approval and conversational export.

## F. Minimal next Gemini diagnostic

Do not start with Backend generation. Diagnose the Agent independently with the teammate's own key.

1. Confirm `AGENT_MODE=gemini`, the intended `GEMINI_MODEL`, and key presence through `/agent/health`. Presence is not proof of validity.
2. Start the Agent in the foreground so local diagnostics are observable.
3. Before another live request, add sanitized exception diagnostics around the catch-all in `GeminiInterpretationProvider.interpret`. Log only exception class, numeric HTTP status/code, SDK status name and elapsed time. Never log the key, request headers, teacher message, prompt, response body or complete provider exception details.
4. Explicitly classify SDK/httpx transport timeouts as `gemini_timeout`; retain the existing auth, model and quota mappings. Validate these mappings with synthetic exceptions offline.
5. Run the focused Agent tests and Ruff.
6. After inspecting the developer project's current model access and quota, authorize exactly one Agent-only request:

```powershell
.\.venv-agent-ui\Scripts\python.exe scripts\smoke_agent_gemini.py
```

7. Record whether an outbound request occurred, the configured model, sanitized status/error class, elapsed time, and whether the response actually drove interpretation. Do not report success from health alone.
8. Only after the Agent issue is understood should the team separately plan one explicitly authorized Backend provider smoke. A complete exam-generation job is not the first diagnostic step.

## Cost-free package verification

```powershell
.\.venv-agent-ui\Scripts\python.exe -m pytest -q tests/test_agent_ui_service.py tests/api/test_ui_jobs.py tests/providers/test_gemini_openai_compat.py
.\.venv-agent-ui\Scripts\python.exe -m ruff check src/astra_agent_ui tests/test_agent_ui_service.py

Set-Location astra-frontend
npm test
npm run build
```

These checks use mocks, fixtures and blocked request layers. They are not live inference evidence.

## Delivery claims

- **INTEGRATED CODE:** packaged on `feat/agent-ui-first-merge`.
- **LIVE GEMINI AGENT VERIFIED:** no.
- **REAL BACKEND GENERATION VERIFIED:** no.
