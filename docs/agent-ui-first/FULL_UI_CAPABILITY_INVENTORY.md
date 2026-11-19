# Full UI capability inventory

Source baseline and feature HEAD are recorded in `INPUT_TO_ACTION_ROOT_CAUSE.md`. Scope: reachable controls in `App.tsx`, not standalone legacy components absent from the application tree.

| UI function | Existing handler/component | Agent binding | Preconditions / effect |
|---|---|---|---|
| Start/workspace navigation | App newExam/openSession | ui.navigate | valid destination/session; observed screen |
| New workspace | ExamSessions.create | ui.session.create | custom/template; new identity observed |
| Select workspace | App openSession | ui.session.open | existing identity |
| Delete workspace | ExamSessions.remove | ui.session.delete | explicit bound confirmation; session absent |
| Sidebar collapse | setControlsCollapsed | ui.sidebar.set_collapsed | boolean; observed state |
| Open setup/catalog | QuickPresetModal/getExamFormats | ui.exam.open_setup | catalog readiness awaited |
| Close setup | closeQuickModal | ui.exam.close_setup | modal open; closed state |
| Format/instruction draft | QuickPresetModal + setupState | ui.exam.configure_setup | available catalog format; visible selection/instructions |
| Generation submit | ExamSessions.generate | exam.generate.start | teacher confirmation, no active job; actual job ID |
| Generation status | ExamSessions progress | read-only Agent context | actual stage/percent; no invented per-question stream |
| Paper/answers/PDF | setViewMode / ExamPaperView | ui.exam.view_mode | real exam; review reveals answers |
| Question focus | ExamPaperView selected ID | ui.question.focus | actual question; preserve view |
| Open editor | QuestionEditor | ui.question.open_editor | real job/question |
| Fill editor fields | controlled QuestionEditor draft | ui.editor.fill | open editor; allowed patch fields |
| Save draft | examService.updateQuestion | exam.editor.save | bound confirmation; revision increases |
| Regenerate question | examService.regenerateQuestion | exam.question.regenerate | bound confirmation; revision increases |
| Close editor | setEditor(null) | ui.editor.close | no save |
| Preview retry | ExamSessions.requestPreview | exam.preview.retry | complete exam; request receipt (not proof of PDF success) |
| Approve | approveExam/store.canApprove | exam.approve | matching viewed PDF, revision/hash, explicit confirmation |
| PDF/LaTeX/answer JSON export | downloadExport | exam.export.download | approved artifact and explicit confirmation; dispatch receipt, not proof of OS save |
| Composer/suggestion draft | ExamSessions.setDraft | ui.chat.draft | workspace; observed draft |
| Branch chat | branchAtMessage | ui.chat.branch | actual message ID; new workspace |
| Retract chat | retractMessage | ui.chat.retract | user-message identity, confirmation |
| Note create | addNote | ui.note.add | generating/complete exam; deduplicated identity |
| Note edit | updateNote | ui.note.update | pending note; resets approval |
| Note cancel | cancelNote | ui.note.cancel | pending/approved/failed note |
| Note approve | approveNote | ui.note.approve | completed exam; prepares revision confirmation |
| Note apply | applyNote | exam.note.apply | matching confirmation; existing individual revision service |
| Cancel Agent task | cancelAgentTask | ui.task.cancel | cancels confirmation, not running generation |
| Prepare consequential action | React pendingConfirmation | ui.action.prepare | exact allowlisted action/params and revision binding |

Additional adapters: `ui.chat.copy` invokes the existing clipboard API pattern; `ui.chat.restore` restores actual message text with `setDraft`; `ui.details.set_expanded` controls question solution/TikZ and source-warning disclosure groups through React state.

Coverage accounting: 31 UI operation families with executable adapters (view modes and export variants grouped); 1 additional read-only progress family; 1 remaining external-tab interaction family. Among 32 executable UI families, 31/32 = **96.9% exposed**. This is adapter coverage, not a claim that all adapters have browser acceptance coverage.

Remaining control family: PDF/log new-tab links still require a user click. Asynchronous model responses cannot guarantee browser popup permission; the existing PDF pane is Agent-accessible. Disclosure adapters currently expand groups rather than a specific individual details element. Clipboard success means the browser acknowledged writeText, not independent OS readback.

Absent product operations: Backend generation cancellation, Word/DOCX, V-ACT setup, web search, uploads. Disabled controls are not counted as implemented capabilities. Unmounted ConfigView/ReviewView/ExportModal are not additional reachable workflows.
