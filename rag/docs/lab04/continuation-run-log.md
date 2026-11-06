# P3–P6 continuation run log (2026-11-06)

All runs used Python 3.14.5 in the isolated local copy of the ASTRA branch. No network services, external model, or paid API were used.

- `python3 -m unittest discover -s tests -p 'test_astra_rag.py' -v`: 9 passed, 0 failed.
- `python3 -m unittest discover -s tests -p 'test_evidence_bundle.py' -v`: 4 passed, 0 failed.
- `python3 compat/run_snapshot_tests.py`: 57 passed, 6 skipped, 0 failed.
- `python3 -m astra_rag.evaluate`: 13 scoped cases for each of two arms. Details and measurements: [results.md](results.md) and [raw JSON](evidence/p4-evaluation.json).
- `python3 -m astra_rag.search -q om --subject 'Vật lí' --grades 11 --kind curriculum --expand --limit 1`: observed `curriculum:vat-li-11-c4-b23`.
- `python3 -m astra_rag.bundle -q 'hàm số' --subject Toan --grades 12 --kind curriculum --budget-bytes 1024`: observed two items and `budget_exhausted`; compact encoded JSON stayed within 1,024 bytes in the test.
- `printf 'hàm số\nToan\n12\n\n' | python3 -m astra_rag.demo`: observed five cited hits. Repeated with `zzzxqvnonexistent`: observed `GAP: no_match`.
- An attempted test command from the repository root failed because `tests` is under `rag/`; it was rerun from `rag/` with the result reported above.

The UI automation tool refused access to Terminal; no screenshot was captured. Streamlit and sentence-transformers are not installed, and downloads were not authorized. The work is partial; see [plan.md](plan.md) for remaining gates.
