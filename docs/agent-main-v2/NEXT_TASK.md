# Next task: owner manual Chat acceptance

For the owner/next engineer in the existing feat/longlth2297/agent-main-v2 worktree. Implementation d59294e; read [live report](LIVE_CHAT_RESULTS.md), [actual predictions](../../eval/agent-semantic/live-20261127.json) and [current authorization](LIVE_CHAT_COMPLETION_SPEC.md). Older deployment/inference blockers are historical.

The real natural THPT to subject question to local Mathematics to actual setup path works. Stored-format recall was corrected and verified live; unsupported Chemistry and home navigation passed. One V-ACT switch timed out upstream at 30 seconds and still needs manual acceptance. Zero exam writes. Eight automated upstream attempts consumed: seven valid frames, one timeout. Two harness-context mistakes count but are excluded from contextual acceptance.

## Current runtime and owner allowance

- Open http://localhost:8000. Actual keyless Worker-profile app remains running here; MAS demo, no local token or private fallback. Reload opens home; select the existing sidebar chat to continue it.
- Owner explicitly requested reopening the four unused attempts after the first window expired. Same persistent session astra-chat-acceptance-20261127-0205, used=8, limit=12; no counters reset or ceilings increased. Current expiry 2026-11-27 05:05 UTC / 12:05 Asia/Bangkok. Current deployment 6e8c5f3d-a116-4c94-8ae1-40ad14d685f1; metadata/health verified forwarding enabled, remaining=4, MAS disabled. These are ASTRA admission limits, not a measurement of the remaining Gemini quota. No inference was consumed when reopening.
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
