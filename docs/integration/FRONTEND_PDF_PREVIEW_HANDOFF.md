# Frontend handoff: exact LaTeX PDF preview

For the frontend teammate. Backend branch: `merge-mas-and-uiux`.
This branch includes the previous `main` + `uiux2` integration and the backend fixes below.
UI integration is now included in commit `6ac1ba0`; the items below describe the
contract the UI team implemented. See `CONNECTED_THPT_UI.md` for the current workflow.

## Problem and backend changes

The current HTML `ExamPaperView` reconstructs the exam layout. It cannot reproduce
the supplied LaTeX template or execute TikZ. `drawingLatex` is source code, not an image URL.
Use the compiled PDF as the canonical visual preview; keep HTML for editing questions.

Backend now compiles the exact saved student `de_thi.tex` locally, including TikZ,
without changing its template, calling a model, or sending the source to an online renderer.
The existing font profile remains unchanged. Preview contains no teacher answers/solutions.
PDF preview is a teacher draft view, available before approval; final export requires approval.

New Composer validation rejects references to absent figures/tables and pipe-delimited
pseudo tables. Contract repair is bounded by the existing retry policy. Illustrator must
return native TikZ for every requested question ID. Reviewer still runs only once.

**Existing jobs are not regenerated or rewritten.** A PDF cannot invent a figure that was
never generated. Display `visualWarnings` and ask the teacher to regenerate the affected
question with explicit figure/table data, or generate a new exam. Do not silently hide warnings.

## Local setup

From the repository root in PowerShell:

```powershell
.\.venv-win\Scripts\python.exe -m pip install -e ".[dev]" -c requirements-tested.txt
.\.venv-win\Scripts\python.exe scripts/install_latex_compiler.py
.\.venv-win\Scripts\python.exe -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000
```

The installer downloads a pinned official Windows x64 Tectonic binary, verifies its
SHA-256, and stores it in ignored `tools/.local/tectonic/`. Alternatively install
XeLaTeX/LuaLaTeX/Tectonic on PATH, or set `EXAM_LATEX_COMPILER` to its executable.
First compilation downloads TeX packages and may take several minutes; later compiles
reuse `EXAM_LATEX_CACHE_DIR` (default `runs/latex-cache`). Default timeout: 300 seconds,
configurable with `EXAM_LATEX_TIMEOUT_SECONDS`. Retry preview after a first-download timeout.
Keep one backend worker. A production deployment must install/warm its compiler and cache.
`GET /api/health` exposes `latexCompilerAvailable`; this checks discovery, not a successful compile.

## API contract

All routes use the existing `/api` proxy. `jobId` is the UUID from generation.
`GET /api/exams/{jobId}` adds:

```ts
preview: {
  status: 'not_requested' | 'unavailable' | 'queued' | 'compiling' | 'ready' | 'failed';
  revision: number; contentHash: string; sourceHash: string;
  compilerAvailable: boolean; draft: boolean;
  statusUrl: string; pdfUrl: string; logUrl: string;
  pageCount?: number; pdfHash?: string; error?: string;
};
hasDrawings: boolean;
visualWarnings: { questionId: string; code: string }[];
```

1. Once generation completes, fetch the exam package.
2. `POST /api/exams/{jobId}/preview` with its current binding:

   ```json
   {"revision": 1, "contentHash": "<64-character hash from the package>"}
   ```

   Returns **202** (`queued`/`compiling`) or **200** (already cached `ready`).
   Repeated requests reuse an active compile/cache; no generation/model call occurs.
3. Poll the returned `statusUrl` every 1–2 seconds until `ready` or `failed`.
   Stop polling on unmount, workspace switch, revision change or terminal state.
4. At `ready`, load **`pdfUrl`** in an iframe/PDF viewer. It returns inline
   `application/pdf`, with cache disabled. These URLs already contain revision/hash query parameters.
5. At `failed`, show `error`, a retry-preview action, and the `logUrl` diagnostics.
   Retry preview compiles the same saved source; it does not repair a broken question.

Same-origin example (when `/api` is proxied on the frontend origin):

```tsx
<iframe key={`${exam.examId}:${exam.revision}:${preview.pdfHash}`}
  title="Student exam PDF preview" src={preview.pdfUrl}
  style={{ width: '100%', height: '80vh', border: 0 }} />
```

If using a separate API origin, resolve returned `/api/...` paths against that origin;
do not prepend `/api` twice. Retain the complete query string. A browser without an
inline PDF viewer should offer a link to open the preview in another tab.

## Frontend behavior implemented by the UI team

- Add preview types and service methods next to the current exam API client.
- Add a **PDF preview** tab/panel beside the HTML question editor. Do not use
  browser print/HTML export as the exact-template preview. Do not run TikZ in KaTeX.
- Clearly label unapproved preview as **Draft — human review required**.
- Show loading/compiling state and `visualWarnings`; `hasDrawings=false` alone is
  valid for a text-only exam, so it is not an error.
- After edit/regeneration: discard the old iframe/preview state, reload the package,
  request preview for the new revision/hash, and clear any previous approval in UI.
- Enable approval after the teacher has opened the current ready preview; submit
  the package's revision/hash via the existing `/approve` endpoint. Backend retains
  compatibility with existing approval clients; PDF viewing is a frontend workflow rule.
- After approval, offer `GET /api/exams/{jobId}/export?type=STUDENT_EXAM&format=pdf`.
  Existing student `tex` and teacher `json` exports remain available. Teacher PDF/DOCX
  are not implemented. PDF export requires an already-ready preview of the current revision.

Errors use `{"error":{"code":"...","message":"...","details":...}}`:

| HTTP / code | Frontend action |
|---|---|
| 503 `latex_compiler_unavailable` | Show setup problem; do not regenerate the exam |
| 409 `stale_revision` / `stale_hash` | Reload package and restart preview for the current binding |
| 409 `artifact_changed` | Source was changed outside the job; show error, do not approve/export |
| 409 `preview_not_ready` | Request/poll preview; never display a previous PDF as current |
| 409 `approval_required` | Ask teacher to approve the current revision |
| status `failed`, `latex_compile_failed` / `latex_compile_timeout` | Show diagnostics and retry action |
| status `failed`, `preview_interrupted` / `preview_artifact_changed` | Retry compilation of saved source |

## Acceptance checks

Use `python -m scripts.ui_pdf_smoke` for an offline-agent test with a real compiler:
22 questions, Vietnamese template, a native TikZ parabola, a student PDF served through
the API, and byte-identical saved/compiled LaTeX. Artifacts/receipt stay under `runs/pdf-smoke/`.
It makes no model calls; first-run TeX package downloads may use the network.

Frontend manual check: generate → open PDF → see header/footer, all three parts and
TikZ when requested → edit a question → old preview cleared → new PDF → approve →
download PDF. Test compiler missing/compile failure and a legacy job with missing-table
warnings. Never show a spinner forever or reuse a stale PDF after a revision change.

Backend checks: `python -m pytest -q`; focused contracts:
`python -m pytest tests/api/test_ui_preview.py tests/thpt/test_visuals.py -q`.

Verified on this branch: Python **355 passed, 1 skipped** (the older PATH-only TeX
test); the real-compiler smoke above passed separately and all four PDF pages were
visually inspected, including Vietnamese text and TikZ. Existing frontend tests
**8 passed**, lint/build passed. Repository-wide `scripts/verify.py` stops at
**91 pre-existing Ruff errors in unchanged `rag_workflow/`**; scoped MAS/backend lint passes.
