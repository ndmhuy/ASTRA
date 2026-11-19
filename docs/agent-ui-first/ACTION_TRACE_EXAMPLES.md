# Agent Action Trace Examples

All IDs below are illustrative/redacted. Traces show the implemented protocol boundary; no private document content or key is included.

## 1. Successful real UI action — open drafting workspace

- Teacher: `Mở màn hình soạn đề`
- Input snapshot: `{screen:"start", workspaceId:null, stateVersion:1, activeJob:null}` with `ui.session.create` available.
- Agent proposal: `{kind:"propose_ui_action", capabilityId:"ui.session.create", actionId:"…", expectedStateVersion:1, params:{mode:"custom"}}`.
- UI validation: capability real/callable, schema valid, version current, no confirmation required.
- Execution: existing `ExamSessions.create('custom')` then `App.openSession(id)`.
- Receipt: `{status:"success", observedStateVersion:2, result:{workspaceId:"…"}}`.
- Response: `Tôi sẽ mở một workspace soạn chi tiết mới. Giao diện đã xác nhận thao tác thành công.`
- Evidence: `REAL_UI_PASS` in Chrome against the local service.

## 2. Ambiguous existing workspace

- Teacher: `Mở cái đề hồi nãy`.
- Snapshot: two session summaries, neither selected by the utterance.
- Agent decision: `{kind:"clarify", text:"Có nhiều workspace… Thầy cô muốn mở workspace nào?"}`.
- UI validation/execution: no proposal, no handler call.
- Receipt: none, because no action was attempted.
- Response: one grouped clarification listing up to four titles.
- Evidence: deterministic interpreter behavior; `UNIT_ONLY`.

## 3. Unsupported Word export

- Teacher: `Sửa câu 5 rồi xuất Word`.
- Snapshot: Word capability is `unavailable`; question-focus Agent action is unavailable.
- Agent decision: `unsupported` for Word. The interpreter does not begin the earlier mutation or silently substitute TeX/PDF.
- UI validation/execution: no proposal, no business request.
- Receipt: none.
- Response: current ASTRA does not support Word; verified formats are PDF, LaTeX and JSON subject to UI gates.
- Evidence: deterministic service test; `UNSUPPORTED_EXPECTED`.

## 4. Multi-step dependency stops safely

- Teacher: `Mở lịch sử rồi quay về trang đầu`.
- Snapshot: `ui.navigate` exists, but no verified history-screen action exists.
- Agent decision: `unsupported`, explicitly stating that the later step is not executed.
- UI validation/execution: zero handlers called.
- Receipt: none.
- Response: history is unavailable and the dependent navigation was not performed.
- Related executor test: when an opener handler fails, later planned receipts are `skipped / DEPENDENCY_FAILED`.
- Evidence: `UNIT_ONLY`.

## 5. In-generation deferred note

- Teacher: `Câu 3 sửa dễ hơn`.
- Snapshot: `{workspaceId:"…", activeJob:{id:"…", stage:"Đang soạn", source:"real"}, stateVersion:7}`.
- Agent proposal: `ui.note.add` with `{targetQuestion:3, requestedChange:"…", teacherText:"…"}`.
- UI validation: active job required; target is a positive display number; text is non-empty and <=500 characters.
- Execution: `ExamSessions.addNote` stores workspace/job identity and `pending` status in UI state only.
- Receipt: `{status:"success", observedStateVersion:8, result:{noteId:"…"}}`.
- Response: note is recorded for later review and has not changed the running exam.
- Evidence: interpreter plus UI-store tests; `UNIT_ONLY`, no live generation was launched.

## 6. Missing Gemini key in AI mode

- Teacher: an open-ended request not covered by deterministic commands.
- Snapshot: minimal UI state; no secret field; real capability descriptions only.
- Agent provider: Gemini mode with missing local key.
- Result: explicit HTTP 503 envelope with `gemini_missing_key`; no model decision is fabricated.
- UI validation/execution: no proposal and no UI mutation.
- Receipt: none.
- Response: Gemini AI mode requires a local key. Offline behavior is available only by explicitly selecting `AGENT_MODE=offline`.
- Evidence: service test for the explicit error; the earlier browser help/action run remains a `REAL_UI_PASS` for labelled offline mode only.

## 7. Stale or duplicate proposal

- Proposal A uses `expectedStateVersion:4`, but current UI capture is version 5.
- Receipt: `failed / STALE_CONTEXT`; handler is not called and the UI explains that state changed.
- Repeating a previously successful `actionId` returns the cached receipt with `duplicate:true`; no side effect repeats.
- Evidence: frontend executor tests; `UNIT_ONLY`.

## 8. Invented model action

- Fake Gemini output: `{kind:"propose_ui_action", capabilityId:"backend.deleteExam"}`.
- Agent post-validation: action is absent from the live callable registry.
- Decision returned to UI: `clarify`; invented capability is removed.
- UI executor independently defaults to deny and would return `CAPABILITY_UNAVAILABLE` if it received the proposal.
- Business Backend requests: zero.
- Evidence: Python and frontend guardrail tests; `UNIT_ONLY`.
