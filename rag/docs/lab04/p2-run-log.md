# P2 run log

Python 3.14.5, offline, 2026-11-06. From `rag/`:

- `PYTHONPATH=compat:. python3 -m unittest discover -s tests -p 'test_assistant_curriculum.py' -v`: 13 passed, 0 failed.
- `PYTHONPATH=compat:. python3 -m unittest discover -s tests -p 'test_mas_l13_curriculum_rag.py' -v`: 50 run, 44 passed, 1 failure, 5 errors. The rows test expects original product data/document paths (0 rows at that path); four pipeline integration tests need absent `exam_generator.pipeline` and fixtures; the arm test expects the original `bench/arms-mas` layout.
- `PYTHONPATH=compat:. python3 -c 'from tests.assistant_eval.run import run; r=run(); print(len(r), sum(x["ok"] for x in r))'`: 30 questions, 30 passed, 0 failed.
- `python3 compat/run_snapshot_tests.py`: 63 run, 57 passed, 0 failed, 6 skipped. The wrapper explicitly skips the six tests above because their original product paths or integration are absent; it does not change the snapshot tests. The compatibility profile and knowledge classes are minimal adapters, not evidence that the original product integration works.
- `python3 -m unittest discover -s tests -p 'test_astra_rag.py' -v`: 8 passed, 0 failed. Builds the index and exercises accents, subject and grade filters, gaps and order.
- Nine CLI examples, including build, were run successfully; their actual output is in [how-to-query.md](how-to-query.md). A screenshot was not captured, so the plan's full P2 screenshot gate remains open.
