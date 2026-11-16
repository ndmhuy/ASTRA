# Connection and execution fixes — 2026-11-16

Reported symptom: every chat turn returned HTTP_502. Inspection found Vite listening on
5173 with no process listening on Agent port 8010. The earlier dev command launched only
the UI, and the UI's generic error gave no useful recovery instructions.

## Changes

- `npm run dev` launches the offline Agent, verifies `/agent/health`, then launches Vite.
  Missing Python, import errors, wrong/occupied Agent port fail before UI startup.
  `dev:ui` retains the separate-server workflow. No keys or generation service are loaded.
- HTTP transient errors 502/503/504, network failure and timeout get one same-payload retry.
  Protocol validation errors are not retried automatically.
- Failed turns remain pending in a controller ledger. The visible retry control uses the
  same turn ID or, after execution, the same feedback ID and results. It does not append
  another user message or execute an already completed effect.
- Duplicate submits are blocked synchronously, prior to React's pending-state commit.
  Both initial and final responses are checked for conversation/request correlation.
  A deleted origin workspace cannot trigger a late UI action.
- Executor validates its own inputs, serializes concurrent plans, checks current availability,
  and rejects changed plan contents under an existing plan ID.
- Modal/sidebar receipts check the actual committed state. UI context version now changes on
  additional manual navigation, modal close, and session deletion paths. Commit observation
  uses bounded timer polling, including background tabs where animation frames can pause.
- Branched sessions do not inherit Agent pending/error state from their source.
- Negated/hypothetical UI commands ask for clarification instead of issuing an effect.

## Verification

Frontend unit tests cover 502 recovery, exact request/receipt replay, duplicate submits,
HTTP retry, parser, executor concurrency, unavailable actions and store isolation.
Four headless Chrome tests use the real React app and Python Agent through Vite:

1. Collapse/expand sidebar, open setup, navigate to library, reopen origin and see final reply.
2. Force 502 on turns, recover connection, retry with one user message and the expected effect.
3. Force receipt failure after creation, retry settlement, verify exactly two total sessions.
4. Manually navigate during delayed turn, verify the stale plan does not override navigation.

Results: frontend unit 16 pass; browser 4 pass; Python full suite 354 pass with one existing
Starlette/httpx deprecation warning. Build and Ruff pass. Frontend lint retains two existing
escape warnings. Vite retains the existing bundle-size warning.

## Limits

This repairs the local M1/M2 path. Requirements evaluation and generation remain fixtures;
production authentication, durable state, cross-restart recovery, arbitrary multi-intent execution
and global chat outside a workspace are separate work. No claim of fixing unobserved unrelated
Backend behavior is made. All changes remain on the owner's M2 feature branch for UI/UX review.
