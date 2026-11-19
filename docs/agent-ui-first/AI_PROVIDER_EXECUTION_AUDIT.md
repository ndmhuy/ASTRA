# AI Provider Execution Audit

Date: 2026-11-19 (Asia/Bangkok)

Audited remote baseline: `origin/merge-mas-and-uiux` at
`8f12fbb2e9c7b6adb43b20b1966b256da6f45586`

Implementation branch: `feat/agent-ui-first-merge`

Local implementation commit: `d8e00f2` (`feat(agent): require Gemini in AI mode`)

## Findings at a glance

- The refreshed remote SHA is unchanged. This audit traces the actual merged source, not an old report.
- The normal UI generation path is real only when Backend `EXAM_PROVIDER=chat_completions` is
  configured. The default `mock` setting does **not** silently generate a mock UI result;
  `JobManager.provider_scope()` rejects it with `provider_not_configured`.
- In the normal live UI path, one `ChatCompletionsProvider` instance is assigned to Composer,
  Illustrator, Solver and Reviewer. Therefore all four roles use the same configured provider,
  model, endpoint, token limit and timeout. Tests or callers may inject different providers per role.
- RAG retrieval, LaTeX rendering, persistence, packaging, approval and export do not invoke a model.
- Agent `gemini` mode now requires a successful Gemini invocation for every natural-language turn.
  It no longer silently falls back to offline intent rules. `offline` is a separately selected and
  explicitly labelled deterministic mode.
- Agent and Backend credentials are loaded from different git-ignored files and never enter React.
- No live call was made in this audit because no credential was supplied and live inference was not
  explicitly enabled. Configuration or a health flag is not counted as invocation evidence.

## Backend execution path

### 1. React request and UI service

1. `astra-frontend/src/App.tsx:111-117`, `handleQuickStart()`, is invoked by the setup modal's
   confirmation handler and calls `store.generate(...)`.
2. `astra-frontend/src/state/examSessions.ts:273-305`, `ExamSessionStore.generate()`, records a
   generating state, creates/reuses an idempotency request ID and invokes
   `this.service.startGeneration()` at line 301.
3. `astra-frontend/src/services/examService.ts:546-552`,
   `ApiExamService.startGeneration()`, calls `requestJson()` and performs
   `POST /api/exams/generate` with JSON plus `Idempotency-Key`.
4. `requestJson()` at `examService.ts:510-531` performs the browser `fetch`, parses the JSON error
   envelope and converts non-2xx responses to `ApiError`.

No AI model is invoked in these React stages.

### 2. Backend route and JobManager

1. `src/exam_baseline/api/app.py:39-45` constructs `JobManager` during FastAPI lifespan.
2. `src/exam_baseline/api/routes_ui.py:53-59`, `generate()`, validates `GenerateRequest` and forwards
   it to `request.app.state.ui_jobs.start()`.
3. `src/exam_baseline/ui/jobs.py:131-158`, `JobManager.start()`, resolves the validated THPT request,
   persists a queued job and schedules `_generate()` with `asyncio.create_task()`.
4. `_generate()` at `jobs.py:178-275` runs retrieval first (`182-198`). A retrieval gap ends the job
   before any provider call. With no injected runner, lines 207-210 enter `provider_scope()` and call
   `Orchestrator.run()`.

`JobManager` allows at most two concurrent generation jobs (`jobs.py:100`). This is application
concurrency, not a provider quota.

### 3. Provider selection

`src/exam_baseline/ui/jobs.py:118-129`, `JobManager.provider_scope()`:

- If `pipeline_providers` were injected into `create_app()`, those objects are used. Tests use this
  route for replay/scripted providers; such calls are mock/offline unless the injected object itself
  performs network I/O.
- Otherwise `settings.provider` must equal `chat_completions`. Any other setting, including the
  default `mock`, produces HTTP-facing error `provider_not_configured`.
- Lines 126-129 force `response_format="json_schema"`, construct one
  `ChatCompletionsProvider`, and use `dict.fromkeys(...)` to assign that same instance to
  `composer`, `illustrator`, `solver`, and `reviewer`.

Backend configuration is loaded by `src/exam_baseline/config.py:11-27` using prefix `EXAM_` and
root file `.env`:

- `EXAM_PROVIDER`
- `EXAM_MODEL`
- `EXAM_API_KEY`
- `EXAM_BASE_URL`
- `EXAM_TIMEOUT_SECONDS` (default 90 seconds)
- `EXAM_MAX_OUTPUT_TOKENS` (default 8192)
- `EXAM_TOKEN_LIMIT_FIELD` (`max_completion_tokens` or `max_tokens`)
- `EXAM_RESPONSE_FORMAT` (overridden to `json_schema` for UI jobs)
- optional temperature, seed, price and spend-ledger variables

`Settings.complete_configuration()` at `config.py:53-77` rejects a missing key, fixture model,
invalid URL and inconsistent spend/structured-output settings before startup.

### 4. Generation stages and actual call multiplicity

`src/exam_baseline/thpt/orchestrator.py:87-306`, `Orchestrator.run()`, owns the live stage order.
Its nested `call()` function (`122-169`) selects `self.providers[agent.role]`, wraps it in
`RecordingProvider`, and invokes `agent.run()`.

| Stage | Caller and source | Nominal model calls | Conditions and skips |
|---|---|---:|---|
| Composer | `compose_part()` at `orchestrator.py:180-213`; `ComposerAgent` at `agents.py:148` | 3 per revision: P1, P2, P3 | Calls may run concurrently. Resume checkpoints at `orchestrator.py:142-148` skip already completed stages. A second revision adds 3 calls only if Reviewer requests revision. |
| Illustrator | `illustrate()` at `orchestrator.py:49-60`, invoked at line 217; `IllustratorAgent` at `agents.py:249` | 1 per revision | It is still called when the request list is empty and is instructed to return `drawings=[]`. A custom injected deterministic illustrator can avoid the provider, but the default live path does not. |
| Solver | `solve()` at `orchestrator.py:62-67`, invoked at line 223; `SolverAgent` at `agents.py:261` | 1 per revision | Receives student-visible questions and drawings, not Composer's private answers. Resume can skip it. |
| Reviewer | `orchestrator.py:228-243`; `ReviewerAgent` at `agents.py:270` | Exactly 1 on revision 1 | It is never called on revision 2. It may request one content revision. |

Nominal successful execution is six provider calls: three Composer, one Illustrator, one Solver and
one Reviewer. If Reviewer requests revision, the pipeline adds three Composer, one Illustrator and
one Solver call, for eleven nominal calls total. This is not a fixed billing count:

- `Agent.run()` at `agents.py:95-145` allows one schema-correction completion for every role except
  Reviewer (`attempts = 2` versus `1`).
- `RecordingProvider.complete()` at `thpt/runtime.py:29-39` allows one network retry for non-Reviewer
  stages after 429, 500, 502, 503, 504, timeout or unreachable errors, waiting one second. Reviewer
  has no provider retry.
- Consequently one logical non-Reviewer stage may make up to two schema attempts, and each attempt
  may make up to two outbound HTTP attempts. Checkpoint resume may instead make zero.

### 5. Outbound Backend model request

`src/exam_baseline/providers/chat_completions.py` is the only adapter used by this UI path:

- `ChatCompletionsProvider.__init__()` at lines 17-35 selects `settings.model`, constructs
  `{EXAM_BASE_URL}/chat/completions`, reads the secret, timeout and output limit.
- `complete()` at lines 39-101 builds OpenAI Chat Completions messages, model, token field and JSON
  schema response format.
- `_send()` at lines 103-138 performs the real `httpx.AsyncClient.post()` at lines 105-110 with
  `Authorization: Bearer ...` and the configured timeout.
- Status-specific errors exist for 400, 401, 403, 404, 429, 500, 502, 503 and 504; transport and
  timeout errors are separately classified. No model is silently substituted.
- Lines 141-181 parse `choices[0].message.content`, usage, response ID and returned model. Refusal,
  content filtering, non-`stop` finish reason, empty content and malformed envelopes are errors.
- `Agent.run()` then normalizes JSON and validates it against the role's Pydantic contract. Invalid
  output is bounded as described above; it is never accepted merely because the HTTP call succeeded.

### 6. Result returned to the UI

1. `JobManager._generate()` reads validated pipeline artifacts and stores the completed job at
   `jobs.py:211-245`; provider/contract failures are converted into a failed job at `251-280`.
2. `routes_ui.py:62-88` exposes status as polling and SSE. `JobManager.status()` at
   `jobs.py:389-396` returns stage, status and sanitized error.
3. `ApiExamService.onProgress()` at `examService.ts:555-584` consumes SSE and polls every 1.5s as a
   fallback. Three consecutive polling failures produce a UI network error.
4. On completion, `examSessions.ts:323-327` invokes `getExamPackage()`.
5. `routes_ui.py:91-93` calls `JobManager.package()`. `jobs.py:297-387` maps validated questions,
   solutions, drawings, provenance and warnings into the UI package.
6. `ApiExamService.getExamPackage()` at `examService.ts:587-592` returns the package to the store,
   which marks the workspace complete.

## Backend Gemini compatibility

The existing adapter is compatible in shape with Google's OpenAI compatibility layer; no pipeline
rewrite is justified:

- Google documents `https://generativelanguage.googleapis.com/v1beta/openai/` plus
  `/chat/completions`, bearer authentication and structured output.
- The repository adapter uses those same wire conventions.
- Offline test `tests/providers/test_gemini_openai_compat.py` verifies the exact URL, bearer header,
  `gemini-3.8-flash`, `max_tokens`, JSON schema payload and response parsing with `MockTransport`.

This proves adapter construction and parsing, not project access or a live generation. The OpenAI
compatibility layer remains documented as beta, and the full THPT schemas must still be exercised
against the configured project/model in the authorized live smoke.

## Agent Gemini execution

### Mode boundary

- `src/astra_agent_ui/config.py:48-70` loads only documented keys from
  `agent-service/.env.local`.
- `AGENT_MODE=offline` uses deterministic UI interpretation and returns `provider="offline"`.
- `AGENT_MODE=gemini` routes every natural-language turn through Gemini. The offline classifier is
  not used as a provider failure fallback.
- `AgentInterpreter.interpret()` at `interpreter.py:296-327` implements this split. Gemini output is
  still checked against the callable `available_real` UI registry by
  `_validate_model_decision()` at `interpreter.py:275-294`.

### Actual network invocation

`src/astra_agent_ui/gemini_provider.py:27-114`,
`GeminiInterpretationProvider.interpret()`:

1. Requires Gemini mode and a local key before importing the optional SDK.
2. Sends only the teacher message (capped at 4,000 characters) and minimized UI context.
3. Constructs `google.genai.Client` at line 75 with a 15-second HTTP timeout.
4. Calls `client.models.generate_content()` at line 79 using exact model
   `GEMINI_MODEL` (default `gemini-3.8-flash`). The native SDK targets the Gemini Developer API
   `POST /v1beta/models/{model}:generateContent` endpoint.
5. Requests Pydantic-structured `GeminiDecision`, maximum 500 output tokens, temperature 0.1, no
   tools and no automatic continuation. This is one bounded interpretation request.
6. Uses `response.parsed`, otherwise validates `response.text`; empty or invalid responses fail.
7. The outer 15-second bound and SDK HTTP timeout classify timeout, authentication/access, missing
   model, quota/rate-limit and other provider failures.

The optional dependency is constrained to `google-genai>=3.6,<4`; PyPI reported 3.6.1 as the
current release during this audit. The live model remains independently fixed by `GEMINI_MODEL`.

`src/astra_agent_ui/app.py:56-89` converts provider failures into explicit JSON error envelopes.
Missing key is 503, quota is 429, timeout is 504, and auth/model/provider failures are 502/503 as
appropriate. `astra-frontend/src/agent/client.ts:23-36` now displays that explicit error. No UI
action proposal is executed when interpretation fails.

The Agent only returns allowlisted UI proposals. It has no import of `exam_baseline`, no Backend URL
and no `/api/exams` request.

## Model identity, pricing and quota

Configured model ID is exactly `gemini-3.8-flash`; there is no automatic model fallback.
Google's current model catalog identifies it as a stable model, with structured output support,
1,048,576 input tokens and 65,536 output tokens. ASTRA applies much smaller limits: Agent 500 output
tokens; Backend 8,192 by default.

Google's current pricing page shows a free tier for standard Gemini 3.8 Flash requests and paid token
pricing, but this does **not** prove this project has free or available quota. Rate limits are applied
per project and vary by tier/account status. The actual RPM/TPM/RPD must be checked in the key's
Google AI Studio **Dashboard → Rate limits/Usage**. A 429 remains a failed smoke; ASTRA will not
switch models.

Authoritative references:

- Model catalog: https://aistudio.google.com/docs/models/gemini-3.8-flash
- Pricing: https://aistudio.google.com/docs/pricing#gemini-3.8-flash
- Project-specific quota: https://aistudio.google.com/docs/rate-limits
- OpenAI compatibility: https://aistudio.google.com/docs/openai
- Python SDK: https://googleapis.github.io/python-genai/

## Local credential setup on Windows

Never paste a key into chat, React, a command line argument or a committed file.

### Agent credential

Template:

`D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first\agent-service\.env.example`

Create this ignored file manually:

`D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first\agent-service\.env.local`

```dotenv
AGENT_HOST=127.0.0.1
AGENT_PORT=8010
AGENT_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
AGENT_MODE=gemini
GEMINI_MODEL=gemini-3.8-flash
GEMINI_API_KEY=<insert locally>
```

`AgentSettings.from_environment()` explicitly loads this file. It does not read Backend
`EXAM_API_KEY`.

### Backend credential

Template:

`D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first\.env.example`

Create this ignored file manually:

`D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first\.env`

```dotenv
EXAM_PROVIDER=chat_completions
EXAM_MODEL=gemini-3.8-flash
EXAM_API_KEY=<insert locally>
EXAM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
EXAM_TIMEOUT_SECONDS=90
EXAM_MAX_OUTPUT_TOKENS=8192
EXAM_TOKEN_LIMIT_FIELD=max_tokens
EXAM_RESPONSE_FORMAT=json_schema
EXAM_SCHEMA_AS_TOOL=false
EXAM_STRUCTURED_OUTPUT_STRICT=false
```

Backend `Settings` reads root `.env` through Pydantic Settings. It does not read Agent
`GEMINI_API_KEY`. The same underlying value may be manually placed in both ignored files for local
development, but the services remain independently configured.

`.gitignore:19-21` ignores `.env*` while explicitly allowing only `.env.example`; lines 65-69 also
ignore `.env`, `.env.local`, `.env.*.local` and `*.local`. Both intended secret files were verified
with `git check-ignore`.

### Install and start

From PowerShell:

```powershell
Set-Location 'D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first'
py -3.12 -m venv .venv-agent-ui
.\.venv-agent-ui\Scripts\python.exe -m pip install -e '.[agent]'

# Terminal 1: Backend; loads root .env
.\.venv-agent-ui\Scripts\python.exe -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Agent; loads agent-service/.env.local
.\.venv-agent-ui\Scripts\python.exe -m uvicorn astra_agent_ui.app:app --host 127.0.0.1 --port 8010

# Terminal 3: React UI
Set-Location .\astra-frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

## Offline verification results

- Agent service tests: 34 passed offline, including required-AI-mode and explicit-error cases.
- Backend Gemini compatibility test: 1 passed offline with `httpx.MockTransport`.
- Combined targeted provider tests: 35 passed in a fresh ignored environment with
  `google-genai==3.6.1`.
- SDK construction check: real `HttpOptions(timeout=15000)` and
  `GenerateContentConfig(max_output_tokens=500, automatic_continuation=False)` validated offline.
- Full Python suite in that environment: 410 passed plus 7 subtests.
- Frontend: 18 tests passed; production build and lint passed. The existing >500 kB chunk warning
  remains non-blocking.
- No credential was present or used; outbound inference count: zero.

## Prepared live smoke A — Agent to Gemini

Prerequisites: configure `agent-service/.env.local`, set `AGENT_MODE=gemini`, install `[agent]`,
start the Agent, and explicitly authorize one live interpretation.

```powershell
Set-Location 'D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first'
.\.venv-agent-ui\Scripts\python.exe .\scripts\smoke_agent_gemini.py
```

Acceptance evidence:

- HTTP response has `provider: "gemini"` and a structured decision containing an actual generated
  response.
- The script never executes a UI proposal and prints `uiActionExecuted: false`.
- Missing/invalid key, unavailable model, 429, timeout or provider failure must fail explicitly.
- A health response or `geminiKeyConfigured=true` alone is not evidence.

Current status: **NOT RUN — blocked on manually configured key and explicit live-inference enablement.**

## Prepared live smoke B — UI to Backend to model provider

Prerequisites: configure root `.env`, confirm the exact model appears for the project, review quota,
start Backend/Agent/UI, and explicitly authorize live generation. In the browser, open the real setup
modal and confirm one THPT generation. This exercises `ApiExamService`, not a direct test shortcut.

Copy the returned job ID from `POST /api/exams/generate`, then inspect sanitized evidence:

```powershell
Set-Location 'D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first'
.\.venv-agent-ui\Scripts\python.exe .\scripts\inspect_backend_live_job.py '<job-id>'
```

Acceptance evidence:

- Browser Network shows the UI's 202 generation request and subsequent SSE/polling.
- The job report contains provider call records with returned model, status, latency and usage.
- At least one call must have `response_received`/`validated`; final job state must be reported as
  completed or failed, never simulated.
- Completed state must be followed by successful `GET /api/exams/{jobId}` and UI rendering.
- A failed 401/403/404/429/5xx is recorded as a real failed test, not converted to success.

Current status: **NOT RUN — blocked on manually configured key, explicit live-inference enablement,
and the cost/quota implications of a nominal 6–11 call generation.**

## Remaining blockers

1. Actual project model access and active quota cannot be known without the user's local project/key;
   Google directs users to AI Studio for project-specific limits.
2. Neither live smoke is authorized yet. No claim of live invocation is made.
3. Full Gemini compatibility of the pipeline's large role-specific JSON schemas remains a live-test
   question despite documented structured-output support and the passing adapter-level offline test.
4. The Backend can make substantially more than one provider request per exam because stages,
   revision, schema correction and transient retries are separate. Confirm quota/cost before enabling.
