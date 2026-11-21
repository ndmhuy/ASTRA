# ASTRA — UI/UX & LaTeX Changes Summary

**Branch:** `feat/agent-ui-first-merge` (base `19950bf`)  
**Audience:** Teammates & coding agents continuing integration work.

## Sequential Commits

### 1. `0cd2713` — `feat(web): add V-ACT setup option and refine UI layout`
- **Left sidebar expanded:** Widened from `164px` → `216px` desktop (`192px` tablet, collapsed remains `58px`) in `astra-frontend/src/styles/createVision.css` and `integratedWorkspace.css`.
- **Setup modal (`QuickPresetModal.tsx`):**
  - Added **Tạo đề ĐGNL (V-ACT)** option (`id: "vact-dgnl"`, 120 questions, 150 min, 1200 pts, 3 sections) alongside **Toán THPT**. Marked `available: false` until backend wires V-ACT UI jobs (keeps Agent capability registry honest; `Tạo đề thi` stays disabled when V-ACT is selected).
  - Fixed modal layout glitch caused by `.workspace-active.create-mode > *` overriding `.setup-modal-backdrop` `position: fixed`; removed `backdrop-filter: blur` and `translate(-50%,-50%)` jitter; cached format list to avoid height jump on reopen.
- **Crisper visual polish:** Reduced excessive border-radius (`14px–18px` / `999px` → `3px–6px`), styled Agent confirmation toast (`App.tsx`) and `QuestionEditor` (`integration.css`).
- **PDF preview & RAG warnings:**
  - Compacted PDF preview status bar in `ExamPaperView.tsx` (`flex: 1; height: 100%` iframe so PDF fills the canvas).
  - Translated English RAG coverage warnings (`P2 topic pack(s)...`) into Vietnamese under **Lưu ý nguồn tham khảo** (`App.tsx`).
- **Verified:** `npm.cmd test` (22/22 passed), `npm.cmd run lint` (0 warnings/errors), `npm.cmd run build` (passed).

### 2. `24aac71` — `feat(data): add V-ACT format contract and official exam LaTeX headers`
- **Added V-ACT JSON contract:** `src/exam_baseline/resources/exam_formats/vact_dgnl_v1.json` (`schemaVersion: "exam-format-v1"`, 120 questions across P1.1 TV 30, P1.2 TA 30, P2 Toán 30, P3.1 Logic/Data 12, P3.2 Science 18, `available: false`, linked to `PROTO_vact_vact.tex`).
- **Updated official exam headers in LaTeX templates & pinned SHA-256:**
  - `src/exam_baseline/resources/templates/PROTO_thptqg_toan_v2.tex` + `src/exam_baseline/thpt/template.py`: added `BỘ GIÁO DỤC VÀ ĐÀO TẠO` / `ĐỀ THI THAM KHẢO`.
  - `src/exam_baseline/resources/templates/PROTO_vact_vact.tex` + `src/exam_baseline/vact/template.py`: added `ĐẠI HỌC QUỐC GIA THÀNH PHỐ HỒ CHÍ MINH` / `ĐỀ THI MINH HỌA`.
- **Verified:** `pytest -q tests/thpt tests/vact tests/api/test_ui_jobs.py` (94 passed); both `.tex` templates compiled cleanly via local MiKTeX `pdflatex` (THPT: 5 pages, V-ACT: 25 pages).

### 3. Root Markdown Cleanup (`docs/notes/`)
- Moved 8 loose root `.md` reports/notes into `docs/notes/`:
  `01_UIUX_HANDOFF_REQUEST.md`, `AGENT_UI_COORDINATION_REPORT.md`, `UIUX_HANDOFF_RESPONSE.md`, `UIUX_IMPLEMENTATION_STATUS.md`, `document.md`, `plan.md`, `restructuring_17.11.26.md`, `review_06.11.26.md`.
- Kept only standard repo config files (`README.md`, `AGENTS.md`, `CLAUDE.md`) plus this `CHANGES_SUMMARY.md` at the repository root.

### 4. `1010a7d` — `feat(web): add exam storage view and polish LaTeX/PDF workspace UX`
- **Dedicated Exam Storage ("Kho đề") view (`ExamStorageView.tsx` + `ExamSessions.rename()`):**
  - Full-page local storage library with search, status filters (*Tất cả, Đã duyệt, Chờ duyệt, Đang soạn, Bản nháp, Lỗi*), inline rename (trimmed and clamped to 100 chars matching `SessionSummary.title`), short session ID + timestamp disambiguation, honest local-storage note (no fake cloud sync), and explicit delete warning when a job is running.
  - Preserved `UiContextSnapshot.screen` (`'start' | 'workspace'`) in `App.tsx` so `/agent/interpret` Pydantic validation never rejects `'library'` view turns.
- **Cleaner left sidebar (`SidebarExamLibrary.tsx`):** Added **Kho đề** counter button and narrowed the sidebar list to the top 5 recent exams with a **Xem tất cả** link.
- **LaTeX/TikZ rendering & PDF-first completion (`MathRenderer.tsx`, `QuestionCard.tsx`, `ExamPaperView.tsx`):**
  - Upgraded `MathRenderer.tsx` to render `\begin{tabular}` tables (including nested-brace column specs), `\(...\)`, `\[...\]`, `\textbf{}`, `\textit{}`, `\emph{}`, `\underline{}`, and strip `\begin{center}`/`\begin{adjustbox}` layout wrappers.
  - Replaced raw TikZ `<pre>` dumps on the student **Đề thi** tab with a PDF jump callout while keeping collapsible TikZ technical source in **Xem đáp án** for teachers.
  - Auto-switches active workspaces from `generating` → `complete` straight to **Xem trước PDF**, moved warnings into the `.paper-scroll` `notices` slot (eliminating duplicate `visualWarnings`), and added a **Xem dạng văn bản** fallback on PDF error states.
- **Verified:** `npm.cmd test` (26/26 passed), `npm.cmd run lint` (`oxlint`, 0 warnings/errors), `npm.cmd run build` (`tsc -b && vite build`), and `pytest -q tests/test_agent_ui_service.py tests/api/test_ui_jobs.py` (50 passed).

### 5. `e4626b8` — `feat(web): replace technical UI errors with friendly Vietnamese messages`
- **Centralized UI message formatting (`astra-frontend/src/utils/userMessages.ts`):**
  - Added `formatUserError()` at UI render boundaries (preserving raw store `session.error` / `previewErrorCode` for internal state and tests while displaying teacher-friendly Vietnamese copy for API/network/auth/spend-limit/PDF/JSON failures).
  - Added `formatCapabilitySuccess()` and `formatVisualWarning()` so chat confirmations and visual alerts never expose internal capability IDs (`ui.exam.open_setup`), uppercase error codes (`EXAM_NOT_READY`), or snake_case warning codes (`missing_figure_code`).
- **UI/UX cleanup across components (`App.tsx`, `ExamPaperView.tsx`, `QuickPresetModal.tsx`, `QuestionEditor.tsx`, `AgentNotes.tsx`, `agent/executor.ts`, `agent/client.ts`):**
  - Removed duplicate error alert banners on draft/error workspaces (error stays once in the left workspace action card).
  - Replaced technical PDF/LaTeX jargon (`artifact_changed`, `latex_compiler_unavailable`, `compile.log`) with clear guidance and translated `AgentNotes` status labels (`pending`/`approved`/etc.) to Vietnamese.
  - Wrapped `AgentClient` `fetch` failures into friendly transport errors and replaced `Giao diện đã xác nhận: <capabilityId>` / `Mã: <CODE>` chat receipts with natural Vietnamese sentences (keeping `Giao diện đã thay đổi` for `STALE_CONTEXT`).
- **Verified:** `npm.cmd test` (29/29 passed, including `tests/userMessages.test.mjs`), `npm.cmd run lint` (`oxlint`, 0 warnings/errors), `npm.cmd run build` (`tsc -b && vite build`).

## Notes for Next Teammate / Agent
- **No secrets committed:** `.env` and `agent-service/.env.local` remain gitignored.
- **V-ACT next step:** When backend adds a V-ACT UI job adapter in `src/exam_baseline/ui/contracts.py` and `jobs.py`, load `vact_dgnl_v1.json` in `format_catalog()` and set `"available": true`; the frontend setup modal will automatically enable V-ACT generation.
