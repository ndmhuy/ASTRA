# Live Chat acceptance — 2026-11-27

For the owner/team reviewing the existing Chat candidate. Authorization: [completion specification](LIVE_CHAT_COMPLETION_SPEC.md). Implementation d59294e. [Machine-readable live predictions](../../eval/agent-semantic/live-20261127.json) are separate from the unchanged 197-record/scenario oracle corpus. No fixture responses or business mocks were used in these real browser turns.

Owner follow-up: the initial 09:40 window expired with all four manual attempts unused. On explicit request, reopened until 2026-11-27 12:05 Asia/Bangkok / 05:05 UTC, deployment 6e8c5f3d-a116-4c94-8ae1-40ad14d685f1. Same session used=8/limit=12, remaining=4; no inference, reset or limit increase. This supersedes the initial window below. Four is ASTRA's configured allowance, not observed remaining Gemini quota.

## Infrastructure and accounting

Existing astra-ai-proxy / astra-gateway / default BYOK / gemini-3.1-flash-lite. Initial disabled rollout 1df26001-8253-4be4-b246-fa2b326c1be5 verified both contracts, encrypted Gateway Token Secret, unchanged ADMISSION namespace 5facb56f387d4f8c8fe723775e04f024, Admission class, global-v1 identity and v1-admission migration. No resource/storage recreation or credential retrieval. Rollback code reference bb165c28-5a06-4372-9c9e-b2bf758b9599: disable forwarding and verify disabled configuration before rollback, since old code lacks session enforcement.

Both astra-intent-v1 and astra-semantic-v1 remain available. Current semantic hash 27addb54bfcb694d5cd838671cf1a1662829eec84b365cba48e24e6a2500b7d4; initial hash e0cacdee692c80c18b2fb94a810b3b15e1fb80c381f331f21cca823bdf3ae7dc changed with the recall catalog correction and regenerated contracts. Legacy hash unchanged. Disabled correction rollout 92ef3674-d7ba-4bc4-9666-5ad131115b56 preceded resumed acceptance d2008f79-99ca-4ec1-83d7-92ba19d30c7f. Automation ended disabled at 1fafb5be-5e67-4e86-a28c-7b3374990878. Final manual deployment is recorded in NEXT_TASK.md.

UTC ledger day 2026-11-27 started at zero consumed, old daily ceilings two. Daily ceiling increased once to 12. Same persistent session astra-chat-acceptance-20261127-0205 used=8, automation limit 8; only the reserved owner phase raises its limit to 12, preserving used=8. Absolute expiry and session usage survive UTC rollover/restart. Old daily counters are archived on rollover; no resets/refunds/new session IDs. Root quota.remainingAttempts includes the session limit; workloads.agent.remainingAttempts is the raw daily remainder, not the diagnostic allowance.

Estimated daily token reservation ceiling 700000 is conservative byte-based admission accounting, not billed/actual token usage. Strict total session maximum remains 12 attempts. Concurrency 1, IP/minute 3, global/minute 10, upstream deadline 30000 ms, output maximum 1024. MAS daily 0/forwarding false; BYOK-only, no paid/wholesale fallback, Gateway maximum attempts 1, no cache/payload logging. No website/Backend deployment.

## Real product observations

| Turn | Observed result | Calls | Visible ms | Provider ms | Prompt/output tokens |
|---|---|---:|---:|---:|---:|
| Natural THPT intake | PREPARE_EXAM family=thpt; visible subject question | 1 | 2216 | 1630 | 1515 / 73 |
| Subject in accidentally new chat | Valid INFORM/Toán; asks missing family; context acceptance excluded | 1 | 1935 | 1387 | 1498 / 69 |
| Recall in accidentally new chat | Valid recall; truthfully no previous request; memory acceptance excluded | 1 | 2076 | 1848 | 1511 / 72 |
| Same-chat “Môn Toán nhé.” | Local; actual thpt-math setup selected, 22 questions/90 minutes | 0 | 152 | — | — |
| Recall before fix | INFORM/what=first; resolver rejected act, no remembered answer | 1 | 2614 | 1684 | 1655 / 71 |
| Recall after fix | QUESTION/what=format; actual stored Toán THPT/source returned | 1 | 3100 | 1983 | 1742 / 73 |
| Chemistry correction | CORRECT/PREPARE_EXAM; unsupported Hóa Học, no substitution | 1 | 3029 | 2525 | 1765 / 83 |
| Switch to V-ACT, no generation | Upstream deadline; no frame or setup change | 1 | 30342 | 30000 deadline | unavailable |
| Ask how to download Word | Local general prerequisites; no export or mutation | 0 | 146 | — | — |
| Unfamiliar home navigation | REQUEST/RETURN_HOME; actual start screen and stored success receipt | 1 | 4774 | 4385 | 1794 / 52 |

Eight upstream attempts: seven canonical HTTP 200 responses, one timeout. Product evidence is narrower: four successful remote workflows, one corrected product failure, two harness exclusions, one timeout, plus two local successes. The harness mistakenly launched fresh conversations for two calls; these are retained and fully counted. Later turns reopen the original chat through its actual sidebar button. Before/after session usage matched every observed attempt; no unrelated admissions observed. Browser business-write monitoring and server access logs show zero exam generation/approval/export requests, all sessions draft, no jobs/questions. No separate title inference.

The timeout occurred awaiting Gateway/provider response headers, before extraction/validation. No upstream HTTP status, finish reason, token usage or conflicting semantic fields exists. Provider overload, exhausted quota and the responsible network hop are unconfirmed. A later deliberately different navigation call succeeded; no blind switch retry was made. Family-switch live acceptance remains open. Out-of-scope and spam/duplicates were not additionally exercised live; prior offline checks remain separate.

Timings include a 100 ms browser settling interval and automation overhead. Local endpoint, Worker and combined Gateway/provider elapsed are available; individual context/serialization/extraction/validation/React phases are not separately instrumented. Successful remote turns ranged 1.935–4.774 seconds; the 30.342-second timeout remains in reliability evidence. No population p95. First prompt 1515/output 73 versus historical 2373/70 is an observation, not a controlled improvement claim: messages/contracts/context differ.

## Corrections, verification and limitations

Pending-subject parsing accepts a subject prefix and polite suffix, still abstaining on negation/richer sentences. Same-chat subject continuation made zero Agent HTTP/model calls. Immediate pending text appears during remote turns; existing abort/stale-state protections remain. Safe Worker telemetry allowlists structural diagnostics, timing and usage, never raw provider text/credentials. Required validation, confirmation and receipt checks remain intact.

Recall was fixed in the catalog: explicit literal-first versus current-format meaning and INFORM/QUESTION eligibility for this read-only goal. Regression also rejects INFORM navigation. Subsequent live prediction selected what=format and returned stored state. This repeated tuned sample is development evidence, not independent NLU evaluation. No hardcoded failed sentence or extra inference for titles.

Modal limitation confirmed: backdrop and aria-modal focus trap block background chat. Escape/close/Huỷ returns to chat and preserves intake; reopening uses authoritative state. Simultaneous chat would alter teammate presentation/focus ownership, so it is deferred. No focus/confirmation weakening. The existing “Không tốn phí AI” setup badge refers to selecting setup, not live academic generation.

Passed: 23 focused Python, 40 frontend, lint/build, Worker TypeScript/22 workerd groups, both generated-contract checks, targeted Ruff and diff checks. Existing build chunk advisory and Starlette/httpx warning remain. scripts/verify.py stops at 91 Ruff findings in 14 unchanged rag_workflow files; repository-wide gate is not green. Detailed ignored artifacts: runs/live-chat/*.json/png and runs/live-chat-server*.log. The live harness never intercepts responses; expected meanings were saved before submission. Some expected subject slots use English conceptual labels; actual canonical equivalents Toán Học/Hóa Học are recorded unchanged.

## Owner manual test

Actual app http://localhost:8000 from this feature worktree, explicit keyless launcher, demoMode=true and providerConfigured=false for MAS. Private .env preserved/bypassed. Reload starts home: reopen an existing sidebar chat before continuing it. The automated browser used isolated storage; normal owner browser starts independently.

Four owner attempts remain under the same session total 12, expiry 2026-11-27 02:40 UTC / 09:40 Asia/Bangkok. Public unrelated traffic consumes this same cap. After expiry, requests are rejected even if /health.forwarding remains true. Do not extend the window or rotate/reset the session without renewed owner direction. Exact local commands remain usable after expiry. Final deployment metadata is in NEXT_TASK.md.

Use one conversation; do not click generation/confirmation controls:

1. “Cô cần chuẩn bị một bài thi thử tốt nghiệp, mình nên bắt đầu từ đâu?” Remote expected: THPT, ask subject, no generation.
2. “Môn Toán nhé.” Local with pending subject: actual Toán THPT setup, 22 questions/90 minutes. Escape before chatting.
3. “Chuyển sang V-ACT giúp cô, chỉ chọn mẫu, chưa tạo đề.” Remote expected: V-ACT setup, obsolete THPT subject cleared, no generation. This remains unresolved live. Escape.
4. “Mình đang chọn mẫu nào, nhắc lại cho cô?” Remote likely: stored V-ACT, no fabricated exam. Alternatively request supported navigation. Exact “Nhắc lại mẫu đề đã chọn” is local.

Normally three remote calls; the fourth is reserved, not required. Respect three/IP/minute. A timeout/failure consumes a slot; do not repeatedly submit.

Core Chat is ready for team review. Full acceptance remains conditional on manual/family-switch results; production readiness is not established. Latest origin/main 0adcc468 has 30 unintegrated commits. Independent NLU accuracy remains unmeasured. Future MAS may favor a separate authenticated Worker/Gateway for paid APIs, larger requests/longer deadlines and deployment isolation; a private existing-Worker operation could reuse admission policies if limits align. Both require actual provider/credential/caller-authorization decisions first. No remote MAS forwarding was implemented.
