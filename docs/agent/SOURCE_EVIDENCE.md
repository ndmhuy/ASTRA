# Agent Phase 1 source evidence

This records Phase A reconnaissance after `git fetch --all --prune` on 2026-11-15
(Asia/Bangkok). Source and executable tests outrank the supplied snapshots.

| Fact | Source (ref:path:line) | Status | Implication |
|---|---|---|---|
| Working implementation base is the generation branch | `origin/feature/mini-composer-illustrator@24a2d092` | verified | This local feature branch was cut from the temporary backend base, not merged into it. |
| `mas-intake-v1` requires resolved intent, full `ExamMatrix`, and RAG evidence | `24a2d092:src/exam_baseline/intake.py:15-80` | implemented downstream boundary | It is not teacher dialogue or draft-to-matrix conversion. |
| Intake encodes an already valid request into `MiniRequest`/`PipelineRequest` | `24a2d092:src/exam_baseline/intake.py:83-114` | implemented | Phase 1 does not replace it or fabricate its inputs. |
| `ExamMatrix` enforces exact topic/type/difficulty totals | `24a2d092:src/exam_baseline/core/models.py:66-114` | implemented | Agent draft completion is distinct from professional matrix validity. |
| `/v2/exams/generate` awaits the pipeline and returns LaTeX | `24a2d092:src/exam_baseline/api/routes_pipeline.py:20-77` | implemented, synchronous | There is no verified job start/status/SSE contract. |
| Default provider is offline mock; real provider needs a key | `24a2d092:src/exam_baseline/config.py:19-53` | implemented | Agent tests/demo never select `chat_completions`. |
| RAG aliases cover many subjects but deployed corpus scope is separate | `85411aa4:rag_workflow/config.json:32-66` | implemented on separate branch | Aliases are conceptual evidence; no RAG branch code was copied or merged. |
| RAG configuration supports grades 10-12 and Kết nối tri thức | `85411aa4:rag_workflow/config.json:2-6` | branch-local fact | Agent fixture must not claim broader production coverage. |
| UI chat response remains a fixed acknowledgement | `a1e3f44d:astra-frontend/src/state/examSessions.ts:74-76` | partial/mock | No live agent transport exists. |
| UI composer is disabled during generation | `a1e3f44d:astra-frontend/src/App.tsx:120` | implemented UI behavior, conflicts with product rule | UI work is required for chat-during-generation integration. |
| UI API adapter expects job/SSE routes not present in backend | `a1e3f44d:astra-frontend/src/services/examService.ts:385-430` | documented adapter only | Phase 1 uses a labeled in-process mock job port. |
| UI defaults to mock service | `a1e3f44d:astra-frontend/src/services/examService.ts:456-462` | implemented | UI progress is not backend performance evidence. |
| Handoff capability registry advertises no actions | `references/ASTRA_AGENT_HANDOFF.zip:ui_capabilities.json` | proposed | Core registry defaults disabled; tests enable a mock handler explicitly. |

## Version drift

- Backend audit UI ref: `9b5ca47c`.
- UI handoff ref: `c052b689`.
- Ref after fresh fetch: `a1e3f44d`.
- Between `c052b689..a1e3f44d`, the inspected contract paths changed only in
  `astra-frontend/src/App.tsx` (4 lines); job/store/service/types/tests were unchanged.
- This is evidence of limited drift, not approval of the proposed UI contract.

## Repository and test commands found

- Backend: Python >=3.10; `python -m pytest -q`; `python -m ruff check .` from
  `README.md` and `pyproject.toml`.
- UI branch: `npm run build`, `npm run lint`; store tests use
  `node --experimental-strip-types --test tests/examSessions.test.mjs` in the handoff.
- No UI source was merged into this branch.

## Branch decision

Repository rules normally require branches from `origin/main`, but `origin/main@9f93fa4`
contains team documents and no runnable backend. The master prompt names `24a2d092` as the
temporary integration baseline. Therefore local branch `feat/longlth2297/agent-orchestrator` was
cut from that exact ref. No teammate branch was checked out, modified, merged, rebased, or
pushed.
