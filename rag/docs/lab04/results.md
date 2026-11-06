# P4 preliminary lexical comparison

Run 2026-11-06 from `rag/` with `python3 -m astra_rag.evaluate`; raw per-query output is [p4-evaluation.json](evidence/p4-evaluation.json). Index snapshot `f251c63-abd83d19cca18cbd`, SQLite file 1,007,616 bytes. Times are one local run including receipt writes, not a benchmark distribution.

The 13-case provisional set adapts existing assistant expectations into shorter, explicitly scoped curriculum queries, plus three gap traps. Eight held-out relevant cases and three gap cases are **not teacher-adjudicated**, are drawn from existing public-to-development examples, and do not measure profile retrieval. IDs for a query are alternatives, not exhaustive judgments. This is hit@5 (at least one expected alternative), not source recall. MRR uses the first expected alternative.

| Arm | Split | Hit@5 | MRR | Correct gaps | Out-of-scope returned | Mean ms/query |
|---|---|---:|---:|---:|---:|---:|
| Lexical | development | 1/2 | 0.500 | n/a | 0/1 | 13.36 |
| Expanded | development | 2/2 | 1.000 | n/a | 0/2 | 5.17 |
| Lexical | held-out | 8/8 | 1.000 | 3/3 | 0/18 | 3.51 |
| Expanded | held-out | 8/8 | 1.000 | 3/3 | 0/18 | 3.92 |

The alias improves the development example “om” → “Ohm”, but this held-out set contains no variant on which it could show a gain. It stays opt-in. Numbers are too small and narrow to support a quality or latency claim beyond these cases. Search writes receipts, so timing includes disk writes.

Not run: dense models, hybrid fusion, reranking, parent expansion, model size or memory measurements, profile relevance evaluation, token cost, and matched Writer generation/blind review. No model or third-party library was downloaded; neither `sentence_transformers` nor Streamlit was installed in the interpreter used. The actual Writer is absent in this snapshot. The P3 and full P4 gates remain open.
