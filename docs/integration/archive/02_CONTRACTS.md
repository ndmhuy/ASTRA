# Boundaries to agree before wiring

For implementers. Existing contracts below are evidence; **new job/API design remains proposed**.
Keep schema definitions in code; these notes do not introduce duplicate schemas.

UI-side architecture and proposed merge seams are explained first in each [team handoff](04_TEAM_TASKS.md).
Proposals are negotiable: reuse equivalent existing team contracts and record the agreed mapping.

**Exam-format configuration:** propose Backend-owned versioned JSON files/catalog containing
format ID/version, subject/grade support, duration/score, ordered sections/types/counts/scoring,
editable fields/constraints and availability. UI/Chatbot consume this catalog; generation submits
format ID/version plus overrides. Backend resolves/validates it. Current UI preset numbers are
placeholders; see [Backend handoff](../TEAM_BACKEND.md) for expectations and proposed file location.

| Boundary | Existing source of truth | Required integration work |
|---|---|---|
| UI ↔ Agent | Agent `models.py`, `http.py`; TS `integration/agentProtocol.ts` on `47b1161` | Preserve `snake_case`, `agent-turn/0.1`, `agent-actions/0.1`; runtime validation and correlated receipts |
| Requirements → MAS | `main:src/exam_baseline/intake.py`, `core/models.py` | Backend supplies descriptor + evaluator converting teacher draft into validated `ExamMatrix`; Agent must not guess missing fields |
| RAG → intake | `main:rag_workflow/mas_adapter.py`, `intake.py` | Feed `mas_intake_rag` into `mas-intake-v1`; validate subject/grade/book/year/topic compatibility |
| Generation → UI | UI `types/exam.ts` versus backend `PipelineRequest`/LaTeX response | Choose generation engine and implement one explicit adapter; existing responses are incompatible |
| Review → export | `main:docs/MAS_INTAKE_AND_EXPORT.md`, exporter implementation | Bind approval to exact draft revision/hash; invalidate on edit; preserve separate student/teacher artifacts |

## Decisions that unblock implementation

1. **First engine/scope:** recommend one supported Toán workflow. Choose generic four-agent
   pipeline OR fixed THPT engine; do not assume `/v2` runs the THPT CLI. Add other subjects later.
2. **Job facade:** recommend wrapping the chosen engine behind the UI's async service boundary.
   Agree endpoint paths and request/result models first; do not rename `/v2` and call it a job API.
3. **Single start caller:** retain the Agent plan's design: UI generation adapter starts once
   using a backend-validated approval reference; Agent supplies the plan, never a second start.
4. **Question identity:** backend owns stable string ID + revision; display numbering is separate.
   Support a discriminated question type for MCQ/true-false/short-answer before full THPT UI.

## Proposed async minimum

- Start: validated request/approval reference + idempotency key → stable job ID.
- Status: job ID, state (`queued/running/succeeded/failed/cancelled`), latest progress,
  structured error; reconnect can recover without starting again.
- Result: versioned exam package + stable question IDs/revisions + artifact references.
  Decide how each engine produces this; LaTeX text alone cannot populate the current question UI.
- Edit/regenerate: expected revision; reject stale edits; invalidate review/export approval.
- Approval/export: actor, draft revision/hash; export only matching reviewed artifacts.

## RAG invariants

- Preserve source locator/version/hash, approval flags, gaps and warnings. Retrieval success
  does not mean teacher approval. `form_example` alone cannot satisfy content evidence.
- Keep corpus's NB/TH/VD scheme. VDC fallback must carry its warning, or use strict rejection;
  never silently equate high discrimination with VDC.
- Treat retrieved text as untrusted evidence; never send Writer keys/solutions to Blind Solver.
- Pin a corpus SHA or portable release manifest; missing corpus must produce an explicit failure.
