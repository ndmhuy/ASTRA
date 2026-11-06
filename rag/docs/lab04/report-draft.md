# Lab04 report draft — ASTRA curriculum RAG

**Draft for Huy to review and complete. Not a submission.** The week handout, screenshots, Huy's own run times, independent review and final lab packaging have not been verified here. The lab repository requires its own report template, declaration and build process.

## Feature and scope

The feature retrieves cited curriculum and exam-profile topic records for a teacher's subject, grade and query. It uses local SQLite FTS5 with accent folding and structured subject/grade filters, records retrieval receipts and reports gaps. Curriculum rows are draft; profile cognitive labels are agent-reviewed, not teacher-confirmed. Retrieval is evidence, not proof that an item is correct or in scope.

## Process and results

The spec and phased plan precede implementation. Huy stated that he reviewed and accepted them; his exact review and checks need his confirmation in [report-inputs.md](report-inputs.md). AI-assisted implementation and its checks are recorded in the ASTRA session log and [P2](p2-run-log.md) and [continuation](continuation-run-log.md) run logs.

The offline P2 CLI and receipt path were run. The continuation added an opt-in spelling variant, a versioned local bundle caller and a terminal demo. Search tests: 9 passed; bundle tests: 4 passed. Snapshot compatibility tests: 57 passed and 6 skipped; those skips include unavailable original product integration and paths. The separate earlier assistant eval reported 30/30, which tests the copied assistant source and should not be attributed to the new index.

A small provisional curriculum-only comparison is documented in [results.md](results.md). On eight held-out expected-hit cases, each lexical arm found an expected alternative in the first five, and both returned the expected gaps on three trap cases. No gain from expansion was established on that set. These are not teacher-adjudicated profile recall or end-to-end quality results.

## Outstanding work

Dense retrieval, fusion, reranking, Streamlit, screenshot evidence, matched Writer generation and blind review were not run. The Writer is absent from this snapshot. The bundle has a UTF-8 byte budget, not a model-token cap, and its role marker is not a prompt-injection defense. A TA-facing report must retain these limitations and cite actual measurements. AI-generated text is not evidence.

## Other work and review

Huy stated that he helped plan and orient several groups through discussions; evidence is limited to the sources listed in [report-inputs.md](report-inputs.md). TODO: Huy supplies any additional evidence, dates, own checks, review and corrections.

## Appendix: AI Usage Notes

Tool: Codex, GPT-6, desktop application. Date: 2026-11-06; exact access times are in the ASTRA session logs. Prompts: continue the RAG phases and report work. AI drafted code, tests, documentation and this draft. Verification by AI: commands and results are recorded in the linked logs. TODO: Huy must describe what he personally did, reviewed and checked, confirm all claims and add the course-required declaration before submission.
