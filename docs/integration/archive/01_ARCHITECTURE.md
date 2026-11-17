# ASTRA integration map

For all teams. Code inspection: 2026-11-17; **cached Git refs only**. Fetch failed
(Git metadata write denied; GitHub connection unavailable). Refresh refs before merging.
No branches switched, code changed, or merges performed. Runtime tests not run.

## What exists

| Layer | Source inspected | Actual boundary/status |
|---|---|---|
| UI | `uiux2` / `origin/uiux2` `939b3ed` | React/Vite; session store; generation defaults to mock |
| Chatbot | `origin/feat/longlth2297/m2-ui-agent-orchestration` `47b1161` | Standalone FastAPI Agent + React adapters; local navigation/setup actions; generation mocked |
| Backend/MAS | `origin/main` `f6b7ea8` | Baseline API, four-agent pipeline, separate THPT/VACT CLI flows, intake/export utilities |
| RAG | same `main`; integration branch `79c9931` is already an ancestor | Retrieval library + separate workbench; Topic Packs and MAS passage adapter |
| Corpus | `origin/staging/rag` `8b8fb7b` | Separate Git snapshot consumed by loaders; not an application branch to merge wholesale |

Target flow: UI ↔ Agent → validated requirements → RAG → MAS → review → export.
**This complete flow is not wired today.**

## Concrete gaps

- UI `services/examService.ts` expects `/api/exams/*`, job JSON, SSE and editable questions.
  Backend `api/routes_pipeline.py` exposes synchronous `/v2/exams/generate`, returning LaTeX.
- Agent `http.py` exposes `/agent/turns` and `/agent/execution-results`; its local UI actions
  do not start backend generation. Requirements/evaluation/job implementations remain fixtures/mocks.
- RAG exposes `retrieve_exam_context()` and `mas_intake_rag`; no call to these was found under
  `main:src/`. An adapter existing does not establish orchestration.
- UI `QuestionItem` requires four choices and numeric IDs. RAG supports P1/P2/P3 and string IDs;
  true/false and short-answer items need explicit UI models/renderers.
- UI uploads currently pass filenames; mock exports produce `.doc`/`.txt`. Neither is a real
  upload pipeline or the backend's reviewed PDF/DOCX export.
- `main` packaging discovers only `src/`; root-level `rag_workflow` currently relies on repo-root
  execution. Deployment needs an explicit packaging decision and corpus release input.

## Source precedence

Use executable schemas/routes first, then the latest delivery report. In particular,
`docs/agent/CONNECTION_RECOVERY_REPORT.md` supersedes older claims that browser tests are absent
(reported: 16 frontend, 4 browser, 354 Python passes; **not rerun here**).
Older `handoff/` examples and blocker tables are historical where current code disagrees.

Read next: [contracts](02_CONTRACTS.md), [merge sequence](03_MERGE_PLAN.md),
[owners and acceptance](04_TEAM_TASKS.md).
