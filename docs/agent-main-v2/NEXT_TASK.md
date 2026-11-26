# Resume after production Worker deployment

For the next session on feat/longlth2297/agent-main-v2 in the existing feature worktree. Fetch origin and inspect Git state before editing. W6 deployment is complete. Continue at the W7 live authorization gate.

Production Worker astra-ai-proxy is deployed at https://astra-ai-proxy.letranhoanglong2227.workers.dev with version 234510ff-c691-4b59-b365-3127c94c2cea. Source checkpoint is 333a44e, followed by deployment documentation commits. Existing gateway variables and encrypted Secret were preserved. ADMISSION uses SQLite migration v1-admission and stable object name global-v1.

Configured model is gemini-3.1-flash-lite, selected by the owner. Availability for the stored Google project remains unverified. Forwarding is false. Global/Agent attempts are 1/1 per UTC day, MAS zero, concurrency one, IP/global bursts 3/10 per minute. No upstream inference occurred.

1. Read PROGRESS.md and WORKER_RUNBOOK.md. Do not repeat implementation or deployment without a concrete reason.
2. Await explicit owner authorization to enable production forwarding and run exactly one live interpretation. The owner has authorized deployment only.
3. After that authorization, verify public health and local demo MAS health, confirm current bindings and remaining diagnostic allowance, then enable ASTRA_FORWARDING_ENABLED centrally. Preserve credentials and model.
4. Send the approved test once through the actual local ASTRA entry point. Use ?C? mu?n t?o m?t ?? thi th? t?t nghi?p.? Confirm it reaches the model, resolves THPT and asks for a subject with zero generation calls. Capture turn/request IDs, admission, attempts, provider/model, HTTP status, latency, semantic output and visible reply.
5. If it fails, investigate the observed category offline. Another inference attempt requires fresh authorization. Keep automatic retries/fallback disabled.
6. After first success, obtain the approved budget for multi-turn manual acceptance. A single successful turn does not establish the full Agent or MAS behavior.

Production health and disabled rejection were verified without inference. A real local /agent/turn reached production and returned disabled. Production trace ad684003-63ea-43e5-91f1-cd8856d15d79 had admitted=false and attempts=0. Local ASTRA remains at port 8000 in Worker profile with Backend MAS demo mode.

Quota persistence/races/rollover were tested in local workerd. Production migration and quota configuration are verified. Production exhaustion was not exercised while forwarding was disabled.

Previous version d140af7f-75d2-4e0b-a470-1e07741479e8 is the original template fallback. Disable forwarding before any rollback and preserve the Durable Object namespace and quota history. Protected version 234510ff-c691-4b59-b365-3127c94c2cea is now available as a rollback target for future changes.

Keep the ignored local diagnostic .env and protected fresh-checkout worktree. Public MAS inference remains absent pending academic provider compatibility.
