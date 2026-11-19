# Capability Coverage Matrix

| User-visible function | React/store handler | Backend dependency | Preconditions | Result |
|---|---|---|---|---|
| Create/open workspace | `App.openSession`, `ExamSessions.create` | none | valid mode/id | **IMPLEMENTED AND VERIFIED** |
| Open/close setup | `setShowQuickModal` | catalog only | current workspace for configuration | **IMPLEMENTED AND VERIFIED** |
| Read/fill setup | `QuickPresetModal`, `getExamFormats` | `GET /api/exam-formats` | catalog ready; available format | **IMPLEMENTED AND VERIFIED** offline with tests/build; live catalog not rechecked this run |
| Confirm/start generation | `App` -> `ExamSessions.generate` | existing generation API | matching confirmation, setup ready, no active job | **IMPLEMENTED BUT NOT LIVE-VERIFIED** |
| Read progress | `ExamSessions` progress state | existing SSE/polling | active job | **IMPLEMENTED AND VERIFIED** with fixtures |
| Paper/review/PDF view | `setViewMode` | preview uses existing API | exam required for review/PDF | **IMPLEMENTED AND VERIFIED** by build/contract tests |
| Focus question | `setSelectedQuestionId`, `ExamPaperView` scroll | none | actual question id | **IMPLEMENTED BUT NOT LIVE-VERIFIED** visually |
| Open question editor | existing `QuestionEditor` | none until save/regenerate | real job/question | **IMPLEMENTED BUT NOT LIVE-VERIFIED** |
| Add/update/cancel note | `ExamSessions` note ledger | none | generating job for add | **IMPLEMENTED AND VERIFIED** |
| Approve/apply note | `approveNote` / `applyNote` | existing single-question regenerate | complete, unapproved exam, matching revision confirmation | **IMPLEMENTED AND VERIFIED** with fake service; live provider not run |
| Preview/approval/export | existing controls | existing APIs | preview/revision/hash/approval gates | **PARTIAL**: visible to Agent context, deliberately not Agent-callable |
| Word/DOCX, V-ACT, upload, web search | no existing safe UI handler | missing | n/a | **UNSUPPORTED** |
| Direct Agent -> business Backend | none | prohibited | n/a | **UNSUPPORTED** by design |

All callable entries are declared in `astra-frontend/src/agent/capabilities.ts`; absent identifiers default-deny.
