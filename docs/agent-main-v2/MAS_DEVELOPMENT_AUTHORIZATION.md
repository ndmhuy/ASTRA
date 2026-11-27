# Owner-approved MAS development use — 2026-11-27

For maintainers of the existing MAS Worker and Backend. This records the owner's latest explicit instruction and supersedes the original one-exam/41-request/two-hour proposal in MAS_CLOUDFLARE_SPEC.md and the older runbook.

Subsequent owner follow-up explicitly extends budget bypass to Chat too. The earlier MAS-only instruction to leave Chat configuration untouched is superseded for that Chat task. See WORKER_RUNBOOK.md; MAS remains independently configured. The prohibition on agent-initiated Gemini calls/generation remains active.

- Enable real MAS forwarding using the revocable internal caller credential and the existing independent Gemini BYOK/Gateway. Run the non-demo application at localhost:8001 for owner-driven testing of multiple exams.
- Temporarily disable ASTRA total/daily request budgets, conservative estimated-token budgets and the two-hour expiry. Keep their implementation configurable so it can be re-enabled. Do not ask for budget approval before each exam in this development mode.
- Preserve the actual Gemini quotas, technical request/output limits, Backend retry/timeout/concurrency, academic validation, model, prompts, schemas and business logic. Preserve caller authentication, credential security, duplicate-job protection and kill switch. Do not expose unrestricted anonymous inference.
- Do not activate billing, buy resources, create more Workers/Gateways or change the existing Chat API/configuration.
- **The agent must not call Gemini to test, generate any exam, or run smoke/health/integration checks that cause real inference. Every real generation request must be initiated by the owner through the UI.** Offline checks and non-consuming connectivity checks are permitted.

Implementation: ASTRA_MAS_BUDGETS_ENABLED=false bypasses only the ASTRA budget checks; authentication, forwarding kill switch and technical admission remain active. The switch defaults to true so bounded behavior remains available. Persistent usage is retained through either mode and restarts. Production deployment/readiness and the exact operator config are recorded in MAS_WORKER_RUNBOOK.md and NEXT_TASK.md.
