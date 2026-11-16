# Agent Phase 1 test plan

| Acceptance area | Tests |
|---|---|
| IN01-IN02 grouped fields and continuity | `test_in01_in02_grouped_missing_and_slot_continuity` |
| IN03-IN05 presets and acceptance | `test_in03_preset_requires_explicit_acceptance`, requirements tests |
| IN06-IN08 correction/negation/invalid | correction test, understanding tests, evaluator validation |
| IN09-IN10 dynamic descriptor/default | `test_descriptor_change_automatically_changes_missing_fields`, default test |
| IN11-IN13 mock readiness/trusted approval | mock-valid test, exact approval test |
| IN14-IN15 replay/unknown | job idempotency test; unknown state logic implemented, live POST deferred |
| JOB01-JOB03 chat/status/no effects | app-help/status tests; unknown/chatter tests |
| JOB04-JOB06 remark and stable question targeting | three named job tests |
| JOB07-JOB09 structural/cancel/supersede | job ledger tests |
| JOB10-JOB15 active gate/package/proposal/workspace | active gate and completion tests; live flag stream deferred |
| UI01-UI03 knowledge/navigation availability | orchestrator/capability tests |
| UI04-UI06 referent/stale/strict params | no guessed ID, stale and extra-param tests |
| UI07-UI08 serial dependency/new ID | executor stops/skips logic; session-create capability deferred |
| UI09-UI11 honesty/content/deduplication | app knowledge, content-as-data, receipt replay tests |
| Vietnamese baseline | `test_understanding.py` + 55-record JSONL evaluation |
| Full repository regression | complete `pytest -q` and Ruff commands in `TEST_RESULTS.md` |

Live integration cases remain blocked and are not counted as passing Phase 1 tests.
