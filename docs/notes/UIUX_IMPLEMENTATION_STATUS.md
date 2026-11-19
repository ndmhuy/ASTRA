# ASTRA UI implementation status

Reviewed 2026-11-14. This is an audit of the checked-out code, not a declaration that the proposed agent interface is implemented.

## Snapshot and reproducibility

- Repository: https://github.com/ndmhuy/ASTRA.git
- Branch: `uiux`
- Reviewed commit: `c052b689ee487e6546d7bac6e32f63a6a88e9780`
- At review start, tracked working tree was clean. `01_UIUX_HANDOFF_REQUEST.md` was an untracked input. Handoff files are new, uncommitted documentation; they do not install an agent or executor.
- Entry: `astra-frontend/src/main.tsx` -> `App.tsx`; React StrictMode is enabled.
- Stack: React 19, TypeScript, Vite, KaTeX, Lucide, custom SVG illustrations. Exact dependencies and lockfile: `astra-frontend/package.json`, `package-lock.json`.
- Verified environment: Node `v24.14.1`. Earlier Node versions were not tested. No agent SDK/runtime is installed by this handoff.

From `astra-frontend`:

```powershell
npm ci
npm run dev
# Vite normally uses 5173; follow its printed URL if that port is occupied.
npm run build
npm run lint
node --experimental-strip-types --test tests/examSessions.test.mjs
```

Checks run against the reviewed application: build passed; all 6 existing tests passed; lint completed with 2 existing `no-useless-escape` warnings in `MathRenderer.tsx` and `examService.ts`. Build warns that the main JS bundle exceeds 500 kB. There is no `npm test` script. No agent integration or real backend was tested.

## Status vocabulary

`IMPLEMENTED`: reachable in the current app. `PARTIAL`: some building blocks exist, but integration or guarantees are missing. `PROPOSED`: designed in this packet, no runtime implementation. `NOT AVAILABLE`: absent from the current app. A method existing in a service does not make it an available agent capability.

## Current implementation inventory

| Area | Status | Exact source and behavior |
|---|---|---|
| Navigation | IMPLEMENTED | `src/App.tsx`: `screen: onboarding | workspace`, `homeTab: welcome | create | library`. No router, URLs, deep links, or browser-history navigation. Semantic screen IDs in the handoff are a proposed normalization. |
| Splash | IMPLEMENTED | `AstraWelcome.tsx`, controlled by `showWelcome`. Not a registered agent destination. |
| Left menu | IMPLEMENTED | `App.tsx`: labeled SVG menu buttons, `controlsCollapsed`, visible collapse/expand button. Collapsed state survives page changes in this mount, not reload. Mobile uses a top menu and hides the collapse control at <=760px. |
| Content framing | IMPLEMENTED | `styles/sidebar.css`: shared cream shell, inset content panel, restrained corner radii. Do not rewrite styling to integrate the agent. |
| Session creation/open | IMPLEMENTED | `state/examSessions.ts`: `create(mode)` returns a UUID; `App.tsx::openSession(id)` sets `activeId` and `screen`. Current helper does not validate the ID before setting state. Executor must validate it. |
| Session lifetime | IMPLEMENTED, memory only | `ExamSessions` is instantiated once by App and subscribed through `useSyncExternalStore`. Messages/questions/drafts survive navigation; reload/tab close loses them. No account identity or persistent storage. |
| Chat rendering | IMPLEMENTED | `Workspace/ChatPane/ChatHistory.tsx`: plain text, timestamps, copy, suggestions, message edit-to-draft, retract, branch. `system` messages are hidden. No rich confirmation card, action receipt, or streamed assistant response. |
| Chat submit | PARTIAL | `ModernChatBar.tsx::handleSend` -> `App.tsx::handleSendMessage(content)` -> `ExamSessions.sendMessage`. Store appends user message and a fixed assistant acknowledgement synchronously. No inference, intent parsing, slot filling, network call, or tool execution. |
| Chat outside workspace | NOT AVAILABLE | Composer/history mount only inside workspace. Navigating to home/library hides chat. A persistent global helper needs a shell-level controller/view. |
| Attachment selection | PARTIAL | Composer collects browser `File[]`, displays names/removal, sends them in the second callback argument, then clears the list. App accepts only text and ignores this argument. No upload endpoint, `fileId`, validation, or backend ingestion. |
| Web option | PARTIAL | Local composer toggle only; passed in ignored callback options. No search is performed. It must not be advertised as a working tool. |
| Quick setup | IMPLEMENTED, limited | `QuickPresetModal.tsx`: subject and one of two presets only. Grade is hardcoded to 12. THPT: 40 questions/50 minutes; DGNL: 30/40. `uploadedFiles=[]`. No prefill or arbitrary schema-driven confirmation. |
| Generation start | IMPLEMENTED UI flow | `App.tsx::handleQuickStart` closes dialog, opens a session, appends all existing user messages to the preset prompt, calls `store.generate(id, params)`. No agent approval token, request hash, or backend idempotency key. |
| Job/session isolation | IMPLEMENTED | Store callbacks close over originating session ID, not currently visible session. Existing tests cover concurrent jobs and late replies after deletion. |
| Duplicate start guard | PARTIAL | Store sets `status=generating` before awaiting start; a second start for that same session is ignored. This is not cross-client, durable, request-level idempotency. `generate()` resolves before job completion and returns no structured start receipt. |
| Progress transport | PARTIAL real adapter / IMPLEMENTED mock | `services/examService.ts::ApiExamService.onProgress` uses default EventSource `message` events. Mock emits timed stage callbacks. Real server compatibility/auth/recovery not verified. |
| Canvas | IMPLEMENTED | `ExamPaperView.tsx`, `QuestionCard.tsx`, `CanvasHeader.tsx`: streamed question preview, KaTeX, answer mode, warnings, export buttons after session complete. Answer mode is component-local `review`. |
| Mobile pane and resize | IMPLEMENTED local controls | `WorkspaceLayout.tsx`: local `mobilePane=chat|paper`; local width state plus ResizeObserver. Despite `left/right` slot names, current visual desktop order is paper LEFT, chat RIGHT. <=760px uses pane tabs. |
| Selection/focus/highlight | NOT AVAILABLE as semantic state | No `selectedQuestionId`, focused-component registry, selected exam question, or programmatic highlight action. QuestionCard labels use display index, not stable DOM target IDs. |
| Question edit/regenerate | PARTIAL / not reachable in current workspace | `EditQuestionModal.tsx` is used by legacy `ReviewView.tsx`. Current App does not mount ReviewView or pass `onEditQuestion` to ExamPaperView. Service methods exist, but store has no question mutation method. Do not expose editor/regeneration as working. |
| Export | PARTIAL | Current App exposes student exam and teacher key as `docx` when complete. API adapter calls `window.open`; no completion/error acknowledgement. Mock downloads plain text as `.doc` or `.txt`, not genuine DOCX/PDF. `MATRIX`/PDF service signatures do not imply current UI support. |
| Errors | PARTIAL | Start/final fetch rejection -> generic `session.error`, retry button, draft/error status. API adapter does not check `res.ok`; SSE has no surfaced error callback. Some failures can remain stuck in `generating`. |
| Cancellation | NOT AVAILABLE | Closing setup cancels setup only. Unsubscribe, deleting a session, and `dispose()` stop local updates; none cancel a real backend job. |
| Agent context/registry/executor | PROPOSED in handoff | No current runtime context exporter, version counter, semantic dispatcher, plan validator, action ledger, permission model, or execution receipts. New JSON/TS files are reference artifacts outside `src`. |

Paths in the table are relative to `astra-frontend/` unless starting with `astra-frontend`.

## Existing data contracts: keep these distinctions

Source: `src/types/exam.ts`.

```ts
interface ExamRequestParams {
  subject: Subject;
  grade: number;
  examType: ExamType;
  durationMinutes: number;
  itemCount: number;
  prompt: string;
  uploadedFiles: string[];
}
```

- `Subject`: `Tổng hợp`, `Vật Lý`, `Toán Học`, `Hóa Học`, `Sinh Học`, `Tiếng Anh`, `Lịch Sử`, `Địa Lý`, `GDCD / KTPL`.
- `ExamType`: `THPT_STANDARD | DGNL_DHQG | MID_TERM | CUSTOM`. Only the first two have quick setup controls.
- Question status: `PENDING | VERIFIED | FLAGGED`. There is no `DRAFT` question enum. A `draft` session is a different concept; do not translate all `PENDING` questions to already verified drafts.
- Question IDs are numbers scoped to an exam/session. Displayed “Câu 3” means index 2 in the rendered list; do not assume its `id` is 3.
- `QuestionItem` includes stem, A-D choices, key, explanation, level, topic, status, optional provenance and writer/solver audit. Read the type file for the full shape.
- `ExamSession.id` is a frontend workspace UUID. `jobId` is a service job ID. `ExamPackage.examId` is a different backend package ID; `complete()` currently does not retain that ID in the session.
- `uploadedFiles: string[]` has no agreed file-reference semantics yet. Do not send local filenames as if they were uploaded backend IDs.
- TypeScript is compile-time only. These interfaces are not the backend's authoritative required-input schema or runtime validators.

## Generation/progress reality

Current path:

```text
QuickPresetModal.onStart
  -> App.handleQuickStart
  -> ExamSessions.generate(workspaceSessionId, params)
  -> examService.startGeneration(params) -> {jobId}
  -> examService.onProgress(jobId, callback)
  -> store.questions + store.meta -> useSyncExternalStore -> Canvas
  -> stage>=5 AND percent>=100 -> getExamPackage(jobId)
  -> complete(sessionId, package) -> session.status=complete
```

Current progress type:

```ts
interface GenerationProgress {
  stage: number;
  stageName: string;
  percent: number;
  estimatedSecondsLeft: number;
  completedItems: number;
  totalItems: number;
  statusMessage: string;
  latestItemPreview?: QuestionItem;
}
```

The store saves counts and unique previews. It DOES NOT retain stage name, percentage, ETA, or status message. A duplicate preview ID is ignored, even when content/status differs; updates are not upserted. Final fetch replaces the entire question list. Counts can differ from the number of visible previews. The agent must not claim that `completedItems` equals the number already shown.

Mock specifics: 8 fixed Physics questions regardless of requested subject/count; metadata echoes the request. Five stage callbacks reveal only five individual previews; completion fetch supplies all 8. The simulation takes roughly 8.1 seconds. Synthetic stage 1 already includes a preview. A selected Toán subject does not generate authentic Math content in mock mode. Mock regenerate changes audit/status fields, not the question stem according to instructions. Treat all this as UI demonstration, not generation quality evidence.

API mode: `.env.example` documents `VITE_SERVICE_MODE=api`, `VITE_API_BASE_URL=http://localhost:8000/api`; default without configuration is mock. Restart Vite after changing env. The active user's private `.env` was not inspected; no claim is made about its current value.

| Method | Path under configured base URL | Current payload/result |
|---|---|---|
| POST | `/exams/generate` | `ExamRequestParams` -> `{jobId}` |
| GET | `/exams/{jobId}/events` | EventSource unnamed `message`; JSON `GenerationProgress` |
| GET | `/exams/{jobId}` | `ExamPackage` |
| POST | `/exams/{jobId}/questions/{questionId}/regenerate` | `{instruction}` -> `QuestionItem` |
| PUT | `/exams/{jobId}/questions/{id}` | `QuestionItem`; response ignored |
| GET | `/exams/{jobId}/export?type=...&format=...` | Opens new browser tab/window; real export unverified |

There are SIX endpoint patterns, notwithstanding stale comments saying four/five. Agent/chat endpoints, requirements discovery, uploads, job cancellation, and execution-feedback endpoints do not exist in this frontend adapter.

## Known integration pitfalls to address before enabling agent writes

1. Replace the synchronous placeholder assistant reply in `sendMessage`; don't append it alongside the real agent response. Add explicit user/assistant-message insertion and session-addressed async settlement.
2. Preserve composer options or explicitly mark them unavailable; don't silently tell teachers files/web were used.
3. Decouple agent turn loading from generation loading. Current composer is disabled throughout generation, so “Đã xong đến đâu?” cannot currently be sent during a job.
4. Store complete progress snapshots and terminal errors; introduce durable job/run identity before retrying. Old job callbacks/finally blocks must not mutate or unsubscribe a newer run of the same session.
5. Add `res.ok` checks, JSON runtime validation, EventSource errors/timeouts, and an explicit failed/unknown job state. Native EventSource auto-reconnect alone does not provide event ordering, replay, or successful recovery.
6. Do not feed concatenated transcript text into `prompt` on every confirmation. Preserve structured requirements separately and send one canonical approved request.
7. Branching currently copies `jobId`, questions, metadata, and error via shallow spread, while a generating branch is marked `draft` and gets no subscription. Before agent use, define whether a branch is a read-only snapshot or a fresh independent exam; never accidentally edit the source job.
8. Retracting truncates visible history but does not undo generation or reset agent memory. Editing puts text in the composer; it does not patch or replay an earlier backend turn. Synchronize explicit branch/retract semantics before exposing these to an agent.
9. Deleting a generating session hides it/stops subscription, but a backend job can continue. Do not describe deletion as cancellation.
10. Browser focus/scroll belongs inside the UI executor. Question targeting must be scoped to the right session, reveal the paper pane on mobile, wait for commit, then focus/scroll a registered ref.
11. React StrictMode is enabled. Never launch a job from mount effects; use confirmed event handlers and request-level idempotency.
12. `generate()` clears existing questions before start is accepted and does not initially clear the prior jobId. Restrict MVP generation to an explicitly approved draft/retry; retain run-specific identity and avoid destructive replacement of a completed exam.

## Test coverage and missing coverage

`tests/examSessions.test.mjs` covers concurrent job isolation, final-fetch failure/retry, duplicate starts/dispose, mock per-job edits, deletion during a job, and deletion before start resolves. These are store/service tests, not browser or agent integration tests. Some fake questions are deliberately incomplete and do not demonstrate runtime schema validation.

Missing automated coverage: semantic navigation executor, stale contexts, action schemas, confirmation binding/expiry, prompt injection through exam text, runtime API validation, reconnect/replay, actual agent turns, global helper UI, file upload, backend cancellation, selected-question focus, and accessible action receipts. Proposed acceptance cases are in `handoff/AGENT_INTEGRATION_ACCEPTANCE.md`.
