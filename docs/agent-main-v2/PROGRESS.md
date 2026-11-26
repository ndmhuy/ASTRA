# ASTRA Agent main-v2 progress ledger

> Scope correction: Cloudflare is for authenticated AI credential gateway only. Do not deploy the ASTRA website, expose the origin, create a Tunnel or migrate MAS. Public web hosting requirements are future blockers, not tasks for this implementation.

Status: IN_PROGRESS
Baseline SHA: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Old Agent reference SHA: fb834b976cb62eb7292fa839cdaf1d8738e1ec50
Feature branch / worktree: feat/longlth2297/agent-main-v2 / ../ASTRA.worktrees/longlth2297-agent-main-v2
Current HEAD: see git log; checkpoint base d57b7ae2c713234bb91521f0f9926ffce6baa7d2
Latest origin/main checked: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Current phase / exact next action: P3 / context/capabilities

| Phase | Status | Evidence level | Commit / report | Blocker / next step |
|---|---|---|---|---|
| P0 baseline | VERIFIED_OFFLINE | STATIC, UNIT | [Baseline](BASELINE.md) | Python baseline run in progress |
| P1 transport | VERIFIED_OFFLINE | REAL_UI_FIXTURE | [Source reuse](TEAM_CHANGES.md) | Interpreter fixture; no live provider |
| P2 guard/compiler | VERIFIED_OFFLINE | UNIT | [Guards](../../astra-frontend/tests/agent-recipes.test.mjs) | Mixed negated requests require clarification |
| P3 context/capabilities | NOT_STARTED | — | — | — |
| P4 A/B/C workflows | NOT_STARTED | — | — | — |
| P5 memory/title | NOT_STARTED | — | — | — |
| P6 provider/latency | NOT_STARTED | — | — | — |
| P7 key gateway/security | NOT_STARTED | — | — | — |
| P8 final integration | NOT_STARTED | — | — | — |

## Checkpoint log (append, never fabricate)
- Date/time, phase, HEAD before/after, exact files, verified commands/result, fixture boundary, blockers/owner, next action, decisions and why.

- 2026-11-26 16:52 ICT · P1 · Parent `8bea5728ed03c9d68dff49b8cf8b2caea0dc35d7` · Built frontend and ran scripts/agent_browser_smoke.py; mounted greeting opened no dialog and made zero Agent HTTP calls. Semantic fixture opened the current setup dialog via same-origin Uvicorn with zero exam writes. P0 Python baseline: 392 passed, 7 subtests; scripts/smoke_server.py passed with mock provider. Transport includes the local server admission used in P2.

- 2026-11-26 16:54 ICT · P2 · Parent `d57b7ae2c713234bb91521f0f9926ffce6baa7d2` · npm test passed 19. pytest tests/api/test_agent_turn.py passed. Tested invalid input, guarded quotes, Vietnamese without accents, rejection of unknown intent, expired state, dependent-tail stop, replay, request-size limit and 429. Built frontend successfully.

## Release gates
- LOCAL_APP_READY: NOT_VERIFIED
- ORCHESTRATION_OFFLINE_VERIFIED: NOT_VERIFIED
- LIVE_AGENT_VERIFIED: NOT_VERIFIED
- LIVE_GENERATION_VERIFIED: NOT_VERIFIED
- KEY_GATEWAY_READY: NOT_VERIFIED
- KEY_GATEWAY_LIVE_VERIFIED: NOT_VERIFIED

## Budget / authorization
- Live inference authorized: NO
- Paid fallback authorized: NO
- Website deployment: OUT_OF_SCOPE
- Remote key gateway provisioning authorized: NO
- Push/PR authorized: NO

## Follow main
Record each baseline refresh and relevant source changes. Do not overwrite main or silently port stale handler assumptions. Mark affected gate reopened when contract changes.
