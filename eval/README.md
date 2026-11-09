# ASTRA RAG Retrieval Evaluation Suite

This directory holds the deterministic benchmark query set (`gold_queries.jsonl`) for `rag_workflow/eval.py`.

## Design & Privacy Rules

- **Zero source text:** `gold_queries.jsonl` stores only query text, expected status/gap codes, `source_locator` identifiers, and question boundary labels (`Câu N`). No textbook or exam text is copied into this file.
- **Automated corpus verification (`auto-corpus-check-v1`):** Before scoring any retrieval mode, `verify_gold_queries()` checks every `relevant` locator and `relevant_passages` question label (`Câu N`) against the loaded corpus snapshot and raises an error if any locator or question label is missing.
- **Dev vs. Held-out Split:** Queries are partitioned into `dev` (18 queries) and `heldout` (19 queries) across `curriculum`, `exam`, and `guardrail` gap checks.

## Running the Benchmark

```powershell
# Evaluate all 3 modes (hybrid, bm25, embedding) on the existing staging corpus
python -m rag_workflow.eval --existing --mode all --out runs/eval-existing.json

# Evaluate held-out split only
python -m rag_workflow.eval --existing --mode all --split heldout

# Evaluate on synthetic demo fixtures (used in CI)
python -m rag_workflow.eval --demo --mode all
```
