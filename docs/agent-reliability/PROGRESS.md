# Agent reliability and persistent generation recovery

For the owner and next engineer. Active branch: `feat/longlth2297/agent-reliability-resume`, cut directly from `origin/main` **98b1df5467255b5de94f0b3191b5613db33bd48a** on 2026-11-28. Previous worktrees and the dirty original main checkout are preserved. Local commits only; no push, PR, main modification or Cloudflare deployment is authorized for this task. No real AI request is permitted for verification.

## Observed baseline

- Main already contains the semantic Agent, local recipes, workflow resolver, execution receipts, browser/server workspace integration, independent Chat/MAS Workers, upload/search/export additions, generation stop/continue and question-regeneration stop controls. No old branch needs a wholesale merge.
- Current continue creates a **new job ID** and copies prior checkpoint sources. Restart marks queued/running jobs failed; no durable paused lifecycle or exclusive execution claim exists. A stop cancels the task and can discard an in-flight valid response before it reaches the checkpoint.
- Native orchestration already has content-addressed response checkpoints shared by THPT, V-ACT and subject profiles. Writes are not atomic; restoration assumes result.json exists, and fingerprints omit provider identity. This is the foundation to extend, preserving native academic validators and algorithms.
- RecordingProvider owns native transport retries (one retry for most stages); Agent.run separately owns structured-output repair. Worker/Gateway each attempt upstream once. Current MAS Worker already preserves HTTP status, but drops Retry-After and structured daily-quota versus temporary-rate metadata. Chat Router has deadlines/fallback/circuit handling but no explicit safe retry classification.
- Verified integration gaps include local routing still calling Word export/upload/web features unsupported despite main implementing them; lifecycle commands lack Agent bindings. Existing benchmark is a small hand-entered corpus rather than a grouped held-out routing evaluation.

## Implementation sequence

1. Extend existing checkpoint persistence and job lifecycle with atomic checkpoints, execution fencing, safe pause boundaries and same-job explicit resume/retry; keep cancellation distinct and restart inference opt-in.
2. Coordinate bounded retry classification/backoff with existing retry owners and pause signals; preserve sanitized Worker error metadata. Prepare Worker changes locally only and document deployment/compatibility.
3. Bind lifecycle and newly supported application actions into the existing Agent/UI. Expand compositional Vietnamese local routing and evaluate grouped development/held-out scenarios with no HTTP/model adapter.
4. Run focused fake-provider and real-local-persistence regressions, verify the actual entry point without inference, and leave the real configuration ready for owner UI acceptance.

Verification at this initial checkpoint: source/history inspection only; no tests or inference run. Findings above are implementation observations, not live quality/performance claims.

## Implemented locally: durable execution foundation

- `4d8d483`: atomic native JSON checkpoints, versioned request/provider/template manifests, operation-bound response digests and academic contract restoration, completed artifact hashes, durable pre-attempt records and cooperative control/fenced-writer hooks.35 focused deterministic THPT checks passed.
- Extended the existing SQLite job store with execution versions, renewable ownership leases and transactional checkpoint/file fencing. Pause waits for a valid in-flight response to be persisted; cancel retains main's transport cancellation behavior. Explicit resume/retry continues the same job and increments its execution version; duplicate resume is idempotent and stale controls fail409. No inference starts automatically after abandoned-lease recovery/restart.
- Generation control API requests carry an execution version. Native section/batch outputs remain actual validated response checkpoints, indexed in the job record; retrying a completed valid section is unnecessary. Existing question-regeneration cancellation and completed-exam version/export logic are retained. Existing continue regression was updated to assert the newly required same-job behavior rather than a replacement exam ID.
-11 focused persistence/checkpoint/stop tests passed, including pause during a real asynchronous **fake** response, persisted16-question progress, Backend restart without calls, same-job resume with only P3 requested, duplicate resume, stale controls, queued pause with zero calls, lease exclusion/expiry and rejecting late writes. This is offline evidence only. UI bindings, coordinated retry and routing evaluation remain in progress.

## Implemented locally: coordinated transport recovery

- One versioned policy config bounds native transport retries (default two attempts; Reviewer retains its existing single transport attempt), jitter/backoff/deadlines and executor timing. Native Agent schema repair stays separate. HTTP adapters, Workers and Gateways do not add retries; Worker/Gateway upstream attempts remain one. Stable operation fingerprints and distinct attempt IDs are recorded before requests and sent as optional MAS trace headers.
- Distinguish safe connection failures, temporary HTTP failures, explicit rate limiting, daily quota exhaustion, auth/model/request failures and uncertain response timeouts. Unknown legacy proxy/quota errors are conservative and do not auto-retry. Chat only automatically retries proven pre-admission failures or connection failures, preserving its original turn ID/deadline; admitted/uncertain inference is not replayed.
- Backend retry waits are pause-aware. Recoverable exhaustion pauses the job; uncertain completion becomes interrupted and requires explicit resume. Retry-After is never shortened and its not-before time persists across pause/restart. Native academic repair, validation and completed checkpoints are preserved.
- Prepared MAS Worker changes locally: sanitized upstream category/Retry-After metadata, capacity versus internal budget distinction and optional operation/attempt trace validation. No remote deployment, credential/model/limit change or billing action occurred. Existing deployments still work; richer Worker error metadata needs a separately authorized deployment.
-63 focused Python fake-provider/API/persistence regressions and14 local Miniflare MAS Worker groups passed; Worker TypeScript passed. Tests cover exact attempt counts, no adapter retry multiplication, auth/quota no retry, safe Chat retry, backend backoff pause, Retry-After after restart, bounded503 recovery and manual same-job retry. No live inference was used. UI and routing/dataset work remain underway.
