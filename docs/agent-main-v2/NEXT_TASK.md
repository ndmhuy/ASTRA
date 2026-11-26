# Resume after the single live Worker attempt

For feat/longlth2297/agent-main-v2 in the existing feature worktree. Fetch and inspect current HEAD before editing. W7 ran exactly one authorized real UI request and failed response validation. Do not repeat it without new authorization.

## Actual evidence

Input was ?C? mu?n t?o m?t ?? thi th? t?t nghi?p.? in a new Edge browser chat. It bypassed the deterministic fast path.

- Local turn ID 3611130c-5059-4a8c-8ad0-0354173e2cdd.
- Worker request ID f6c188e1-1739-459b-aa7e-d81164542316.
- Admission true, one upstream attempt, Google AI Studio, gemini-3.1-flash-lite, upstream HTTP 200.
- Worker elapsed 3610 ms; browser interpretation 3955 ms; total visible response 4009.3 ms.
- Local FastAPI returned HTTP 200 with temporarily_unavailable/schema.
- Visible response was ?K?t qu? t? AI ch?a ??c ???c. Th?y c? c? th? g?i m?t y?u c?u ng?n, v? d? ?Ch?n V-ACT?.?
- One Agent request and zero business/exam-generation writes. No THPT intake, subject clarification or business instruction was executed.

## Current state

Forwarding is disabled on production version b0932058-bdf3-46ed-8ac0-e7977207bfec. Persisted health after redeployment showed remainingAttempts=0 and activeReservations=0 for UTC 2026-11-26. Keep global-v1 and ADMISSION storage intact. Local ASTRA remains at http://127.0.0.1:8000 with Worker transport and mock/demo MAS.

The original trace recorded only schema, upstream status and timings. The provider body was discarded and gateway payload collection was disabled. Its exact failed field, completion reason and raw semantic response cannot be recovered from the recorded evidence.

The verified diagnostic defect is fixed offline. Current Worker logs report the parsing/validation stage, candidate count, finish reason, bounded numeric token metadata, text byte count and schema validation paths/keywords. Eleven local workerd groups passed. Targeted final parser/quota tests and TypeScript check passed. Parser constraints and UI safety remain enforced. This diagnostic fix has been deployed with forwarding disabled.

## Authorized next work boundary

1. Review ignored runs/live-worker-one/result.json and tail.private.json. Screenshot actual-response.png shows the real failure.
2. Obtain new authorization for one diagnostic inference and an explicit allowance. The previous one-attempt authorization is consumed. Do not reset or delete quota storage. The UTC rollover alone does not grant authorization.
3. With approval, verify/read remaining quota, deploy/enable only the approved profile and make one controlled real UI request. Disable forwarding afterward. Preserve the model and fallback-disabled policy unless the owner directs otherwise.
4. Read the detailed schema-stage metadata before proposing a parser, token-budget or generation-parameter correction. Do not assume truncated output, a null field or a schema violation caused the first failure without evidence.
5. A successful semantic response must still produce actual THPT subject clarification with zero generation requests. Multi-turn acceptance requires its own approved budget.

Production rollback history and setup commands are in WORKER_RUNBOOK.md. Shared credentials remain remote. MAS public inference is absent pending academic provider compatibility.
