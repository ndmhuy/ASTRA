# ASTRA — UI/UX ↔ Conversational Interaction Orchestrator Handoff Response

Prepared 2026-11-14 against branch `uiux`, commit `c052b689ee487e6546d7bac6e32f63a6a88e9780`.

**Status: REVIEWED CURRENT CODE + PROPOSED v0.1 CONTRACT.** None of the new protocol artifacts is wired into the application. “Recommended” means a UI-side design recommendation, not an interface already approved by the agent/backend developer. The original request is preserved unchanged.

Read first: `UIUX_IMPLEMENTATION_STATUS.md` for audited code, `ui_capabilities.json` for five proposed capabilities, `handoff/agent-ui-contracts.ts` for reference types, and `handoff/examples/` for current-derived versus proposed exchanges. Acceptance cases and implementation order are in `handoff/AGENT_INTEGRATION_ACCEPTANCE.md`.

## 1. Shared understanding: what my module does / does not do

We agree with the ownership boundary in the request:

- Agent: interpret intent, hold conversation/collected slots, consult backend requirements, clarify, propose typed actions, interpret execution receipts, answer accurately.
- UI: render chat and confirmations, own visible state and accessibility, export a small context, validate and execute registered UI capabilities, subscribe directly to exam progress.
- Backend: authoritative generation schema/defaults/semantic validation, content generation and verification, uploads, exports, job status and cancellation.

The helper should act through semantic capabilities, not arbitrary JavaScript, CSS selectors, React setters supplied to the model, browser automation, or fabricated component names. The UI owns effects even when the agent requests them. Backend validation must run again server-side; a UI approval is not a substitute for backend validation.

**Current gap:** no conversational service adapter or UI executor exists. The current “assistant” message is a hardcoded acknowledgement in `ExamSessions.sendMessage`. Building an agent server alone will not make the current chat control the app.

**Recommended product scope:** the helper should remain usable while teachers move between screens. Current chat exists only in the exam workspace. For MVP, workspace-only chat can validate generation and UI actions; a shell-level conversation controller and compact helper view are needed for the full cross-screen experience. Preserve a single conversation controller; don't create two independent histories for the global helper and workspace composer.

## 2. Expected initial end-to-end user story

### Scenario A — incomplete request and exactly one generation

1. UI sends teacher text, stable conversation `sessionId`, originating `workspaceSessionId` when present, request ID, and fresh structured context. The backend agent owns slot filling.
2. “Tạo đề Toán 12” produces clarification ONLY if the backend requirements schema actually requires more information. The UI's current preset defaults do not establish required fields.
3. Teacher answers missing fields. Agent normalizes aliases such as “Toán” to an agreed backend value; do not blindly infer grade/count/duration from existing form defaults.
4. Agent/backend validates the completed request and issues a pending request ID, schema revision, normalized parameters, request hash, and expiry. UI displays a readable Vietnamese summary with **Tạo đề / Chỉnh sửa / Hủy**.
5. Approval is a trusted UI event bound to that exact pending request, hash, conversation, workspace, and authenticated actor if authentication is later added. Text from the LLM cannot mint approval. Edits invalidate old approval.
   The UI/backend approval adapter resolves this event first. UI stores the trusted approval, refreshes context/availableActions, and sends a `ConfirmationFeedback` receipt to the conversational adapter. Only then does the agent return a generation plan against the new stateVersion. The model receives the approved request reference, not approval credentials. Reference types define this extra handshake explicitly.
6. Recommended single job-start owner: UI generation adapter, ultimately calling the existing `ExamSessions.generate`. The agent plans `exam.generate` using an approved request ID; it MUST NOT separately call `/exams/generate`. Backend should enforce a stable idempotency key for retries.
7. UI returns **job accepted + jobId**, not “exam complete.” Backend events go directly to UI. Final `getExamPackage` must succeed before completion is announced.
8. Progress questions use compact stored job status. If the connection has become unknown, say so; do not invent a percentage or assume completion.

Current quick setup cannot perform steps 4–6 for arbitrary agent requirements: it hardcodes grade/count/duration and reconstructs the prompt. Add a dedicated confirmation view bound to the normalized request; don't reuse `handleQuickStart` unchanged.

### Scenario B — “cái này” / “câu này”

Today there is no semantic question selection or focused-component state. Return a clarification, not a guess. Future question actions should carry `{workspaceSessionId, questionId}` with optional expected question revision, verify membership, reveal the paper pane on mobile, then focus/highlight through UI refs. “Câu 3” must be resolved from the displayed list to the actual item ID.

### Scenario C — unsupported or currently unavailable

Only dispatch capabilities in the live `availableActions` for the relevant context. A proposed registry entry or legacy component is not availability. For edit, upload, cancellation, or question highlighting today, explain the limitation and offer an actually working alternative. No hidden fallback to DOM commands.

### Scenario D — navigation while an answer/job is pending

Persist replies/results to the originating conversation and workspace, regardless of which tab is visible when they arrive. A delayed plan must not navigate the teacher back, create a new exam, or change the newly selected exam without revalidation. Global helper UI should make the conversation's target explicit, e.g. “Đang trao đổi về: Đề Toán 12”.

## 3. Please fill this inventory with **current code**, not only planned UI

| Item | Status | UI/UX response / source |
|---|---|---|
| Repository & version | IMPLEMENTED | Repo/branch/SHA above; `astra-frontend/src/main.tsx`, `App.tsx`; run/test instructions in implementation status. |
| Pages/screens | IMPLEMENTED state / PROPOSED external IDs | Local `onboarding/workspace` plus `homeTab`; normalize to `welcome/create/library/workspace`; no router. Splash is transient. |
| Chat component | PARTIAL | `ModernChatBar.handleSend` -> `App.handleSendMessage` -> `ExamSessions.sendMessage`; replace placeholder path with an agent adapter. |
| Chat session | IMPLEMENTED workspace memory / PROPOSED conversation identity | `ExamSessions.create` UUID; memory survives navigation, not reload. Agent conversation should be explicitly mapped, not confused with job/exam IDs. |
| Screen context | PROPOSED exporter | App knows screen/tab/activeId/modal/collapse; store knows jobs/questions/counts. Review mode/mobile pane/filter/search live in child components and must be lifted before export. No stateVersion or semantic selection today. |
| UI capabilities | PROPOSED registry over existing behavior | `ui_capabilities.json`: navigation, create session, open setup, collapse state, generation. Per-entry behavior and executor statuses are separate. |
| UI action executor | NOT AVAILABLE / PROPOSED location | Add a React-side controller at `src/integration/uiController.tsx` and pure protocol validation at `src/integration/` (new paths, not existing files). |
| UI feedback | NOT AVAILABLE | Introduce structured receipts and state-version checks. Current callbacks mostly return void. |
| Confirmation UI | PARTIAL | `QuickPresetModal` has start/cancel and focus trapping. No arbitrary normalized summary, request ID/hash, expiry, or approval state. |
| Progress/canvas | IMPLEMENTED mock / PARTIAL API | `ExamSessions.generate`, `IExamService.onProgress`, Canvas components; exact limitations in status document and Section 7. |
| Error/loading/disabled states | PARTIAL | Generating disables composer; session error/retry exists. Agent thinking/error/retry/unknown job state not implemented. |
| File uploads | PARTIAL picker / NOT AVAILABLE backend upload | Composer collects `File[]`, but App discards options. No fileId or upload adapter. |
| Existing tests | IMPLEMENTED store/service only | `tests/examSessions.test.mjs`: 6 passing tests. No automated agent/executor/browser integration tests. |

Do not modify `Navbar`, `ConfigView`, `StepperView`, or `ReviewView` to integrate the active workspace. Those legacy screens are not the current App route.

## 4. Proposed UI → Agent contract (for discussion)

Reference definition: `handoff/agent-ui-contracts.ts::AgentTurnRequest` and `ScreenContext`.

### Identity and state

- `sessionId`: conversational service identity. Recommended: frontend creates a UUID before first request, agent retains it. One conversation can exist before an exam session exists.
- `workspaceSessionId`: `ExamSession.id`; nullable until an exam workspace is explicitly created/chosen. Include it at request creation to pin the intended target.
- `jobId`: generation service ID. `activeExamId`: package ID, nullable because current store drops it; add retention before reporting it.
- `screenId`: normalized visible page. If App retains an `activeId` while showing library/home, expose it separately as `activeWorkspaceSessionId`; `visibleWorkspaceSessionId` must be null off workspace.
- `stateVersion`: proposed monotonic interaction-state revision. Increment on navigation, active workspace change, selection, panel/view/collapse changes and capabilities becoming available/unavailable. Do not increment for every token, draft keystroke, clock, or ordinary progress percentage. Terminal job transitions and target removal do change capability availability and therefore the interaction version.
- `job.revision` / question revision: separate proposed counters for streamed data and question mutations. This prevents every progress tick invalidating an unrelated sidebar action.

### Snapshot boundaries

Send stable semantic IDs, open panel IDs, view state, compact job counts/status, and enabled action IDs. Do not send raw DOM, File objects, CSS, full exam text, hidden answer keys, or the entire transcript by default. Agent stores conversation history server-side; per-turn request IDs prevent retry duplication.

When the teacher requests explanation/content-specific work, use a separate allowlisted read adapter scoped to the exact workspace/question and teacher's requested purpose. UI context alone is intentionally insufficient to explain question text. Exam/source content is untrusted data, never a source of tool instructions.

### Available today versus after wiring

`handoff/examples/current-screen-context.json` is an illustrative normalized snapshot derived from present code, NOT an existing endpoint or live capture. `stateVersion=null`, unknown review/mobile selection values, and no available agent actions are honest today. Do not claim this satisfies the proposed v0.1 type, which requires a numeric version.

After wiring, sample request/plan/receipt are in `handoff/examples/proposed-agent-exchange.json`. Refresh context from the controller after each committed action and before each new turn. Use a small deterministic capability-availability function; do not ask the LLM whether a button should be enabled.

## 5. Proposed Agent → UI action contract (for discussion)

Reference types are in `handoff/agent-ui-contracts.ts`. This packet recommends keeping a reply and an optional action plan as separate response fields. The reply describes intent (“Mình sẽ mở Tủ đề”), while a later execution acknowledgement supports completion (“Đã mở Tủ đề”).

### Execution rules

1. Parse and runtime-validate the entire envelope and every action against the versioned registry. Reject unknown keys, arbitrary targets, excessive actions (MVP cap: 5), mismatched session IDs, and unsupported schema versions. TypeScript alone is insufficient.
2. Deduplicate by `(sessionId, planId, actionId)`; return the prior receipt for a replay. Persist the ledger for the supported retry lifetime; a process-local map alone cannot guarantee exactly-once behavior across reloads/restarts.
3. Check `expectedStateVersion` once at plan entry against a fresh snapshot. Bind explicit workspace IDs; never substitute the current active exam for a missing target.
4. Execute actions serially. After each action, recheck existence, availability, permissions, and relevant target revisions against current state. A navigation render must settle before a dependent UI operation. Don't compare every following action to the plan's original stateVersion, because earlier plan actions legitimately changed it.
5. Keep a UI interaction epoch: teacher navigation/selection during execution invalidates the remaining stale operations. An in-flight backend effect may already have happened; return its actual receipt and skip remaining actions. A UI cannot undo a started backend job by dropping its reply.
6. Stop at first failure or `pending_user_confirmation`; report prior successes and remaining actions as skipped. Plans are not transactions: no automatic rollback of a successful navigation or started job.
7. A navigation receipt is successful only after the intended screen/session is observable in committed UI state. A closed/hidden tab may delay visual focus; don't report successful focus before applying it.
8. `exam.generate` succeeds only when the backend start call confirms a job ID. Return that ID and bind it to the originating session. A timeout after POST is an **unknown start outcome**; resolve by idempotency key/job lookup before retrying, rather than launching another job.

### Stable proposed errors

| Code | Meaning / recommended behavior |
|---|---|
| `UNSUPPORTED_SCHEMA` / `UNKNOWN_CAPABILITY` | Reject; request compatible protocol or supported action. |
| `INVALID_PARAMS` | Do not coerce unknown IDs or drop extra keys silently. |
| `STALE_CONTEXT` | No new effect; return fresh context and let agent re-evaluate. |
| `SESSION_NOT_FOUND` / `QUESTION_NOT_FOUND` | Target was deleted/does not belong to this session; clarify. |
| `CAPABILITY_UNAVAILABLE` / `PERMISSION_DENIED` | No effect; explain supported alternative. Current app has no auth/roles, so do not invent them in the snapshot. |
| `CONFIRMATION_REQUIRED` / `CONFIRMATION_EXPIRED` | Show/reissue exact normalized request summary. |
| `JOB_ALREADY_RUNNING` | Return existing job reference; don't start another. |
| `BACKEND_VALIDATION_FAILED` | Preserve collected slots; ask only for necessary corrections. |
| `BACKEND_UNAVAILABLE` / `START_OUTCOME_UNKNOWN` | Preserve user text; expose retry/resolve state accurately. |
| `ACTION_FAILED` | Unexpected UI failure; record action ID, retain truthful receipt. |

### MVP and deferred actions

Five initial definitions are in `ui_capabilities.json`. They are disabled until an executor exists. `exam.generate` additionally depends on backend validation, approval binding, and a reliable start receipt.

Deferred capabilities (NOT registered/enabled): `question.highlight`, `question.open_editor`, `question.regenerate`, `canvas.set_view`, `workspace.set_mobile_pane`, `library.set_filter`, `exam.export`, `exam.cancel`, `session.delete`, generic `panel.open`. Existing local controls may support some behavior, but an externally callable contract still needs explicit work. Avoid a generic panel action that can open any arbitrary component.

## 6. Capability registration format — UI/UX contribution

`ui_capabilities.json` is a static versioned registry with JSON Schema parameter definitions and semantic target enums. It includes implementation status, source paths, runtime availability gates, confirmation policy, and receipt expectations.

- `behaviorStatus` describes existing application behavior.
- `executorStatus=PROPOSED` and `advertiseToAgent=false` mean the action is not callable today.
- After implementation, enable only capabilities whose handlers, validation, and availability checks are actually installed. Build `screenContext.availableActions` from that enabled registry and current UI state.
- Dynamic conditions such as “session exists” are code checks, not JSON Schema alone.
- Use set-style operations (`set_collapsed {collapsed:true}`), not ambiguous toggles, so replay does not invert the state unexpectedly.
- Semantic `target` IDs are protocol names, not DOM IDs. `main-navigation` happens to be an actual nav ID; others need no matching HTML ID.
- Session creation returns `workspaceSessionId`; the agent cannot invent it. If a later action needs that returned ID, obtain a follow-up plan after the receipt. No string interpolation or `$lastResult` syntax is supported in v0.1.

The packet supplies a proposed adapter signature, not a hidden working executor. Friend can build against mocks now; UI implementation remains a separate integration task.

## 7. Progress events and division of responsibility

See implementation status for exact `GenerationProgress`, mock behavior, endpoint table, and current store algorithm. The real API adapter exists, but real streaming has not been exercised here.

### Current event example

`handoff/examples/progress-event.json` uses the exact current type and a complete illustrative question, not a captured live backend event. EventSource currently listens to unnamed `message` events; a backend that emits only named `event: question.updated` messages will not reach that listener without adapter changes.

### Recommended protocol upgrade, requiring backend agreement

- Add explicit `jobId`, run ID, monotonic `eventId`/sequence and event kind (`progress`, `question.upsert`, `completed`, `failed`, `cancelled`). Keep the current consumer compatible only through an explicit adapter/version.
- Upsert question items by ID and revision; ignore older revisions and duplicate event IDs. Preserve display order independently of arrival order.
- Add terminal failures/cancellation and network-disconnected/unknown states; don't overload `percent=100` to mean every outcome.
- Define reconnect replay window, Last-Event-ID behavior, authoritative job-status lookup, final package readiness, and behavior when replay is unavailable. Native EventSource reconnect is not this contract.
- Backend determines content status. UI never promotes PENDING/FLAGGED to VERIFIED because an LLM says “done.” Completion may still contain flagged questions needing teacher review.
- UI stores the latest compact progress snapshot. Agent reads it on demand; no LLM call per event.
- Auth/CORS and transport remain integration decisions: current EventSource has no custom headers or explicit credentials; do not assume bearer-token SSE works unchanged.
- Export “success” means a response/download has been initiated or verified according to adapter capability, not that Word opened or the teacher saved a file. Current `window.open` cannot verify either.

## 8. Questions we need to settle together (reply inline)

| Decision | UI recommendation / current fact | Owner / status |
|---|---|---|
| Source of truth for screen state | Current App local state + ExamSessions; lift view state into one React UI controller, retaining session store for exam data. Avoid a second competing router/store. | UI / PROPOSED |
| Executor location | React-side `src/integration/uiController.tsx`, pure validators/registry adapter alongside it. Components expose typed props/refs. | UI / PROPOSED |
| Chat transport | Start with REST JSON turns + execution-result feedback; exam progress stays SSE. Add assistant-text streaming only after semantic tool/result lifecycle works. Endpoint names in types are illustrative. | UI + agent / PROPOSED |
| Required exam inputs | Backend versioned schema + validation endpoint/adapter; exact endpoint/schema provider not available in current code. Do not derive mandatory fields from QuickPresetModal. | Backend / REQUIRED AGREEMENT |
| Generation caller | UI generation adapter is the sole starter, preserving existing store/progress ownership; agent proposes one approved action. Alternative backend-orchestrator ownership would require an explicit attach-to-existing-job API and disabling UI start. Do not mix both. | All / PROPOSED |
| Progress rendering | UI consumes backend events directly; add stored job snapshot/error callbacks. | UI + backend / existing mechanism PARTIAL |
| Errors | Inline agent-turn error + retry retaining text; job failure in workspace; structured action receipts. One assistant message per real event, not two conflicting acknowledgements. | UI + agent / PROPOSED |
| Confirmation/cancel | UI summary bound to validated request; UI approve/edit/cancel events update pending request state. “Hủy” before start discards draft approval; after start requires separate supported backend cancel. | All / PROPOSED |
| Conversation vs workspace | Separate IDs for global helper; explicit origin workspace per turn. Workspace-only MVP may map one-to-one but must document that choice. | UI + agent / PROPOSED |
| Retraction/branching | Initially keep current message controls from mutating agent memory until a versioned fork/truncate protocol exists; expose clear behavior. | UI + agent / REQUIRED AGREEMENT |
| Concurrency | Allow separate exam jobs per workspace, serialize turns per conversation, deduplicate requests; reject stale targeted writes. Generation must not disable informational helper questions. | All / PROPOSED |
| Persistence/auth | None today. Decide supported reload/reconnect lifecycle and actor ownership before claiming durable execution or cross-user isolation. | All / OPEN |

## 9. Concrete handoff requested from UI/UX

Delivered:

1. `UIUX_IMPLEMENTATION_STATUS.md`: audited implementation, exact snapshot, run/check results, service contract, gaps, and pitfalls.
2. `ui_capabilities.json`: five typed capability proposals with availability gates and sources.
3. `handoff/agent-ui-contracts.ts`: reference request/response/context/action/result/confirmation interfaces, explicitly not runtime code.
4. `handoff/examples/current-screen-context.json`: honest current-derived snapshot; no pretend executor/stateVersion.
5. `handoff/examples/proposed-agent-exchange.json`: a complete proposed navigation request, plan, result, and feedback envelope.
6. `handoff/examples/progress-event.json`: full current-shape event fixture.
7. `handoff/AGENT_INTEGRATION_ACCEPTANCE.md`: implementation sequence, Vietnamese interaction examples, integration/failure checks, and remaining backend questions.
8. `handoff/examples/generation-confirmation.json`: proposed approval binding and one-job start lifecycle, with explicitly fictional backend validation/hash values.

No new React runtime integration, backend endpoints, or production capability availability is claimed by these deliverables. No commit/push performed for this handoff.

## 10. My commitments back to UI/UX

The requested agent-side commitments are suitable. Please return:

- Proposed schema/endpoint versions, runtime validators, and the actual backend requirements provider, including unknown/unsupported values and semantic-validation errors.
- A mock agent adapter that consumes these semantic contexts/capabilities and returns typed plans, plus a feedback endpoint or adapter method for receipts.
- Explicit agreement on generation ownership, request/plan/action idempotency, approval binding, and unknown-start recovery.
- Tests for slot filling using backend requirements, unsupported/unavailable actions, stale and ambiguous references, multi-session races, and execution feedback before claiming completion.
- A memory policy for branch/retract/reload and file references; no hidden coupling to the frontend's visible chat array.

Suggested freeze: agree on the five capability definitions and reference types, implement/mock the UI executor and confirmation path, then enable only handlers that pass the acceptance suite. The first real integration should clarify an incomplete request, preserve the conversation across replies, approve a normalized request, start exactly one job, and render backend progress without involving an LLM in every event.
