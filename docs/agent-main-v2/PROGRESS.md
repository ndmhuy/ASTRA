# ASTRA Agent main-v2 progress ledger

> Scope correction: Cloudflare is for authenticated AI credential gateway only. Do not deploy the ASTRA website, expose the origin, create a Tunnel or migrate MAS. Public web hosting requirements are future blockers, not tasks for this implementation.

Status: PARTIAL
Baseline SHA: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Old Agent reference SHA: fb834b976cb62eb7292fa839cdaf1d8738e1ec50
Feature branch / worktree: feat/longlth2297/agent-main-v2 / ../ASTRA.worktrees/longlth2297-agent-main-v2
Current HEAD: see git log; checkpoint base fbc951bade177dcea0d6e19079d17238dcd5b495
Latest origin/main checked: 7523c79556a9935df5008c92043f1e38d6e5d2a2
Current phase / exact next action: W7 additional attempt identified an application cross-field contract mismatch. Provider grammar corrected offline. Forwarding disabled, allowance exhausted. Another live verification requires new authorization.

| Phase | Status | Evidence level | Commit / report | Blocker / next step |
|---|---|---|---|---|
| P0 baseline | VERIFIED_OFFLINE | STATIC, UNIT | [Baseline](BASELINE.md) | Python and frontend baseline passed |
| P1 transport | VERIFIED_OFFLINE | REAL_UI_FIXTURE | [Source reuse](TEAM_CHANGES.md) | Interpreter fixture; no live provider |
| P2 guard/compiler | VERIFIED_OFFLINE | UNIT | [Guards](../../astra-frontend/tests/agent-recipes.test.mjs) | Mixed negated requests require clarification |
| P3 context/capabilities | PARTIAL | REAL_UI_FIXTURE | [Inventory](BASELINE.md) | 18 of 34 bound intent IDs observed in browser |
| P4 A/B/C workflows | PARTIAL | REAL_UI_FIXTURE, REAL_HTTP_NO_AI | [Browser smoke](../../scripts/agent_browser_smoke.py) | Browser-local guard added. Backend ownership and full race coverage remain open |
| P5 memory/title | VERIFIED_OFFLINE | REAL_UI_FIXTURE, UNIT | [Memory tests](../../astra-frontend/tests/agent-memory.test.mjs) | Browser-local persistence; shared accounts and durable pending plans absent |
| P6 provider/latency | VERIFIED_OFFLINE | UNIT | [Timing harness](../../astra-frontend/scripts/agent-benchmark.mjs) | Live model eligibility, intent accuracy and p95 require operator verification |
| P7 key gateway/security | VERIFIED_OFFLINE | UNIT, REAL_UI_FIXTURE | [Gateway setup](CLOUDFLARE_GATEWAY_SETUP.md) | Owner reports gateway, stored key and Run token provisioned. Runtime authentication and project model access await live acceptance. |
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

- 2026-11-26 · Codex CLI manual test · Added tool-disabled ephemeral Codex exec with the shared intent schema, 30-second deadline and no fallback. Tested subprocess using a fake process and ran 19 focused Python tests. Native app started with demo MAS and the frontend timeout expanded to 35 seconds. Live inference remains for the user to test.\n\n- 2026-11-26 · Real Codex diagnostic · One authorized endpoint request returned HTTP 200, configuration failure, CLI exit 1 in 6.6 seconds. CLI stderr reported invalid structured-output schema. The detailed error text was truncated by the initial sanitizer. Corrected the schema to require every property, permit null on optional values, remove unsupported constraints, and validate the decoded result. Verified offline for all 34 intent shapes and restarted the app. No second live attempt was made.

- 2026-11-26 · R1–R5 · Parent `7e63bd1`. Added shared vocabulary, catalog-grounded intake, guidance, source-linked memory and automatic titles using the existing compiler. Updated BYOK documentation and classified upstream errors without payload logging. 27 frontend tests, 20 focused Python tests, production build and the mounted semantic-fixture regression passed. No local gateway account ID, gateway ID, Run token or model configuration was present. The old process contained two successful manual Codex responses, OPEN_SETUP and clarify. The new contract and Cloudflare live acceptance remain unverified. The exact manual scenarios and authorization gate are in [Manual acceptance V2](MANUAL_ACCEPTANCE_V2.md).

## Release gates
- 2026-11-26 · Gateway activation, parent `6851fce`. Prepared the ignored local gateway profile for `astra-gateway` with a 30-second deadline, one persisted daily attempt, gateway retries suppressed and fallback disabled. Rebuilt the traced frontend. Board of evidence: 27 frontend checks and 16 focused Python checks passed; loopback UI, health and catalog returned HTTP 200 with demo MAS. Startup reports the missing account ID, Run token and project model by field name. Dashboard alias and project access still require owner confirmation. Zero live attempts.
- LOCAL_APP_READY: VERIFIED_OFFLINE
- ORCHESTRATION_OFFLINE_VERIFIED: PARTIAL
- LIVE_AGENT_VERIFIED: FAILED_APPLICATION_CONTRACT, latest live turn
- LIVE_GENERATION_VERIFIED: BLOCKED_EXTERNAL
- KEY_GATEWAY_READY: VERIFIED_OFFLINE
- KEY_GATEWAY_LIVE_VERIFIED: TRANSPORT_OBSERVED, HTTP 200 and complete Gemini JSON

## Budget / authorization
- Live inference authorized: NO
- Paid fallback authorized: NO
- Website deployment: OUT_OF_SCOPE
- Remote key gateway provisioning authorized: NO
- Push/PR authorized: NO

## Follow main
P8 refreshed origin with prune. Main remained at the audited SHA with 0/0 local divergence. No merge was required.

- 2026-11-26 W0. Resumed at 52a21be on the existing feature worktree. Fetched origin, main divergence 0/0. Integration uses Turn/Decision with generated Python prompt/schema resources. Worker deployment and live inference await authorization. MAS remains demo.

- 2026-11-26 W1-W3. Added TypeScript Worker, generated authoritative contract, SQLite Durable Object admission, fail-closed validation and one-attempt BYOK transport. Added public Worker Python provider and explicit keyless launcher with 30/33/38-second Worker/local/browser deadlines. Direct diagnostic settings preserved. Verification in progress; forwarding disabled.

- 2026-11-26 W4-W5. MAS compatibility inspected: Chat Completions JSON/schema/tool contract, output limit 8192, bounded role retries and multi-call orchestration. No verified Gemini academic compatibility; MAS route absent and counter reserved at zero. Six real local workerd/SQLite DO groups passed including parallel admission, persistent restart, UTC reset, expired leases, input rejection and native BYOK fixtures. Fixed workerd redirect mode to manual after actual runtime rejection. 23 focused Python checks and 27 frontend checks passed; build passed. No remote inference.

- 2026-11-26 W5-W6. Nine local workerd test groups passed with real SQLite DO persistence and synthetic upstream fetch. Covered request/body/schema/credential overrides, missing Secret, kill switch, parallel admission, restart, UTC rollover, expired leases, role ceiling, invalid output, charged timeout and admission failure. TypeScript check and Wrangler production dry run passed. Dependency audit found zero vulnerabilities after matching Wrangler's pinned Miniflare 5 beta. Added generated contract fingerprint checked before inference to prevent deployed/client contract drift.
- 2026-11-26 W5 fresh checkout. Created detached sibling longlth2297-agent-worker-fresh at d323dae, installed independent Python dependencies with pip and npm ci/build without .env, Wrangler or Codex. Real UI, health and catalog returned 200 on port 8011 with demo MAS. LaTeX was detected from this machine; fresh compiler/RAG installation and live AI were not tested. Stopped the temporary server and retained its protected worktree.
- 2026-11-26 W6. Production /health returned Hello World. Wrangler whoami did not confirm authentication. Existing production Worker remains owner-managed. Credential scan of tracked source, outgoing history, browser bundle and built wheel found zero known key-pattern/value matches and no credential-header markers in browser assets. Latest native process restarted on port 8000 with explicit worker transport and demo MAS. W7 awaits authorization; zero remote inference attempts.

## Worker release gates

| Gate | Observed status |
| --- | --- |
| WORKER_IMPLEMENTED | VERIFIED_OFFLINE, production bundle and strict contract |
| QUOTA_PROTECTION_VERIFIED | VERIFIED_OFFLINE for quota races/persistence; production binding/config verified and kill switch observed with zero attempts. Production quota exhaustion remains unexercised. |
| ASTRA_WORKER_PROFILE_VERIFIED_OFFLINE | VERIFIED_OFFLINE, Python contract tests, mounted UI fixtures and credential-free startup |
| WORKER_DEPLOYED | VERIFIED_PRODUCTION, version b0932058-bdf3-46ed-8ac0-e7977207bfec, forwarding false |
| LIVE_GATEWAY_VERIFIED | TRANSPORT_OBSERVED, one admitted attempt returned upstream HTTP 200 for gemini-3.1-flash-lite; semantic response rejected |
| LIVE_AGENT_ORCHESTRATION_VERIFIED | FAILED_APPLICATION_CONTRACT, completed JSON violated semantic consistency; corrected provider grammar remains live-unverified |
| KEYLESS_MAS_GENERATION_VERIFIED | BLOCKED_COMPATIBILITY, existing academic provider contract differs; public MAS route absent |
| FRESH_CLONE_VERIFIED | LOCAL_STARTUP_VERIFIED at d323dae with independent dependency install; remote AI and complete RAG/LaTeX installation unverified |

Use [Worker runbook](WORKER_RUNBOOK.md) and [next task](NEXT_TASK.md). The initial global budget of one is an operator diagnostic setting. Distributed clients rely on centralized quotas and retain local burst/replay guards.

- 2026-11-26 W6 authorized deployment preparation, parent bc1c024. Wrangler authenticated. Existing Worker's gateway account matches the single authenticated account; encrypted Run Secret, astra-gateway and default alias confirmed through version metadata. Selected owner model gemini-3.1-flash-lite without inference availability claim. Prior version d140af7f-75d2-4e0b-a470-1e07741479e8 retained for rollback. Forwarding false; global/Agent allowance one, MAS zero. Production deployment authorized; live inference remains unauthorized.

- 2026-11-26 21:28 ICT W6 production deployment. Owner authorized existing astra-ai-proxy. Deployed source at 333a44e using Wrangler 4.168.0 with keep-vars. Production version 234510ff-c691-4b59-b365-3127c94c2cea at 100%. Previous version d140af7f-75d2-4e0b-a470-1e07741479e8 recorded privately for rollback. ADMISSION namespace 5facb56f387d4f8c8fe723775e04f024 created with class Admission and migration tag v1-admission from new_sqlite_classes. Runtime usage_model remains standard. No account billing setting was changed.
- W6 production configuration. Metadata comparison confirmed all four previous plain-text/secret bindings unchanged, including encrypted Run Secret. Model gemini-3.1-flash-lite, forwarding false, global/Agent daily limits 1/1, MAS 0, concurrency 1, IP/global bursts 3/10 per minute, timeout 30000 ms, output 1024. Health returned 200 with astra-intent-v1 and false; public JSON response required no login. Interpretation GET returned 405 and MAS route 404.
- W6 zero-inference runtime validation. POST to disabled production interpretation returned 503/disabled. The actual local FastAPI Agent endpoint then called the deployed Worker and returned HTTP 200 with temporarily_unavailable/disabled. Production tail recorded request ad684003-63ea-43e5-91f1-cd8856d15d79, admitted=false, attempts=0, category=disabled. Quota reservations and real provider availability were not exercised. Local ASTRA health remained 200 with demoMode=true and mock MAS. W7 has zero live upstream attempts and awaits separate authorization.

- 2026-11-26 W7 preparation, parent 40a4b5b. Owner authorized forwarding and exactly one real UI turn. Added read-only persisted quota health so the remaining allowance can be checked before inference, plus bounded redacted upstream failure diagnostics. Ten local workerd checks passed. No live attempt sent yet.

- 2026-11-26 W7 single live UI attempt. Global allowance verified as 1 from persisted read-only health, then enabled version e338764b-bedf-4f2c-939c-84412b3cb121. Exact requested sentence required model interpretation and was entered once in a fresh real Edge chat. Turn 3611130c-5059-4a8c-8ad0-0354173e2cdd reached Worker request f6c188e1-1739-459b-aa7e-d81164542316. Admitted=true, upstream attempts=1, upstream HTTP=200, provider google-ai-studio, model gemini-3.1-flash-lite. Worker rejected the response as schema after 3610 ms. Browser model route measured 3955 ms, local HTTP turn 4004.6 ms, visible response 4009.3 ms. One Agent request and zero business writes. Local response was temporarily_unavailable/schema. THPT resolution and subject clarification did not occur. Forwarding disabled again at version 4e94ac52-39cd-4b00-95ff-a2304400a02a; persisted remainingAttempts=0, activeReservations=0.
- W7 offline investigation. Production trace had outcome ok, no exceptions, upstream HTTP 200, category schema. The first instrumentation discarded completion metadata and validation details, so its exact failed field/finish reason cannot be recovered. Fixed this verified diagnostic defect by recording schema stage, candidate completion, safe token counts, byte count and validation paths/keywords without teacher text. Eleven local workerd groups passed; targeted parser/quota checks and TypeScript passed after final refinement. Incomplete, invalid JSON and invalid semantic responses remain rejected. No second live attempt.

- W7 final state. Offline diagnostic fix deployed with forwarding false as b0932058-bdf3-46ed-8ac0-e7977207bfec. Health confirmed remainingAttempts=0 and activeReservations=0 after deployment, proving consumed quota survived redeployment. MAS health remains demoMode=true. Exact provider finish reason/invalid field remains unknown because the first schema trace omitted it. Further inference requires new authorization and an explicitly approved allowance. Evidence remains in ignored runs/live-worker-one/result.json, tail.private.json and actual-response.png.

- 2026-11-26 structured-output investigation, parent 3574a88. Inspected envelope, selection, extraction, JSON, provider validation, Python validation and compiler. First failed payload remains unavailable. Verified provider/internal optional-null mismatch and redundant non-task intents requirement. Generated provider schema reduced from 11014 to 3026 bytes while the full 34-intent schema remains authoritative after normalization. Explicit MINIMAL thinking is documented for this model and confirmed by v1 discovery. Retained output limit 1024. Added precise blocked/empty/truncated/provider/application validation metadata; no live attempt yet.
- Structured-output offline checkpoint. Fifteen Worker groups passed, including all 34 action variants and documented Gemini envelope/error fixtures; 23 focused Python checks passed. Provider schema shrank 72.5 percent. Backend restarted with synchronized fingerprint. Owner authorized one additional inference; plan raises global/Agent ceilings 1 to 2 while preserving the already consumed attempt, then disables forwarding immediately after one fresh UI submission.

- 2026-11-26 additional authorized live UI turn. Preserved consumed quota and raised global/Agent daily ceilings from 1 to 2. Before enable remaining=0; after enable remaining=1. Exactly one fresh UI submission, turn 0a3ee1db-6a10-45ca-a04e-50dd655ab6d8, Worker 6a66b6fb-b5bc-41ce-84cf-147bd3cc4dc2. Upstream HTTP 200, one candidate, STOP, application/json, valid JSON, one final text part, 158 text bytes, 2373 prompt tokens and 70 output tokens. No thought token count reported. Provider elapsed 2042 ms, Worker 2228 ms, browser interpretation 2897 ms, total visible response 2955.7 ms. Failure stage application_contract with semantic_invariant after both structural validators passed. No exam/business writes. Disabled immediately as version 4c4cb939-d0d3-4975-89f8-9c50fc29527b; remaining=0, active=0.
- Verified root cause class. Provider grammar allowed cross-field combinations prohibited by the application's validator. Corrected generated provider schema to four exclusive alternatives: action, intake, guidance and plain non-action. Required action arrays contain at least one entry; non-action arrays remain empty. All prior strict argument and UI guards stay active. Final provider schema is 3832 bytes versus 11014 internal bytes. Sixteen local workerd groups passed including cross-field regression and every existing intent. Exact subtype among the prior combined semantic checks was not retained, so historical provider contents are not fabricated. No third inference attempt.

- Final structured-output checkpoint. Deployed correction d588368 as production version bb165c28-5a06-4372-9c9e-b2bf758b9599 with forwarding false. Metadata confirmed original four gateway/Secret bindings unchanged, global/Agent ceilings 2 and selected model unchanged. Read-only health after redeployment reports remainingAttempts=0 and activeReservations=0. Local server restarted with the final exported fingerprint, distributed Worker provider and demo MAS. No third inference call. WORKER_RUNBOOK.md records the pipeline audit, official Gemini parameter sources and deferred OpenAI/Anthropic fallback evaluation. NEXT_TASK.md records the exact authorization boundary and live evidence.
