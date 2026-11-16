# Test results

## Agent transport follow-up

Observed after adding standalone HTTP service, correlated receipt handling and intake guards:

```text
python -m ruff check .
All checks passed! (exit 0)
python -m pytest -q
331 passed, 1 warning in 13.62s (exit 0)
```

The 13 additional cases cover HTTP round trip/replay, request ID payload collision, wrong receipt
address/action/plan, unobserved navigation, workspace isolation, resource limits, strict inbound
JSON, OpenAPI exposure, empty/unaccepted topics and wrong field types. No UI source changed.
Prior results below are retained as historical Phase 1 evidence.

This file is updated from commands actually executed on Windows, Python 3.12.10. No API key,
network inference, paid model, browser, or generation backend was used.

## Phase C focused run

```text
.\.venv-agent\Scripts\python.exe -m pytest -q tests\agent
42 passed in 0.09s
exit code 0
```

## Lint

```text
.\.venv-agent\Scripts\python.exe -m ruff check src\exam_baseline\agent tests\agent
All checks passed!
exit code 0
```

## Curated evaluation

```text
.\.venv-agent\Scripts\python.exe -m exam_baseline.agent.evaluation evaluation\utterances_vi.jsonl
55 records; intent exact recall 1.0000; slot-case accuracy 1.0000;
false unsafe actions 0
exit code 0
```

These are in-sample deterministic corpus results, not a claim about arbitrary Vietnamese or
model quality. The corpus includes accents/no accents, mixed language, corrections, negation,
multi-intent, deictic, invalid, remark, and injection-shaped cases.

## Full repository regression

```text
.\.venv-agent\Scripts\python.exe -m pytest -q
318 passed, 1 warning in 14.06s
exit code 0
```

The warning is a dependency deprecation from `fastapi.testclient`/Starlette recommending
`httpx2`; it is not emitted by the agent package and did not fail a test.

## Demo smoke

```text
.\.venv-agent\Scripts\python.exe -m exam_baseline.agent.demo
JSON trace emitted; exit code 0
```
