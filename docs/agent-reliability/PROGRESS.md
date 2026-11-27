# Agent reliability and persistent generation recovery

For the owner and next engineer. Active branch: `feat/longlth2297/agent-reliability-resume`, cut directly from `origin/main` **98b1df5467255b5de94f0b3191b5613db33bd48a** on 2026-11-28. Previous worktrees and the dirty original main checkout are preserved. Local commits only; no push, PR, main modification or Cloudflare deployment is authorized for this task. No real AI request is permitted for verification.

## Observed baseline

- Main already contains the semantic Agent, local recipes, workflow resolver, execution receipts, browser/server workspace integration, independent Chat/MAS Workers, upload/search/export additions, generation stop/continue and question-regeneration stop controls. No old branch needs a wholesale merge.
- Current continue creates a **new job ID** and copies prior checkpoint sources. Restart marks queued/running jobs failed; no durable paused lifecycle or exclusive execution claim exists. A stop cancels the task and can discard an in-flight valid response before it reaches the checkpoint.
- Native orchestration already has content-addressed response checkpoints shared by THPT, V-ACT and subject profiles. Writes are not atomic; restoration assumes result.json exists, and fingerprints omit provider identity. This is the foundation to extend, preserving native academic validators and algorithms.
- RecordingProvider owns native transport retries (one retry for most stages); Agent.run separately owns structured-output repair. Worker/Gateway each attempt upstream once. MAS Worker currently collapses upstream errors, obscuring permanent versus transient failures. Chat Router has deadlines/fallback/circuit handling but no explicit safe retry classification.
- Verified integration gaps include local routing still calling Word export/upload/web features unsupported despite main implementing them; lifecycle commands lack Agent bindings. Existing benchmark is a small hand-entered corpus rather than a grouped held-out routing evaluation.

## Implementation sequence

1. Extend existing checkpoint persistence and job lifecycle with atomic checkpoints, execution fencing, safe pause boundaries and same-job explicit resume/retry; keep cancellation distinct and restart inference opt-in.
2. Coordinate bounded retry classification/backoff with existing retry owners and pause signals; preserve sanitized Worker error metadata. Prepare Worker changes locally only and document deployment/compatibility.
3. Bind lifecycle and newly supported application actions into the existing Agent/UI. Expand compositional Vietnamese local routing and evaluate grouped development/held-out scenarios with no HTTP/model adapter.
4. Run focused fake-provider and real-local-persistence regressions, verify the actual entry point without inference, and leave the real configuration ready for owner UI acceptance.

Verification at this initial checkpoint: source/history inspection only; no tests or inference run. Findings above are implementation observations, not live quality/performance claims.
