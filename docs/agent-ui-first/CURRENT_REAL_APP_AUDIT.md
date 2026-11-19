# Current integrated ASTRA: capability and product-vision audit

Audience: Agent, UI/UX and Backend teammates. Audit date: 2026-11-19, Asia/Bangkok. **Audit only; application code unchanged.**

## Reproducible baseline

- Worktree: `D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA-agent-ui-first`.
- Branch: `feat/agent-ui-first-merge`.
- Audited HEAD and fetched feature remote: **`bb7f59e30b832adb428f819aa56ecc0ad25f4453`**.
- Original merged ancestor: `8f12fbb2e9c7b6adb43b20b1966b256da6f45586`.
- User-authorized fast-forward: `19950bf` -> `0cd2713` (V-ACT option/UI polish) -> `24aac71` (format resource/template hashes) -> `bb7f59e` (documentation organization). No history rewritten, integration merge commit, push or application edit.
- `02_CODEX_REAL_APP_CAPABILITY_AUDIT_PROMPT.md` was **not found** in the repository. This audit follows the user's supplied requirements.
- Vision references: `docs/mvp-plan.md:1` (teacher request, blueprint, RAG, writing, independent solving, review and publishing), `docs/notes/document.md:7` and `:52` (original user journey). Those documents contain historical format sizes and proposed endpoints; current code, not those descriptions, determines availability.

## Verdict

ASTRA has a working **single-process local THPT application**, a separate native V-ACT Backend/CLI workflow, an increasingly broad React Agent adapter, and significant unfinished reliability/product contracts. It is not yet the original general exam assistant.

The newly visible V-ACT choice is **UI_ONLY / PARTIAL**, not an enabled generation flow. Native V-ACT is **BACKEND_ONLY**, not missing generation code. CUSTOM_RANDOM is **MISSING as a product mode**, although generic bank/matrix validation is reusable.

Do not reuse the earlier “96.9%” adapter coverage figure as product completion: it counts grouped adapters, does not enumerate all workflow state combinations, and does not prove live language mapping, confirmation integrity, multi-tab correctness or exam quality.

## Classification and evidence rules

| Label | Meaning |
|---|---|
| ACTUALLY IMPLEMENTED | Reachable code performs the operation; runtime proof is separately stated |
| BACKEND_ONLY | Functioning server/CLI/domain path not wired into the current teacher UI workflow |
| UI_ONLY | UI representation/local behavior with no complete Backend operation |
| MOCK_ONLY | Fixture/simulation behavior; not evidence of production model generation |
| PARTIAL | Some of the requested end-to-end contract exists; exact gap is stated |
| MISSING | No implementation found in inspected paths |
| NOT VERIFIED | No current runtime evidence for that claim, even when source exists |

All file/line references in this audit are relative to the audited repository SHA. Runtime fixture tests do not establish live provider health or semantic question quality.

## Current runtime and tests

At inspection start, none of ports 5173/8000/8010 was listening. Started **only Vite** for browser inspection. Final observation: 5173 listening; business Backend and Agent not listening. Thus the ordinary browser cannot perform real chat/generation until those services are started; no health flag is claimed for them at this SHA.

| Check actually run | Result | Limits |
|---|---|---|
| `python -m pytest -q tests/api tests/thpt tests/vact tests/core tests/providers tests/test_agent_ui_service.py tests/architecture` via `.venv-agent-ui` | **264 passed, 11.99s** | Isolated fixtures/provider transports; compiler tests can use local toolchain; no inference |
| `npm --prefix astra-frontend test` | **22 passed** | State/executor/service fixtures |
| frontend lint | passed | Source checks |
| frontend production build | passed | Existing chunk warning, ~603 kB JS |
| `node astra-frontend/tests/browserActions.mjs` | **PASS**, four turns, actual Chrome/React | Model HTTP/Backend intercepted; answers, focus, setup and receipts observed; zero inference |
| Concurrent JobStore probe, temp DB, 16 callers/8 threads/same key | 1 distinct job, exactly 1 creator | Tests DB idempotency only, not live model side effects |
| Same key/different fingerprint | JobConflict observed | HTTP mapping is 409 (`api/app.py:76`) |
| Second-manager startup interruption | queued job became failed | Confirms process-ownership limitation |
| Direct format catalog/GenerateRequest probe | only `thpt-math`; V-ACT rejected in formatId/subject/examType/duration/itemCount | No job/model call |
| Two-tab Chrome draft probe | Tab A displays Draft A, tab B displays Draft B, persisted array holds Draft B | Confirms stale UI and last-writer-wins persistence; no inference |
| Confirmation-language probe | `xác nhận=true`; `đồng ý=false` | Direct invocation of actual exported matcher |
| Live Gemini, current live THPT/V-ACT generation, current generated-paper quality | **NOT VERIFIED / NOT RUN** | Explicit audit restriction |

One temporary DB probe encountered Windows WinError 32 during cleanup after reporting its results. `JobStore.connect` returns sqlite connections used as transaction context managers without explicit close; handle lifetime relies on garbage collection. No application DB was modified by that probe.

## Full teacher workflow assessment

### Natural-language app control

`ModernChatBar.handleSend` -> `App.processAgentTurn` (`App.tsx:378`) -> `AgentClient.interpret` (`agent/client.ts:11`) -> session-protected `/agent/interpret` (`astra_agent_ui/app.py:138`) -> `AgentInterpreter.interpret` (`interpreter.py:304`) -> mandatory Gemini or explicit offline mode -> typed decisions -> React registry/executor (`executor.ts:22`) -> existing App/store handlers -> receipt -> per-workspace task (`orchestrator.ts:20`).

**ACTUALLY IMPLEMENTED**, with browser fixture proof for answers/paper/question focus and guided setup. **PARTIAL** against the vision: no autonomous replan; no navigation-history stack; Gemini receives IDs/roles, not previous teacher text or a structured conversation intake history. The active task is supplied by React but omitted from the provider's minimal context (`gemini_provider.py:84`), limiting “continue/like before” understanding. Four-decision ceiling can constrain requests containing both answer and actions.

### Guided THPT creation

Open real setup -> `getExamFormats` (`examService.ts:534`) -> Backend catalog (`ui/contracts.py:13`) -> available format and prompt -> `ui.exam.configure_setup` -> pending teacher confirmation -> React `store.generate` (`examSessions.ts:345`) -> `POST /api/exams/generate` (`routes_ui.py:54`) -> `JobManager.start/:131` -> RAG -> native THPT orchestration -> status/package.

**ACTUALLY IMPLEMENTED** for locked Math grade 12 / 22 questions / 90 minutes. Catalog slot blueprint can be overridden only through the validated Backend contract; React has no matrix editor. Arbitrary natural-language constraints do not mutate the locked matrix. Native Request enforces P1 12, P2 4 with four statement levels each, P3 6 (`thpt/models.py:27`). Prompt preferences are sent to models, not automatically guaranteed by a business constraint validator.

**PARTIAL:** intake is selected format + free text, not a durable confirmed/missing/changeable-field conversation contract. “20 questions” cannot become a valid THPT request. Setup modal's current V-ACT data is a frontend fallback, not a catalog response.

### Guided V-ACT creation

`QuickPresetModal.tsx:16` defines unavailable V-ACT fallback; `mergeWithVactOption/:37` adds it to actual catalog results. `resources/exam_formats/vact_dgnl_v1.json` exists, also unavailable. `format_catalog/:13` never loads it; `GenerateRequest/:18` accepts only THPT. `JobManager` imports THPT Request/Orchestrator/rendering and hardcodes 22-question/package metadata.

Separate `vact/cli.py:8` -> native V-ACT Orchestrator (`vact/orchestrator.py:11`) supports 120 MCQs, ordered q1..q120 slots, passage/table/group binding, batched composition/solving, template rendering and human review. Fixture tests passed. **BACKEND_ONLY / PARTIAL** overall. No V-ACT HTTP UI-job route or unified revision/package/preview contract; merely enabling the frontend option would be incorrect.

### Generation progress and conversation

Backend persists stage snapshots (`jobs.py:160/:389`), SSE emits changed snapshots (`routes_ui.py:68`); React combines EventSource and 1.5-second polling (`examService.ts:555`). Composer stages can overlap and stage percent is monotonic coarse progress. Backend emits no `latestItemPreview` per question; simulated per-question emergence is a MockExamService behavior. UI chat remains enabled except while a turn is busy.

**ACTUALLY IMPLEMENTED** stage/status and terminal results; **MOCK_ONLY** per-question progressive stream; **MISSING** teacher generation cancellation. Deleting a local workspace or cancelling Agent task stops local observation, not provider work.

### Deferred revision notes

UI ledger (`examSessions.ts:264/:287/:294/:301/:321`) supports create/dedupe/update/cancel/approve/apply with job/workspace associations and optional stable question/revision identifiers. Completion surfaces pending notes (`:662`). Application calls existing single-question regenerate, invalidates preview and requires a higher observed revision.

**PARTIAL:** notes are browser-local, generation-time stable IDs may be null, completion does not reconcile every note identity, apply does not compare the note's original approved revision/job to the current exam before submission. General notes without target question cannot be applied. Failed notes can be edited back to pending, not approved directly. Direct UI note apply catches no rejection locally. No server note ledger or batch revision API.

### Review, approval and export

Question editing persists through `jobs.py:402`; regeneration (`:443`) repairs one question but solves the entire revised exam, optionally redraws, and intentionally performs **no extra Reviewer pass**. Both increment revision and clear approval. Preview is revision/source-hash keyed (`preview.py:26`), local compiler-based, checks source and cached PDF hashes. UI approval requires matching ready/opened preview (`examSessions.ts:173`). Backend approval (`jobs.py:432`) checks revision/content/source but **does not require a ready/viewed preview**. Export (`:519`) requires current approval and unchanged source; supported combinations are student tex/pdf and teacher JSON.

**ACTUALLY IMPLEMENTED** fixture-tested workflow; **PARTIAL** end-to-end review authority. Approval is an assertion by the supplied reviewer string, not authenticated teacher identity. Export/download receipts confirm dispatch, not OS save or print success. Source-file streaming has a transaction gap discussed in the reliability report.

## Companion reports

- [Capability inventory](CURRENT_CAPABILITY_INVENTORY.md)
- [Persistence, concurrency and safety boundaries](CURRENT_STATE_RELIABILITY_AUDIT.md)
- [CUSTOM_RANDOM feasibility](CUSTOM_RANDOM_FEASIBILITY.md)
- [Adversarial edge-case matrix](ADVERSARIAL_TEACHER_MATRIX.md)
- [Cross-team roadmap and acceptance contracts](CROSS_TEAM_PRODUCT_ROADMAP.md)

No production-readiness or universal UI-control verdict is inferred from passing fixtures. The audit files are new deliverables; historical reports are not rewritten as current evidence.
