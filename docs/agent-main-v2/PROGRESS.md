# ASTRA Agent main-v2 progress ledger

> Scope correction: Cloudflare is for authenticated AI credential gateway only. Do not deploy the ASTRA website, expose the origin, create a Tunnel or migrate MAS. Public web hosting requirements are future blockers, not tasks for this implementation.

Status: PARTIAL
Baseline SHA: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Old Agent reference SHA: fb834b976cb62eb7292fa839cdaf1d8738e1ec50
Feature branch / worktree: feat/longlth2297/agent-main-v2 / ../ASTRA.worktrees/longlth2297-agent-main-v2
Current HEAD: see git log; checkpoint base fbc951bade177dcea0d6e19079d17238dcd5b495
Latest origin/main checked: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Current phase / exact next action: P8 / see final report

| Phase | Status | Evidence level | Commit / report | Blocker / next step |
|---|---|---|---|---|
| P0 baseline | VERIFIED_OFFLINE | STATIC, UNIT | [Baseline](BASELINE.md) | Python and frontend baseline passed |
| P1 transport | VERIFIED_OFFLINE | REAL_UI_FIXTURE | [Source reuse](TEAM_CHANGES.md) | Interpreter fixture; no live provider |
| P2 guard/compiler | VERIFIED_OFFLINE | UNIT | [Guards](../../astra-frontend/tests/agent-recipes.test.mjs) | Mixed negated requests require clarification |
| P3 context/capabilities | PARTIAL | REAL_UI_FIXTURE | [Inventory](BASELINE.md) | 18 of 34 bound intent IDs observed in browser |
| P4 A/B/C workflows | PARTIAL | REAL_UI_FIXTURE, REAL_HTTP_NO_AI | [Browser smoke](../../scripts/agent_browser_smoke.py) | Browser-local guard added. Backend ownership and full race coverage remain open |
| P5 memory/title | VERIFIED_OFFLINE | REAL_UI_FIXTURE, UNIT | [Memory tests](../../astra-frontend/tests/agent-memory.test.mjs) | Browser-local persistence; shared accounts and durable pending plans absent |
| P6 provider/latency | VERIFIED_OFFLINE | UNIT | [Timing harness](../../astra-frontend/scripts/agent-benchmark.mjs) | Live model eligibility, intent accuracy and p95 require operator verification |
| P7 key gateway/security | VERIFIED_OFFLINE | UNIT, REAL_UI_FIXTURE | [Runbook](DEPLOY_RUNBOOK.md) | Cloudflare provisioning and live calls require authorization |
| P8 final integration | PARTIAL | REAL_UI_FIXTURE, REAL_HTTP_NO_AI, UNIT, STATIC | [Final handoff](FINAL_REPORT.md) | Live provider and gateway verification blocked by authorization. Remaining cases listed in acceptance results. |

## Checkpoint log (append, never fabricate)
- Date/time, phase, HEAD before/after, exact files, verified commands/result, fixture boundary, blockers/owner, next action, decisions and why.

- 2026-11-26 16:52 ICT · P1 · Parent `8bea5728ed03c9d68dff49b8cf8b2caea0dc35d7` · Built frontend and ran scripts/agent_browser_smoke.py; mounted greeting opened no dialog and made zero Agent HTTP calls. Semantic fixture opened the current setup dialog via same-origin Uvicorn with zero exam writes. P0 Python baseline: 392 passed, 7 subtests; scripts/smoke_server.py passed with mock provider. Transport includes the local server admission used in P2.

- 2026-11-26 16:54 ICT · P2 · Parent `d57b7ae2c713234bb91521f0f9926ffce6baa7d2` · npm test passed 19. pytest tests/api/test_agent_turn.py passed. Tested invalid input, guarded quotes, Vietnamese without accents, rejection of unknown intent, expired state, dependent-tail stop, replay, request-size limit and 429. Built frontend successfully.

- 2026-11-26 16:59 ICT · P3 · Parent `2a93fd0135b15b72e439a360786c1028befec44a` · Built frontend and ran browser smoke after correcting a stale-binding race caused by clearing the composer. Mounted setup, session listing, sidebar collapse and status were observed with no exam writes. Ported canvas/editor/approval/export handler bindings with stable target resolution and scoped confirmation. Their state-dependent checks continue in P4/P8.

- 2026-11-26 17:04 ICT · P4 · Parent `956c0a9dd35230b0d56b4d67bb8c8510ddef6713` · npm test passed 21. Browser used real catalog/evaluate routes and mounted handlers. Observed select V-ACT, reject incompatible THPT limits, no start before confirmation, one intercepted THPT start, active-job chat, note cancellation and review, editor navigation, teacher PDF gate, approval, and browser JSON download. Exam job/preview/approval/artifact responses are HTTP fixtures. Regeneration for V-ACT is unavailable by backend contract.

- 2026-11-26 17:07 ICT · P5 · Parent `7dc83e0661fad4c9601b4de8ef3d2aebad7f2f60` · Browser reload opened the saved chat by its manual title and retrieved the actual format choice after a fixture generation. npm test passed 23, including old-store migration, bounded retrieval, branch/retract, and preserving malformed storage. Store remains canonical. Prepared operations require fresh confirmation after reload.

- 2026-11-26 17:09 ICT · P6 · Parent `5dc9104907dde3defb7a55de4c6c44f06a313d32` · Ran provider timeout, cancellation/late result, quota/cooldown, no-auth/schema fallback, and attempt budget tests. Ran the local routing harness: 16/16 curated cases, 800 samples, p50 0.005 ms, p95 0.021 ms, no provider or rendering timing. Built the frontend. All metrics are offline.

- 2026-11-26 17:13 ICT · P7 · Parent `443c41a239ed8bc10298a80c141f150d4c9de362` · Mock requests validated Gemini and MAS native BYOK paths, only Cloudflare Run authentication, BYOK-only/cache/log headers, provider error classification, route/host guard, and durable attempt budget. 50 focused Python checks passed and the mounted fixture workflow still passed. Added browser Web Locks and storage conflict detection for local generation. No account access, provider calls, hosting or gateway provisioning.

- 2026-11-26 17:21 ICT · P8 · Parent `fbc951bade177dcea0d6e19079d17238dcd5b495` · Refetched unchanged main. Frontend lint/build and 23 tests passed. Python suite 408 plus 7 subtests, then 16 focused final Agent checks. Native loopback startup, mock HTTP smoke, and browser fixture passed. Browser covered manual V-ACT setup, evaluated THPT and V-ACT, fixture job progress and notes, editor prefill/save, approval and JSON download. Build and branch credential-pattern scans returned no matches. Audit, coverage, runbook and AI log included.

- 2026-11-26 · Follow-up · Direct Gemini local transport uses the existing credential and model. Model metadata returned HTTP 200 with generateContent support. Native app started with demo MAS, a 30-attempt daily limit and sanitized traces. No inference or generation sent. Live response remains to be manually verified.

- 2026-11-26 · Codex CLI manual test · Added tool-disabled ephemeral Codex exec with the shared intent schema, 30-second deadline and no fallback. Tested subprocess using a fake process and ran 19 focused Python tests. Native app started with demo MAS and the frontend timeout expanded to 35 seconds. Live inference remains for the user to test.\n\n## Release gates
- LOCAL_APP_READY: VERIFIED_OFFLINE
- ORCHESTRATION_OFFLINE_VERIFIED: PARTIAL
- LIVE_AGENT_VERIFIED: BLOCKED_EXTERNAL
- LIVE_GENERATION_VERIFIED: BLOCKED_EXTERNAL
- KEY_GATEWAY_READY: VERIFIED_OFFLINE
- KEY_GATEWAY_LIVE_VERIFIED: BLOCKED_EXTERNAL

## Budget / authorization
- Live inference authorized: NO
- Paid fallback authorized: NO
- Website deployment: OUT_OF_SCOPE
- Remote key gateway provisioning authorized: NO
- Push/PR authorized: NO

## Follow main
P8 refreshed origin with prune. Main remained at the audited SHA with 0/0 local divergence. No merge was required.
