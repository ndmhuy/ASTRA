# ASTRA RAG Retrieval & MAS-Handoff Evaluation Suite

This directory holds:
1. `gold_queries.jsonl`: the deterministic benchmark query set for free-text curriculum and exam retrieval (`rag_workflow/eval.py`).
2. `toan_thpt_acceptance.json`: the **Toán THPT MAS-Handoff Acceptance Suite** (`P1`, `P2` with `a..d` levels, `P3`, `VDC` policies, and missing-data gaps) plus the 22-question sample exam matrix verification.

## Design & Privacy Rules

- **Zero source text:** `gold_queries.jsonl` and `toan_thpt_acceptance.json` store only query/matrix specifications, expected status/gap/warning codes, `topic_pack_id` / `unit_id` / `source_locator` identifiers, and question boundary labels (`Câu N`). No copyrighted textbook or exam text is copied into these files.
- **Automated corpus verification (`auto-corpus-check-v1`):** Before scoring any retrieval mode, `verify_gold_queries()` checks every `relevant` locator and `relevant_passages` question label (`Câu N`) against the loaded corpus snapshot and raises an error if any locator or question label is missing.
- **Dev vs. Held-out Split:** Queries in `gold_queries.jsonl` are partitioned into `dev` (17 queries) and `heldout` (18 queries) across `curriculum`, `exam`, and `guardrail` gap checks.

## Running the Benchmarks

```powershell
# 1. Run the Toán THPT MAS-handoff acceptance suite (8 cases + 22-question sample matrix)
python -m rag_workflow.eval --acceptance --out runs/eval-toan-acceptance.json

# 2. Evaluate all 3 modes (hybrid, bm25, embedding) on the existing staging corpus
python -m rag_workflow.eval --existing --mode all --out runs/eval-existing.json

# 3. Evaluate held-out split only
python -m rag_workflow.eval --existing --mode all --split heldout

# 4. Evaluate on synthetic demo fixtures (used in CI)
python -m rag_workflow.eval --demo --mode all
```
