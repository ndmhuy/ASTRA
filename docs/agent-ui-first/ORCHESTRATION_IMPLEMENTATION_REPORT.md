# Orchestration Implementation Report

Date: 2026-11-19. Branch: `feat/agent-ui-first-merge`. Verified merged baseline: `origin/merge-mas-and-uiux` at `8f12fbb2e9c7b6adb43b20b1966b256da6f45586`; implementation started from feature HEAD `e956c746d8e5fa8695801eb25e9f506227d34680` (baseline ancestor, 8 commits ahead).

## Operational result

The Agent can now return a typed plan of up to four UI actions. React owns execution: `AgentTaskController` re-captures context before each action, the default-deny executor validates the current state, invokes an existing React/store handler, waits for settlement, and records the observed receipt. Tasks are persisted per `ExamSession`; duplicate actions, stale state, partial failure and loops stop safely.

Source evidence:

- Task state and receipts: `astra-frontend/src/agent/contracts.ts`; bounded controller: `orchestrator.ts:10-145`.
- Registry and preconditions: `capabilities.ts:13-161`; executor freshness/effect checks: `executor.ts:22-62`.
- Compact live context and handler wiring: `App.tsx:158-296`; turn/confirmation continuation: `App.tsx:299-359`.
- Existing UI-owned generation remains `ExamSessions.generate` -> `IExamService.startGeneration`; the Agent service has no Backend client.

## Implemented teacher workflows

1. Multi-step navigation/setup: workspace creation/opening, real setup modal, real catalog state, configuration draft and explicit resumable confirmation.
2. Generation start: only `exam.generate.start` with the matching pending confirmation invokes the existing React `store.generate`; concurrent jobs remain rejected by the store.
3. Exam navigation: paper/review/PDF mode, question focus and existing editor opening.
4. During-generation notes: add/update/cancel/deduplicate; associate workspace/job and later exam/revision/stable question identity.
5. Deferred revision: teacher approves a note, then separately applies it through existing one-question `regenerateQuestion`; the store refreshes and requires an observed higher revision before marking it applied.

## Gemini integration

`GeminiPlan` is a schema-bounded list of 1-4 decisions. React still validates every returned action. Each SDK attempt is bounded to 15 seconds, one retry is allowed only for selected 5xx statuses, and the total budget is 32 seconds. Output is capped at 900 tokens and sanitized errors distinguish timeout, transport, request rejection, auth, model access, quota, local SDK and upstream errors. Mandatory Gemini mode remains fail-closed; offline mode remains labelled offline. Live verification was later authorized and passed for Agent interpretation and one complete 22-question Backend job; see `AI_PROVIDER_EXECUTION_AUDIT.md`.

## Verification

- Frontend: 20 tests passed; `npm run lint` passed; production build passed (existing >500 kB chunk warning).
- Agent: 36 focused tests passed using offline/fake SDK boundaries.
- Runtime: Vite and Agent health returned HTTP 200. Backend was not reachable in the current shell because the documented `.venv-win` interpreter is absent; no generation was attempted.
- Browser DOM automation was not available, so new visual behavior is implemented but not browser-verified.

No Backend business-core file was modified. No key was read or printed. No push or merge was performed.
