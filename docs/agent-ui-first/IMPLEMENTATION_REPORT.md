# ASTRA UI-First Agent Implementation Report

Date: 2026-11-18 (Asia/Bangkok)

Audience: ASTRA UI, Agent, and integration reviewers

Baseline: `origin/merge-mas-and-uiux` at `8f12fbb2e9c7b6adb43b20b1966b256da6f45586`

Feature branch: `feat/agent-ui-first-merge`
Worktree: `D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first`

## Outcome

The verified GO slices are implemented without changing ASTRA business-core code. A dedicated loopback Agent service interprets minimal UI context and returns proposals. The React UI alone validates and executes allowlisted actions, observes resulting state, and produces receipts. Agent code has no `exam_baseline` import, business URL, exam client, job client, RAG client, or export client.

The following are now `REAL_CALLABLE_FROM_AGENT` when the local Agent service and UI are running:

- `ui.navigate`
- `ui.session.create`
- `ui.session.open`
- `ui.exam.open_setup`
- `ui.sidebar.set_collapsed`
- `ui.note.add`
- `ui.note.update`
- `ui.note.cancel`

Generation, question mutation, preview, approval, and export remain UI-owned ordinary workflows and are described in help, but are deliberately not Agent-callable in this slice. The Agent can open the real setup modal; only the modal's existing teacher confirmation can begin generation.

## Architecture delivered

```text
Teacher -> React chat -> /agent/interpret (loopback, session token)
        <- answer or typed UI action proposal
React -> context/version/schema/allowlist validation
      -> existing App / ExamSessions handler
      -> observed post-state receipt
      -> verified teacher-facing response

React ordinary controls -> existing examService -> ASTRA business Backend
Agent service ------------------------------------X no business access
```

`src/astra_agent_ui/` is a separate interpretation package. It accepts only a sanitized snapshot, has a deterministic Vietnamese router, registry-only help fallback, future knowledge-source interface, and optional schema-bounded Gemini adapter. `astra-frontend/src/agent/` owns the runtime manifest, context tracker, transport, executor, idempotency cache, stale-state checks, effect verification, and dependent-step stopping.

## Slice evidence

| Slice | Delivered behavior | Verdict |
|---|---|---|
| 1 — interpreter and live executor | Typed context/proposals/receipts; schema validation; default-deny registry; duplicate and stale rejection; observed UI effects; dependent-step stopping | `REAL_UI_PASS` for create/open workspace; `UNIT_ONLY` for other executor guards |
| 2 — optional Gemini | Official `google-genai` adapter, `gemini-3.8-flash`, Pydantic response schema, 15-second timeout, bounded context/output, no tools, fail-closed allowlist | `UNIT_ONLY`; live model intentionally not called because no opt-in key was supplied |
| 3 — guided setup | Natural Vietnamese/no-accent setup requests open the existing `QuickPresetModal`; the real catalog displayed Toán THPT, 22 questions, 90 minutes | `REAL_UI_PASS`; no generation launched |
| 4 — chat and notes | Composer is no longer disabled by generation; UI-owned notes can be added/updated/cancelled and are never auto-applied; completion prompts for review | `UNIT_ONLY` for active-job behavior; ordinary browser chat passed |
| 5 — assistance | Missing official knowledge file falls back to verified runtime registry; Word/V-ACT/upload/search/question-focus are answered as unsupported; unsupported controls are disabled | `REAL_UI_PASS` for registry help; `UNIT_ONLY` for adversarial cases |

## Real browser run

With the local Agent service on 8010 and Vite on 5173, the real Chrome-rendered application was exercised:

1. From the start screen, teacher entered `Mở màn hình soạn đề`.
2. `/agent/session` and `/agent/interpret` returned HTTP 200.
3. Agent proposed `ui.session.create` using the current state version.
4. UI executor called the existing `ExamSessions.create` and `App.openSession` path.
5. The workspace appeared and chat displayed: `Giao diện đã xác nhận thao tác thành công.`
6. `ASTRA làm được gì?` returned registry-grounded help while Gemini was disabled and no key existed.
7. `Mở thiết lập đề Toán THPT` opened the real catalog-backed modal. It showed Toán Học, grade 12, 22 questions, 90 minutes and explicit unsupported-file text. The modal was cancelled; **Tạo đề thi was not clicked**.

This is a `REAL_UI_PASS` for Agent service -> proposal -> UI executor -> observed UI state. It is not evidence of live Gemini or live exam generation.

## Security and boundary facts

- Agent binds to `127.0.0.1`/`localhost` only and rejects non-loopback host configuration.
- CORS origins default to exactly `http://127.0.0.1:5173` and `http://localhost:5173`.
- `/agent/session` issues an in-memory random token; `/agent/interpret` requires it.
- Payload is capped at 64 KiB, turns are concurrency-limited, and teacher messages are capped at 4,000 characters.
- `GEMINI_API_KEY` is loaded only by the Agent process from environment or ignored `agent-service/.env.local`.
- Health reports key presence only. No key value is logged, returned, stored in React, or placed in a `VITE_*` variable.
- Static scans found no Agent business API URL, `exam_baseline` import, or browser Gemini credential.

## Test results

| Command | Result |
|---|---|
| `npm test` | 18/18 frontend tests passed |
| `npm run build` | Passed; existing >500 kB chunk warning remains |
| `npm run lint` | Passed |
| `python -m pytest -q` | 406 tests plus 7 subtests passed; one existing Starlette/httpx warning |
| `python -m ruff check src/astra_agent_ui tests/test_agent_ui_service.py` | Passed |
| boundary `rg` scan | No Agent fetch/business route/import found |
| bundle secret scan | No `GEMINI_API_KEY` or `VITE_*GEMINI` in frontend source/build |

The final counts above supersede intermediate focused runs.

## Local development

From the feature worktree:

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn astra_agent_ui.app:app --app-dir src --host 127.0.0.1 --port 8010
```

In another shell:

```powershell
cd astra-frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Start the existing business Backend on port 8000 only when catalog or ordinary exam UI workflows are needed. Install `.[agent]` and configure the ignored local environment only for an explicitly opted-in Gemini run; see `GEMINI_LOCAL_SETUP.md`.

## Explicit limitations

- No live Gemini call, paid inference, or real generation job was performed.
- No official ASTRA application-knowledge document exists. The shipped help source status is `verified_ui_registry_only`.
- Agent cannot delete workspaces, generate, edit questions, focus a question, approve, export, upload, search the web, run V-ACT, or export Word.
- No production authentication/multi-user deployment claim is made; this is a secured local development boundary.

## Release verdict

- `READY_FOR_DRAFT_PR`: **YES**, after reviewer inspection of teammate-owned wiring listed in `TEAM_CHANGES.md`.
- `READY_FOR_MERGE`: **NO**. Live Gemini remains opt-in and unverified for the developer's project/quota; browser automation is manual evidence rather than a committed browser CI suite; production auth is out of scope; product/UI owners must review the new chat and disabled unsupported affordances.
