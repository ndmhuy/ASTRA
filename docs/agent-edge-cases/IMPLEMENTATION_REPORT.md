# Edge-case implementation against the existing application

Baseline: `f9523e9e3b568b6495530ee18ee9ebd226416768`, branch `feat/agent-ui-first-merge`; remote ancestry checked. Original merged ancestor remains `8f12fbb2e9c7b6adb43b20b1966b256da6f45586`. Existing uncommitted audit documents were preserved. The complete 333-line all-in-one user document and embedded 90-case atlas were read. Matrix case wording comes from that document, not inferred scenarios.

## Code actually implemented

- `src/astra_agent_ui/plan_safety.py`: deterministic post-interpretation plan authorization, not a replacement intent classifier. Missing/contradictory question targets clarify; multiple explicitly named question IDs remain valid. A rejected dependency removes the executable tail. Negated costly actions, commentary, unavailable bank/random/upload/search/Word/V-ACT UI requests and invalid reload continuation cannot become business actions. Gemini mode still invokes the configured provider and fails explicitly; no fallback was introduced.
- `interpreter.py`: validates complete model plan through this guard before returning to React. General paraphrase understanding remains model-dependent and was not live-tested.
- `app.py`: actual body-size check, malformed content-length rejection, per-local-client/session 30 requests/minute guard, and immediate busy rejection instead of unbounded semaphore waiters. This is local process admission control, not authenticated tenant quota or distributed rate limiting.
- `astra-frontend/src/App.tsx`: synchronous in-flight turn ref, pre-dispatch 4000-character guard, visible offline/demo label, receipt-derived action success narration, sanitized failure category/code. Plain predicted model answers are suppressed when proposals exist. Existing handlers remain the only business callers.
- `agent/executor.ts`: target workspace/exam/revision validation, actionId/payload conflict rejection, preserved safe service error codes, meaningful prerequisite vs temporary-failure wording. Existing freshness, confirmation, effect verification and in-flight dedup remain.
- `state/examSessions.ts`: reject blank/oversized note updates; note approval cannot rebind an old job; reconcile pending note stable identity on matching job completion; ignore lower-percent nonterminal snapshots within one job; terminal error progress becomes explicitly failed. There is no invented event sequence or durable server note log.

Reused real UI functions: App workspace/setup/view/editor/confirmation handlers, ExamSessions message/note/generate/watch/preview state, ApiExamService idempotent start and existing HTTP services, QuickPresetModal catalog, ExamPaperView/QuestionCard presentation. No Backend business/core/provider/RAG module or environment credential file was changed.

## Verification and scope

- Frontend tests: **25 passed** (target mismatch/action ID conflict, confirmation, cancel/dedup, state lifecycle, provider errors and preview fixtures).
- Agent tests: **45 passed** (new target/source/commentary/dependency/negation/reload/rate tests plus prior boundary/provider regressions).
- Chrome: **8 turns**, actual React components/state/executor; answers, focus, editor draft, disclosures, setup two-step receipts, cancellation, unsupported no-op, stale-context abort passed. Model HTTP responses are fixtures; Backend calls are intercepted. **REAL_UI_PASS**, not live Gemini success.
- Frontend build/lint and Python Ruff passed. Build retains existing large-chunk warning.
- Zero live Gemini calls and zero real generation/revision jobs.

Commands:

```powershell
npm --prefix astra-frontend test
npm --prefix astra-frontend run lint
npm --prefix astra-frontend run build
node astra-frontend/tests/browserActions.mjs
.\.venv-agent-ui\Scripts\python.exe -m pytest tests/test_agent_ui_service.py -q
.\.venv-agent-ui\Scripts\python.exe -m ruff check src/astra_agent_ui tests/test_agent_ui_service.py
```

Matrix counts: **22 IMPLEMENT_NOW**, **28 SAFE_GUARD_NOW**, **40 BLOCKED_BACKEND** = 90. These are feasibility/ownership classes, not pass counts. Exact cases without executed evidence are labelled NOT_VERIFIED. Browser fixtures prove mounted effects and guard behavior, not arbitrary Vietnamese language accuracy. Read `CASE_IMPLEMENTATION_MATRIX.md` for each case's limits.

Still blocked: distributed ownership/atomic workspace single-job enforcement, durable cancellation/resume/mutation receipts, sequence-aware events, bank import/QA/pool feasibility/family dedup, random selection/hybrid assembly, rights and immutable source snapshots. No fake endpoints, item bank or psychometric equivalence was added.
