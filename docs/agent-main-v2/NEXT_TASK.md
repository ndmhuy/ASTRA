# Next task: approve and observe one real MAS exam

For the owner/next engineer in the existing feat/longlth2297/agent-main-v2 worktree. Current scope: [MAS specification](MAS_CLOUDFLARE_SPEC.md) and [MAS runbook](MAS_WORKER_RUNBOOK.md). Worker implementation cfbf951; Backend integration/readiness accompanies this checkpoint. Earlier Chat-only and no-MAS authorization blockers are historical.

## Current MAS gate

- Application for MAS acceptance: **http://localhost:8001**, actual Backend demoMode=false/providerConfigured=true. The old 8000 process remains the demo profile; use 8001. Restart using `.venv-win/Scripts/python.exe scripts/start_mas_worker.py --port 8001` and the existing ignored .env.mas-worker profile. No Gemini/Gateway key is needed locally; only the revocable Worker caller credential.
- Existing MAS Worker final version aa62dcd7-ab17-4c31-b282-745634d05d3c, model gemini-3.1-flash-lite, independent astra-mas-gateway/default BYOK. Actual deployed Secrets and prior Gateway bindings preserved. Forwarding=false, total/daily/token limits zero, used=0. Never replace this with the Chat Worker or its credential.
- No owner-approved MAS inference has occurred. Specification section 7 explicitly requires access-policy/budget approval first. Concrete proposal: internal revocable bearer access; owner starts exactly one standard Toán THPT 22-question/90-minute exam; maximum 41 upstream calls, 4000000 conservative reservation units, two-hour activation window. See runbook for derivation, payload limits, exact deployment steps and acceptance evidence to capture. Do not silently reset counters or auto-run the exam.
- After approval, activate through the existing Worker with bounded quotas and expiry, verify metadata/health, then let the owner submit through the current UI. Keep native RAG/Composer/Illustrator/Blind Solver/Reviewer/validation unchanged. Worker has no academic orchestration. No website/Backend deployment, push, PR, merge or new Gateway/Worker.
- Actual disabled checks passed: wrong/no caller token401, correct token with forwarding disabled503, used remains0. 10 Worker groups,17 focused Python checks, real RAG22-context preflight, and non-demo mounted browser passed. Synthetic HTTP academic completions are explicitly fixtures, not live Gemini acceptance. Independent Chat responsiveness during a blocked MAS request passed locally; live concurrent Chat/MAS remains for owner acceptance.
- Latest fetched origin/main d67d218c has 36 missing commits; no integration performed. Earlier unrelated RAG lint findings remain outside scope.

## Prior Chat checkpoint (historical; MAS information below is superseded)

The real natural THPT to subject question to local Mathematics to actual setup path works. Stored-format recall was corrected and verified live; unsupported Chemistry and home navigation passed. One V-ACT switch timed out upstream at 30 seconds and still needs manual acceptance. Zero exam writes. Eight automated upstream attempts consumed: seven valid frames, one timeout. Two harness-context mistakes count but are excluded from contextual acceptance.

## Current runtime and owner allowance

- Open http://localhost:8000. Actual keyless Worker-profile app remains running here; MAS demo, no local token or private fallback. Reload opens home; select the existing sidebar chat to continue it.
- Latest owner request authorizes 20 additional manual calls instead of the previous four. Actual preserved usage was already 12 when checked; total session/global/Agent ceilings are now 32, leaving 20. Same session astra-chat-acceptance-20261127-0205, no reset. Current expiry 2026-11-27 05:40 UTC / 12:40 Asia/Bangkok. Deployment b5fe6c1f-cafe-4583-ad72-309ba8c38150; actual metadata/health verified used=12, limit=32, remaining=20, forwarding enabled, MAS disabled. ASTRA's allowance is not a measurement of Gemini quota. No inference was consumed in this update. This supersedes the earlier 12-total authorization and both earlier windows.
- Both contracts retained; semantic hash 27addb54bfcb694d5cd838671cf1a1662829eec84b365cba48e24e6a2500b7d4. Existing Gemini 3.1 Flash Lite / astra-gateway / BYOK default.
- Session allowance/expiry survive UTC rollover/restart. Public traffic consumes the same cap. Read /health.quota.diagnostic and root remainingAttempts, not raw daily workload remainder. After expiry inference is blocked even if forwarding flag stays true.
- Automation is exhausted: do not run agent_live_acceptance.py again. Follow the four-step owner script in LIVE_CHAT_RESULTS.md. Subject continuation and exact format recall can be local; natural intake/switch/recall usually use the model. Maximum three/IP/minute.
- Setup modal blocks chat. Escape/close/Cancel preserves intake; then continue. No generation/confirmation clicks during Chat-only acceptance.

If the app exits, run `.venv-win/Scripts/python.exe scripts/start_agent_worker.py --port 8000` in this worktree. Startup makes no inference and bypasses the preserved private .env. After expiry leave the window closed; renewal needs owner direction, retaining session usage. To close early, in workers/astra-ai-proxy set ASTRA_FORWARDING_ENABLED=false in existing ignored .wrangler/live-chat-session.jsonc, deploy that same config and verify /health.forwarding=false. Never recreate/reset storage. Historical rollback code bb165c28-5a06-4372-9c9e-b2bf758b9599 is only safe after disabling forwarding.

## Remaining release gates

- Record owner family-switch/manual behavior. Full live acceptance remains conditional; corrected recall is development evidence. Core Chat can be reviewed; PR preparation also needs owner acceptance and upstream compatibility. No push/PR/merge authorized here.
- Latest fetched origin/main 0adcc468 has 30 commits missing here. No automatic merge/rebase. Preserve existing worktree and protected fresh clone ../longlth2297-semantic-fresh-20261127.
- Focused checks passed: 23 Python, 40 frontend, 22 Worker groups, contracts, lint/build. Repository verify.py fails on 91 existing Ruff findings in unchanged RAG code. Address separately before claiming the entire repository green.
- Independent MAS provider/credential/quota pool and caller authorization remain unavailable. MAS daily=0 and forwarding false. Do not use Chat credentials for academic generation.
- The 197-record/scenario corpus is unchanged. Independent NLU accuracy and population p95 remain unmeasured; expansion to 700 is not a substitute for evaluation.
