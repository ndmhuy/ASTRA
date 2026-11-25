# ASTRA: shared integration plan

For all teams. Proposed by UI/UX; interfaces are open to revision. Reuse existing contracts
where possible and agree mappings before changing shared code.

## 1. What UI/UX already has

| Part | Role / connection point |
|---|---|
| `App.tsx` | Screens, navigation, active workspace, setup dialog |
| `state/examSessions.ts` | Per-workspace chat, questions, generation state and job ID; results target their original workspace |
| `services/examService.ts` | Backend adapter: start, progress, result, edit/regenerate, export |
| `types/exam.ts` | Current UI request/result types; adapt jointly at boundaries |
| `WorkspaceLayout` | Chat beside live exam canvas; quick setup uses presets, detailed entry opens a custom workspace directly |

Current limits: generation/chat use mocks; questions assume four-choice MCQ; uploads pass
filenames. Format counts are placeholders, not authoritative specifications.

## 2. How we connect

Teacher input -> UI/Chatbot -> Backend-validated matrix -> RAG -> MAS -> teacher review -> export.

| Team | Integration proposal |
|---|---|
| UI | Keep presentation/session ownership; connect services and Agent handlers |
| Chatbot | Port M2 controller/protocol/executor; interpret intent, request missing fields, return plans; UI executes and reports receipts |
| Backend/MAS | Own format rules, validation, generation jobs/results, question revisions and reviewed exports |
| RAG | Retrieve from validated matrix; pass evidence, provenance, warnings and gaps into MAS intake |
| Corpus | Provide pinned release + coverage metadata to RAG; keep bulk source data separate from app merges |

**Shared exam-format JSON:** propose Backend-owned versioned files/catalog with format ID,
subject/grade support, duration/score, ordered sections/types/counts/scoring, editable fields,
constraints and availability. UI/Chatbot consume it; submit format ID/version + overrides.
Existing equivalent configuration can be exposed instead; Backend should propose corrections.

## 3. Agreements needed

- Choose one first engine/scope. Generic `/v2` and fixed THPT/VACT flows are different.
- UI expects async jobs/progress; existing `/v2/exams/generate` returns synchronous LaTeX.
  Agree an adapter with idempotent start, recoverable status, structured result and errors.
- UI generation adapter is the proposed sole start caller; Agent supplies validated plans.
- Agree stable question IDs/revisions and MCQ/true-false/short-answer models; numbering is display-only.
- Preserve source/approval flags and retrieval gaps; show unsupported combinations explicitly.
  NB/TH/VD and VDC require explicit mapping. Solver must not receive Writer answers.
- Bind approval/export to exact revision/hash; editing invalidates approval.

## 4. Merge order

1. Refresh refs; create integration branch from latest `main`.
2. Integrate `uiux2`, then M2 chatbot adapters. Manually reconcile App/store/scripts/proxy;
   preserve direct detailed setup, loading/transitions and readable exam names.
3. Connect format catalog + requirements evaluator, then pinned RAG -> intake -> chosen engine.
4. Connect real jobs/results/editing/export; run one complete teacher workflow before merge.

Cached `main` already includes inspected RAG integration/handoff and mini-composer/optimized
pipeline branches. Use newer M2 chatbot branch rather than merging its predecessor separately.
Do not merge corpus history wholesale or overwrite teammate files with ours/theirs.

## 5. Completion gate

- [ ] Clean setup starts all services and loads the pinned corpus.
- [ ] Real request reaches RAG/MAS and displays real questions/progress/errors.
- [ ] Retry/reconnect does not duplicate jobs or update the wrong workspace.
- [ ] Counts/types/scores match format; unsupported inputs fail clearly.
- [ ] Edits require new approval; reviewed PDF/DOCX opens; student copy excludes answers.
- [ ] Python tests, RAG acceptance, frontend build/lint/unit/browser checks pass.

Send this file to everyone; send each team its own `TEAM_*.md` for implementation details.

Inspection: 2026-11-17, cached refs only: UI `939b3ed`, M2 `47b1161`, main `f6b7ea8`,
corpus `8b8fb7b`. Remote refresh failed; no merge or application tests performed.
