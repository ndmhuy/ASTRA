# Current capability inventory — bb7f59e

This inventory starts from reachable JSX, stores and server routes. Agent exposure is a separate column. Locations are source evidence, not proof of live model accuracy. Runtime verification is described in `CURRENT_REAL_APP_AUDIT.md`.

## Reachable React application

| Function / actual handler | State/service and observable outcome | Agent exposure | Classification and availability |
|---|---|---|---|
| Welcome enter/timer, `AstraWelcome.tsx:7`; App showWelcome | local welcome dismissal | no dedicated action | ACTUALLY IMPLEMENTED local gate |
| Landing detailed/template/chat, `App.tsx:114/:121/:122`; WorkspaceStart | create workspace or open setup; chat goes to Agent | create/open_setup/navigate | ACTUALLY IMPLEMENTED; natural-language inference NOT VERIFIED now |
| New/select workspace, App newExam/openSession `:81/:82`, SidebarExamLibrary `:31` | browser store create/select | ui.session.create/open, ui.navigate | ACTUALLY IMPLEMENTED; create/open fixture-tested |
| Delete local workspace, Sidebar confirmation -> `ExamSessions.remove/:207` | removes local record, unsubscribes; Backend job retained | ui.session.delete with prepare | UI_ONLY persistence boundary; no server deletion |
| Sidebar resize/collapse, App controls state | layout state | ui.sidebar.set_collapsed | ACTUALLY IMPLEMENTED |
| Setup catalog/options/instruction/count display, `QuickPresetModal.tsx:55/:121/:126` | current Backend catalog plus unavailable frontend V-ACT; form draft | ui.exam.open_setup/close_setup/configure_setup | THPT ACTUALLY IMPLEMENTED; V-ACT UI_ONLY placeholder; latest Chrome setup passes |
| Start setup generation, App handleQuickStart `:122`, store.generate `:345` | job ID, generating state, subscription | exam.generate.start | ACTUALLY IMPLEMENTED with teacher confirmation; no current live run |
| Editable additional instructions | setup.prompt, max 1000 UI chars; Backend accepts 10000 | configure_setup | ACTUALLY IMPLEMENTED; preferences not domain guarantees |
| Chat send/draft/suggestions, `ModernChatBar.tsx:40`, App `:378` | user message appended, Agent response/receipts, composer state | ui.chat.draft and conversational turn | ACTUALLY IMPLEMENTED; send is not recursive Agent execution |
| Copy/restore/retract/branch chat, `ChatHistory.tsx:40/:54`, store `:214/:215/:221` | clipboard acknowledgement; composer; local messages truncated; new draft branch | ui.chat.copy/restore/retract/branch | ACTUALLY IMPLEMENTED; retract requires Agent confirmation; branch is conversation-only, not cloned exam |
| In-flight turn disabling | agentBusy in App/ModernChatBar | local behavior | ACTUALLY IMPLEMENTED; no distributed request lock |
| Progress/stage/error notification | store.watch `:380`, real status API/SSE | read-only activeJob | ACTUALLY IMPLEMENTED coarse progress; per-question stream MOCK_ONLY |
| Paper/answer/PDF tabs | App viewMode, ExamPaperView; QuestionCard answer/review display | ui.exam.view_mode | ACTUALLY IMPLEMENTED; answer/paper fixture-browser proof |
| Select/focus actual question | App selectedQuestionId; ExamPaperView focus effect | ui.question.focus | ACTUALLY IMPLEMENTED via adapter; fixture-browser proof |
| Solution/TikZ/native details and warnings | QuestionCard details; App warning text translation/disclosures | ui.details.set_expanded groups | ACTUALLY IMPLEMENTED group adapter; individual toggle stays native; broad receipt is handler acknowledgement |
| Question editor open/close | App editor, QuestionEditor draft | ui.question.open_editor, ui.editor.close | ACTUALLY IMPLEMENTED when real question/job exists |
| Edit stem/choices/key/statements/solution | QuestionEditor controlled draft, App patch allowlist | ui.editor.fill | ACTUALLY IMPLEMENTED; adapter does not expose every text-length constraint as formal JSON Schema |
| Save question | QuestionEditor onSave -> updateQuestion -> refresh | exam.editor.save | ACTUALLY IMPLEMENTED after confirm; Backend schema validates, approval invalidated |
| Regenerate question | QuestionEditor onRegenerate -> regenerateQuestion | exam.question.regenerate | ACTUALLY IMPLEMENTED; costly, bounded roles, current live operation NOT VERIFIED |
| Note add/edit/cancel/review | AgentNotes, store `:264/:287/:294` | ui.note.add/update/cancel | UI_ONLY ledger; fixtures verify lifecycle |
| Note approve/apply | store `:301/:321`; App onApply `:498` | ui.note.approve, exam.note.apply | PARTIAL binding/idempotency/refresh issues; actual single-question Backend service |
| Preview auto-request/retry/poll | store.complete `:662`, requestPreview `:412`; ExamPaperView | exam.preview.retry, pdf view | ACTUALLY IMPLEMENTED when compiler exists; request receipt does not imply compile success |
| View PDF, open new tab, compiler log | iframe and anchors in ExamPaperView | PDF pane callable; anchors manual | ACTUALLY IMPLEMENTED if matching artifact exists; popup/log operations not independently Agent bound |
| Approve current exam | CanvasHeader -> App approve `:139` -> store.canApprove `:173` | exam.approve with prepare | ACTUALLY IMPLEMENTED UI gate; Backend gate is weaker |
| Download student PDF/LaTeX and teacher JSON | CanvasHeader, App `:130`, ApiExamService.downloadExport `:659` | exam.export.download | ACTUALLY IMPLEMENTED for approved revision; no DOCX or matrix export route |
| Prepare/confirm/cancel Agent operation | App `:269/:395/:583`; store.cancelAgentTask `:258` | ui.action.prepare, ui.task.cancel | PARTIAL: specific params/revision for generic actions, weaker generation/note binding; cancel does not abort running async call |
| Avatar/session label and decorative art | App/header | none | UI_ONLY static; no account/settings implementation |
| Attachment/web controls | ModernChatBar disabled controls | unsupported manifest | MISSING actual upload/search; not working controls |

Legacy `ConfigView`, `ReviewView`, `ExportModal`, `OnboardingFork` and older navigation components exist in source but are not mounted by current App. Their forms/format choices are **UI_ONLY / not reachable in the current product**, and must not inflate supported scope.

## Every business HTTP route family

| Actual route | Function/location | Status |
|---|---|---|
| GET `/`, `/health` | routes_baseline.py:24/:29 | ACTUALLY IMPLEMENTED docs redirect/service metadata |
| POST `/v1/exams/generate` | routes_baseline.py:39 | BACKEND_ONLY generic one-call matrix/bank JSON service; not UI job endpoint |
| POST `/v2/exams/generate` | routes_pipeline.py:30 | BACKEND_ONLY generic four-agent pipeline; synchronous response with LaTeX/human-inspection headers or report |
| GET `/api/health` | routes_ui.py:25 | ACTUALLY IMPLEMENTED configuration/compiler summary, not inference proof |
| GET `/api/exam-formats` | routes_ui.py:37 | ACTUALLY IMPLEMENTED returns only THPT resource |
| POST `/api/exam-formats/evaluate` | routes_ui.py:42 | BACKEND_ONLY validates THPT/native matrix without model calls |
| POST `/api/exams/generate` | routes_ui.py:54 | ACTUALLY IMPLEMENTED idempotency key, durable job receipt, async THPT |
| GET `/api/exams/{job_id}/status`, `/events` | routes_ui.py:63/:68 | ACTUALLY IMPLEMENTED snapshots/SSE, UUID job identity |
| GET `/api/exams/{job_id}` | routes_ui.py:92 | ACTUALLY IMPLEMENTED completed teacher package incl. answers |
| PUT `/api/exams/{job_id}/questions/{question_id}` | routes_ui.py:97 | ACTUALLY IMPLEMENTED revision-checked edit |
| POST `/api/exams/{job_id}/questions/{question_id}/regenerate` | routes_ui.py:104 | ACTUALLY IMPLEMENTED revision-checked repair, no mutation idempotency token |
| POST `/api/exams/{job_id}/approve` | routes_ui.py:111 | ACTUALLY IMPLEMENTED revision/hash/source validation, no authenticated identity or viewed-preview requirement |
| POST/GET `/api/exams/{job_id}/preview` | routes_ui.py:116/:131 | ACTUALLY IMPLEMENTED start/status; exact revision/content hash |
| GET `/api/exams/{job_id}/preview.pdf`, `/preview.log` | routes_ui.py:143/:160 | ACTUALLY IMPLEMENTED revision-bound files |
| GET `/api/exams/{job_id}/export` | routes_ui.py:171 | ACTUALLY IMPLEMENTED supported type/format pairs only |

No UI-job list/delete/cancel/resume route, server workspace/chat/note endpoints, V-ACT UI generation route, CUSTOM_RANDOM route, auth/tenant management, question-bank CRUD, search/upload endpoint was found in mounted routers. These are **MISSING**, not unnamed existing APIs.

## Other Backend implementations and mocks

| Implementation | Source | Classification / limit |
|---|---|---|
| Native THPT generation and checkpoint resume | thpt/orchestrator.py:87; thpt/cli.py:19/:37 | ACTUALLY IMPLEMENTED domain path; resume exposed through CLI, not UI jobs |
| Native V-ACT 120-question multi-batch workflow | vact/orchestrator.py:11/:50; vact/models.py:31; vact/cli.py:8 | BACKEND_ONLY; tests prove schema/rendering policy, not live exam quality |
| Generic matrix, bank reuse, custom constraints | core/models.py:65/:152/:194; core/validation.py:39 | BACKEND_ONLY reusable contracts, not deterministic random assembly |
| Mini draft, raw materials/bank input, fixture replay | draft/cli.py:32; draft/composer.py | BACKEND_ONLY draft workflow; fixture mode MOCK_ONLY; not approved UI export |
| Baseline evaluation/reporting, benchmark suites | baseline/evaluation.py, reporting.py; benchmarks/; pipeline/benchmark.py | BACKEND_ONLY measurement tooling; no teacher analytics UI |
| Pinned RAG release, scoped evidence assembly | ui/jobs.py:112/:178; intake.py: encode_thpt_retrieval; rag_workflow/matrix_retriever.py | ACTUALLY IMPLEMENTED THPT path; frontend cannot curate or upload corpus |
| Provider HTTP adapter | providers/chat_completions.py:14 | ACTUALLY IMPLEMENTED transport; runtime quota/model success NOT VERIFIED this audit |
| Optional persistent cost reservation | providers/budget.py:14 | ACTUALLY IMPLEMENTED when explicitly configured; local estimate, no provider-account quota query |
| Mock provider and MockExamService | providers/mock.py; examService.ts:244 | MOCK_ONLY simulated questions/stages/edits/exports; explicit VITE_SERVICE_MODE selection |
| Offline Agent rules | astra_agent_ui/interpreter.py:61/:304 | MOCK_ONLY natural-language demo subset; output labelled offline; not Gemini-powered |
| Approved Application Knowledge source class | astra_agent_ui/knowledge.py:32 | PARTIAL future contract; not automatically installed/loaded by App; approved document absent |

## Agent exposure truth

The registry currently contains 32 callable IDs (including task/confirmation infrastructure), but this is **not** a percentage of all product functions. `capabilityCatalog` (`capabilities.ts:220`) computes only some prerequisites; it may advertise an action as available despite closed editor/missing approval. `parameterSchema` is argument documentation using descriptive strings/arrays, not a complete machine-validated JSON Schema. Per-action React validators enforce only their implemented checks. Some effects use result booleans rather than independently observed state.

Natural-language reliability over all paraphrases and every capability category is **NOT VERIFIED** by this audit. Current browser tests inject typed proposals at the HTTP boundary and use the real React executor/handlers.
