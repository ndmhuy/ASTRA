# RAG snapshot (from the Lecturing product)

What this is: a verbatim snapshot of the curriculum-grounded RAG that already exists in the Lecturing app, copied here as the starting point for ASTRA's knowledge base. Audience: ASTRA members building the RAG track.

Provenance (source repo is private; no history is copied):
- `src/rag.py`, `src/curriculum_map.py`, `data/`, `bench/A1-BPLBRAG.json`, `tests/test_mas_l13_curriculum_rag.py`: branch `claude/format-frames-7af6e7`, from commit `435c3be7` (2026-10-23, L13 + L9-lite).
- `src/assistant_curriculum_source.py`, `tests/test_assistant_curriculum.py`, `tests/assistant_eval_*`: commit `558be906` (2026-11-01, assistant curriculum source and 30-question eval).
- `docs/`: the curriculum-RAG architecture plan (2026-10-22) and the textbook-series decision.

Contents: a 687-row draft curriculum map (`data/*.jsonl`, grades 10-12, with CHECKS/GAPS/SOURCES notes), a lexical (BM25-style, diacritic-folded) retriever behind an interface, an evidence bundle under a token cap (default 3000), and the assistant source that re-ranks by coverage and reports honest gaps.

Not runnable on its own: the files import `exam_generator.mas_profile` and `exam_generator.assistant.knowledge`, which stay in the product and are not copied. Verified here only: `python -m py_compile` passes on `src/*.py`. The tests were not run in this repo. Port them (stub those two modules) before relying on them.

Removed on purpose: production prompts, licence/DRM code, keys, textbooks. Textbook text stays in a private store (see `docs/astra-curriculum-rag-plan.md`, rights section).
