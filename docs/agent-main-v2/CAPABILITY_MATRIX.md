# ASTRA Agent V2 capability matrix

For UI and API reviewers. Each registered semantic intent has an App adapter. The shared registry defines the typed arguments consumed by both language boundaries. Availability is checked against the live local view and session, with reachable actions resolved after a prior step succeeds.

- Registered intent adapters with a source binding: 34/34.
- Intent IDs observed in the mounted browser smoke: 18/34. The service fixture intercepts expensive exam HTTP. Setup catalog and evaluate use the real FastAPI handlers.
- The remaining 16 intent IDs have source bindings. Evidence for each scenario and its limits appears in [Acceptance results](ACCEPTANCE_RESULTS.md).

| Surface | Semantic intents | Handler owner | Availability |
| --- | --- | --- | --- |
| Workspace | HOME, CREATE_SESSION, OPEN_SESSION, LIST_SESSIONS, DELETE_SESSION, SET_SIDEBAR | App and SidebarExamLibrary | Active standalone workspace or local library. Delete and sidebar layout have state and confirmation gates. Recent lookup sorts by creation timestamp. |
| Setup | OPEN_SETUP, CLOSE_SETUP, SHOW_FORMATS, SELECT_FORMAT, FORMAT_DETAILS, PREPARE_GENERATION | QuickPresetModal, App, ExamSessions and ApiExamService | Draft or error. Catalog and actual evaluate endpoints. One explicit Start for the evaluated payload. |
| Canvas | STATUS, WARNINGS, SET_VIEW, FOCUS_QUESTION, FOCUS_SECTION, SCROLL_TOP | ExamSessions and ExamPaperView | Live stored job status or completed package. Question navigation uses stable ID and revision. Programmatic PDF navigation does not satisfy teacher review. |
| Editor | OPEN_EDITOR, CLOSE_EDITOR, PATCH_EDITOR, VERIFY_QUESTION, REGENERATE_QUESTION | QuestionEditor, App and ApiExamService | Completed package and unique question. Teacher saves the draft using the existing editor. Verify and regenerate ask for confirmation. V-ACT provides edit and verify. |
| Review and export | RETRY_PREVIEW, APPROVE, EXPORT | ExamPaperView, CanvasHeader and the existing API service | Retry requires a failed preview. Approval requires teacher review. Export requires current approval and matching PDF revision/hash. |
| Notes | ADD_NOTE, CANCEL_NOTE, REVIEW_NOTES, APPLY_NOTES | ExamSessions and the existing question operation | Job-bound notes. Stable mapping after completion. Applying notes is confirmed and bounded. THPT regeneration only. |
| Memory | RENAME, RECALL, CHAT_MESSAGE, SET_DRAFT | ExamSessions and the existing composer/ChatHistory | Local browser only. Named and numbered targets resolve from current state. Retract asks for confirmation. Clipboard permissions depend on browser and user activation. |

## Intake and guidance refinement

The semantic envelope also carries non-executable guidance and intake proposals. The mounted browser observed the current catalog supplying subject clarification and read-only structure, and the existing SELECT_FORMAT binding opening the real Toán THPT dialog on a follow-up. Topic evaluation continues to use PREPARE_GENERATION. These routes add no new executable IDs. [Acceptance evidence](MANUAL_ACCEPTANCE_V2.md)

## Browser-observed intent IDs

`OPEN_SETUP`, `OPEN_SESSION`, `SET_SIDEBAR`, `LIST_SESSIONS`, `SET_VIEW`, `STATUS`, `FOCUS_QUESTION`, `OPEN_EDITOR`, `APPROVE`, `EXPORT`, `SELECT_FORMAT`, `PREPARE_GENERATION`, `ADD_NOTE`, `CANCEL_NOTE`, `REVIEW_NOTES`, `RENAME`, `RECALL`, `PATCH_EDITOR`.

## Remaining product and browser limits

| Capability | Actual path and limit |
| --- | --- |
| Welcome splash, pane dragging, file picker, web toggle, PDF/log external tab, drawing details | Existing manual controls. A file selection or toggle has no supported upload/search service. Browser-gesture controls remain available through their native interaction. |
| Question save | Agent can prefill the existing editor using teacher-supplied text. The Save button or its existing keyboard shortcut commits the teacher-reviewed draft. |
| V-ACT question regeneration | Native API rejects it for this format. The question editor and verify action are available. |
| Word export, arbitrary random/custom generation, bank assembly, job cancellation | No matching integrated product route. |
| Job ownership across devices and account chat isolation | Native prototype has no authenticated tenant boundary. Browser-local generation uses Web Locks and store freshness checks. |

## Worker integration checkpoint, 2026-11-26

The new keyless Worker transport preserves the existing semantic compiler and product recipes. Nine local workerd security/quota groups, seven Python Worker contract cases, existing focused checks, frontend checks/build and mounted semantic-fixture regression passed. Independent dependency installation and UI/health/catalog startup passed in a fresh detached checkout without private .env. Production still returned Hello World. Deployment, project-approved model and real Agent acceptance remain pending. MAS public inference is absent until its Chat Completions academic contract and credential compatibility are verified. [Current gates](PROGRESS.md) ? [Deployment and rollback](WORKER_RUNBOOK.md)
