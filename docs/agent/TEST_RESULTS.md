# Test results

## M2 UI orchestration implementation — 2026-11-16

Observed after implementing the React adapter/executor and matching local Agent capabilities:

```text
astra-frontend: npm run build
PASS (exit 0; bundle-size warning only)

astra-frontend: npm run lint
PASS (exit 0; 2 pre-existing no-useless-escape warnings)

astra-frontend: npm test
10 passed, 0 failed (exit 0)

python -m ruff check src/exam_baseline/agent tests/agent
All checks passed (exit 0)

python -m pytest tests/agent -q
73 passed, 1 dependency warning (exit 0)

python -m pytest -q
349 passed, 1 dependency warning in 14.81s (exit 0)
```

The live proxy smoke produced `action_plan -> ui.navigate(library) -> receipt -> reply` through
`127.0.0.1:5173/agent`, with both Uvicorn endpoints returning 200. Browser automation could not
start because its Windows native pipe was unavailable, so browser E2E is explicitly unverified.
No paid model, Backend generation, or external API was called.

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
