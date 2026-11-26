# ASTRA Agent main-v2 progress ledger

> Scope correction: Cloudflare is for authenticated AI credential gateway only. Do not deploy the ASTRA website, expose the origin, create a Tunnel or migrate MAS. Public web hosting requirements are future blockers, not tasks for this implementation.

Status: IN_PROGRESS
Baseline SHA: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Old Agent reference SHA: fb834b976cb62eb7292fa839cdaf1d8738e1ec50
Feature branch / worktree: feat/longlth2297/agent-main-v2 / ../ASTRA.worktrees/longlth2297-agent-main-v2
Current HEAD before checkpoints: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Latest origin/main checked: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Current phase / exact next action: P1 / integrate versioned turn transport

| Phase | Status | Evidence level | Commit / report | Blocker / next step |
|---|---|---|---|---|
| P0 baseline | VERIFIED_OFFLINE | STATIC, UNIT | [Baseline](BASELINE.md) | Python baseline run in progress |
| P1 transport | NOT_STARTED | — | — | — |
| P2 guard/compiler | NOT_STARTED | — | — | — |
| P3 context/capabilities | NOT_STARTED | — | — | — |
| P4 A/B/C workflows | NOT_STARTED | — | — | — |
| P5 memory/title | NOT_STARTED | — | — | — |
| P6 provider/latency | NOT_STARTED | — | — | — |
| P7 key gateway/security | NOT_STARTED | — | — | — |
| P8 final integration | NOT_STARTED | — | — | — |

## Checkpoint log (append, never fabricate)
- Date/time, phase, HEAD before/after, exact files, verified commands/result, fixture boundary, blockers/owner, next action, decisions and why.

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
