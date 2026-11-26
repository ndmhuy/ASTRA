# ASTRA Agent V2 baseline

For ASTRA implementers and reviewers. This records source and offline checks before the Agent changes.

- Fetched with `git fetch --all --prune`. Audited and fetched main both resolve to `7523c79556a9935df5008c92043f1e38d6e5d2a2`. Local main divergence was 0/0.
- Remote Agent reference `fb834b976cb62eb7292fa839cdaf1d8738e1ec50`, merge base `8f12fbb2e9c7b6adb43b20b1966b256da6f45586`, comparison 35 commits on main and 26 on legacy. Local comparison tips were `e17f055`, `52ebad6`, `afdbcd6`, and `c1fbac6`. Only the tracked source in the remote reference is a reuse input.
- Original checkout contains untracked engineering packs, frontend test results, and UI-first documents. Work proceeds from the verified main commit in a sibling worktree with an ignored marker and a copy of the pack.
- Node 24.19.0. `npm.cmd ci`, `npm.cmd test` (16 tests), lint, and production build passed. Vite reported the existing large chunk warning. Python 3.13.5 is available and in the repository CI matrix. Python baseline results are recorded in the progress ledger.
- FastAPI serves the dist bundle in native web mode. Vite proxies `/api`. Same-origin local web UI and backend use an existing SQLite job store and revision/hash guards. Existing app lacks account or workspace ownership enforcement. UI can resume observing a recorded job ID. A server restart causes interrupted jobs to fail. Atomic workspace admission across tabs is absent.
- Pinned Git RAG object is present. Main exam API source has THPT and V-ACT. No local model calls, provider verification, or secret file reads during baseline.

## Screen inventory at baseline

| Surface | Existing controls and entry points | Baseline limits |
|---|---|---|
| Start and welcome | `AstraWelcome` completion; `WorkspaceStart` template/detailed start and composer; `App.tsx:92` | Landing chat opens preset modal unconditionally |
| Sidebar | `SidebarExamLibrary.tsx:42` new, list/open, delete/cancel; `App.tsx:147` brand, sidebar collapse and edge | Browser-local sessions, no separate search/rename controls |
| Setup | `QuickPresetModal.tsx:33` health/catalog, select/expand, keyboard and close/start; `routes_ui.py:44` evaluate | Fixed counts and durations, asynchronous catalog |
| Draft/error | `App.tsx:172` setup/retry; `ModernChatBar.tsx:34` draft/send, IME, attachments, web toggle | Canned assistant reply; no accepted upload or search |
| Generation | `examSessions.ts:281` job watch, progress; `App.tsx:183` progress and warnings | Composer disabled, no platform cancellation or per-question generation stream guaranteed |
| Chat history | `ChatHistory.tsx:34` suggestions, copy, edit-to-draft, retract, branch | Browser clipboard permission and transcript lifecycle |
| Complete/paper/review | `ExamPaperView.tsx:324` paper, answer review, PDF, flagged list, section jump and top; question cards and review rows can open editor | Stable IDs and revisions must be resolved against the current package |
| Editor | `QuestionEditor.tsx:111` close; typed fields, instruction, save, regenerate, one-question verify | Revision-sensitive, inference for regenerate/verify |
| PDF/approval/export | `CanvasHeader.tsx:62` preview, approval, PDF/TEX/JSON; `ExamPaperView.tsx:287` retry and compiler log | Current revision/hash and preview ready gate PDF; ordinary preview open was used as approval prerequisite |
| API-only or absent | `routes_ui.py` provides validate/status/events/package and artifact operations. Job cancel, arbitrary formats, Word, upload and web search have no integrated product path. | Agent must use UI-owned service |
