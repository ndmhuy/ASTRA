# Next task: owner release gates for the semantic candidate

For the next engineer on feat/longlth2297/agent-main-v2 in the existing worktree. Implementation is at 6951266; the following documentation/AI-log commit contains the final handoff. Read UNIFIED_SEMANTIC_WORKFLOW_SPEC.md, PROGRESS.md, SEMANTIC_WORKFLOWS.md and the current WORKER_RUNBOOK.md gate before acting.

## Exact next external step

Owner Gate A: review and authorize deployment of the existing lightweight astra-ai-proxy Worker, disabled, preserving current global/Agent ceilings 2 and all persisted usage. Current production is bb165c28-5a06-4372-9c9e-b2bf758b9599 and forwarding=false. Keep astra-gateway, its existing BYOK alias/token and ADMISSION/global-v1/v1-admission. No website or Backend deployment, no new paid resources, no storage reset.

After explicit deployment authorization, verify /health lists astra-intent-v1 and astra-semantic-v1, compare semanticContractHash with src/exam_baseline/resources/agent/semantic-contract.json, check masForwarding=false and inspect persisted quota. This read-only readiness check must not invoke inference.

Gate B separately needs a newly approved bounded persisted Chat allowance. Both historical authorizations are consumed. No retry or fallback initially. Submit one natural THPT message that actually reaches the model; require accepted canonical THPT meaning, missing-subject clarification, one upstream attempt, recorded timings/usage/diagnostics, and zero generation writes. Disable forwarding after the approved test. Do not claim acceptance if the message used a local fast path. Gate C multi-turn acceptance needs its own budget.

## MAS remains independently blocked

Do not enable public MAS forwarding. The local disabled adapter preserves CompletionRequest and academic model/limits but cannot forward arbitrary academic prompts anonymously. Gate D needs an independent credential and actual quota pool, provider compatibility, owner-approved caller authorization/resource policy and explicit generation authorization. Do not substitute the Agent model or key, and do not change academic contracts to fit Agent limits.

## Independent follow-up work

- Extend and team-review the 197-record/scenario synthetic subset toward the proposed approximately 700 coverage objective. Keep paraphrase/scenario families within one partition. Use actual live failure evidence when authorized; do not inflate counts with template duplicates or report oracle-frame checks as NLU accuracy.
- Record independent evaluation predictions using the existing harness; it never calls a provider itself. NLU goal/slot accuracy, visible model latency and token/billing metrics are unmeasured.
- Inspect and reconcile the 18 upstream main commits when integration is explicitly undertaken. Do not automatically merge/rebase main or rewrite pushed history. The current branch intentionally preserves its existing base.

## Local recovery and evidence

- Explicit keyless runtime: build astra-frontend, then python scripts/start_agent_worker.py --port 8000. Model Chat remains unavailable until the v2 deployment/live gates; deterministic UI/chat and demo MAS remain usable. The saved private Gateway .env was preserved and has incomplete configuration.
- 56 focused Python tests, 39 frontend checks, 20 workerd groups, frontend lint/build, generated-contract checks, both mounted browser scripts and the isolated-clone startup passed. Exact scope/limits are in PROGRESS.md. No model inference was performed.
- The isolated clone is ../longlth2297-semantic-fresh-20261127 and has its own fresh dependencies, no private .env/.dev.vars, and a DO_NOT_DELETE marker. Do not remove it or other live worktrees without owner agreement.
- Ignored evidence: runs/semantic-worker-tests.log, runs/semantic-frontend-tests.log, runs/semantic-build.log, runs/semantic-security-audit.json, runs/semantic-fresh-results.json and runs/semantic-fresh-start.log. No secret values are needed to continue.

No deployment, inference, real generation, public-budget activation, push, PR or merge is authorized by this handoff. Safe local fixes, tests and corpus work remain authorized.
