# ASTRA Worker deployment and acceptance

For the operator deploying the credential proxy. The target is the existing `astra-ai-proxy` at `https://astra-ai-proxy.letranhoanglong2227.workers.dev`. React, FastAPI, exams, RAG and LaTeX run locally.

## Current candidate: owner Gate A review, 2026-11-27

The current implementation candidate is `6951266` on `feat/longlth2297/agent-main-v2`. It includes the core `fe648eb`, readiness checkpoint `310401d`, preserved-ceiling configuration `98c387e`, observed-question reference checkpoint `a900e79`, the final intake-bound/diagnostic correction a318b74, and stored-answer information/routing 6951266. Read [Semantic workflows](SEMANTIC_WORKFLOWS.md) and [the current master specification](UNIFIED_SEMANTIC_WORKFLOW_SPEC.md). This section supersedes earlier single-contract/single-pool assumptions; historical evidence below remains intact.

- Target: the existing Worker and `astra-gateway`; no website, Backend, database hosting or new resources.
- Current production deployment: `bb165c28-5a06-4372-9c9e-b2bf758b9599`, created 2026-11-26 14:53:40 UTC. Read-only deployment/version metadata confirmed Agent/global daily ceilings 2, MAS ceiling 0, model `gemini-3.1-flash-lite`, forwarding false, ADMISSION present and the Gateway token still a Secret binding. Secret values were not read or printed.
- Current public health: legacy `astra-intent-v1`, forwarding false, remaining attempts 0 and active reservations 0. No inference was performed during this implementation.
- Proposed change: add `/v2/agent/interpret`, canonical semantic parsing, safe field diagnostics, duplicate-turn protection, separate workload accounting/circuits and Chat reservations. Preserve `/v1/agent/interpret`, its hash and existing Secret bindings. New health metadata lists both contracts and the semantic hash; `masForwarding` remains false.
- Configuration review: `wrangler.jsonc` retains `keep_vars: true` and now matches the observed production ceilings of 2 with forwarding=false. This local configuration alignment neither resets storage nor adds an allowance to the running Worker. New concurrency/token/rate settings default to bounded Chat policy and disabled MAS; normal public budgets require separate operator approval.
- Storage: keep ADMISSION, `global-v1` and `v1-admission`. No Durable Object namespace/class migration is needed. New ledger fields are additive. Old leases/rates are interpreted as Agent workload entries, and historical attempt counts remain. Historical token usage is unknown; new token reservations do not reconstruct it.
- Secrets: preserve the encrypted token and existing account/gateway/BYOK variables. No client credential, new paid resource or billing activation is part of the proposal. MAS remains a closed integration boundary and has no public forwarding endpoint.
- Rollback: first disable forwarding. Restore the known production version with the existing documented Wrangler rollback command targeting `bb165c28-5a06-4372-9c9e-b2bf758b9599`. Preserve all durable storage and the consumed ceilings/counters; do not delete/recreate ADMISSION. Recheck health and quota without invoking inference. Old code can ignore the additive ledger fields; no MAS requests have been released.

The local Worker dry run, TypeScript checks and 20 workerd groups pass; the final readiness-header check also passes independently. All 34 React adapters have mounted fixture evidence across the two browser scripts. These checks do not authorize deployment or prove real provider understanding.

No paid Cloudflare feature was added. SQLite Durable Objects are supported on the Free plan, and current Workers limits permit the lightweight resource model. Free-plan request CPU and actual account limits still need runtime observation after an authorized deployment; local wall times are not billed CPU measurements. No plan or billing settings were changed. [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), [Durable Object availability and limits](https://developers.cloudflare.com/durable-objects/platform/pricing/)

### Separate inference and MAS gates

After explicit deployment approval, deploy disabled first and verify the public readiness contract/hash and persisted quota. A deployment approval is not an inference allowance. Gate B requires an explicitly bounded new persisted allowance, no automatic retries/fallback, one natural THPT message reaching the real model, accepted canonical meaning, missing-subject clarification and zero generation requests. Preserve the two consumed attempts. Record actual HTTP status, finish reason, field diagnostics, usage, upstream attempt count and visible timing. Disable forwarding after the approved run.

Gate C requires its own multi-turn budget for natural paraphrases, subject follow-up, unsupported subject, family correction, memory and navigation. Gate D separately requires an independent academic credential/provider, approved caller authorization/resource policy and explicit real-generation permission. No anonymous expensive MAS route is available in this candidate.

### Explicit local Worker profile

Build `astra-frontend`, then run `python scripts/start_agent_worker.py --port 8000` from the feature checkout. This explicitly chooses keyless Worker interpretation, disables fallback and keeps MAS in demo mode. Startup sends no inference request. Until the v2 Worker rollout and live gates are approved, model-assisted Chat remains unavailable; local UI controls and deterministic chat remain usable. Private Gateway and Codex diagnostic launchers remain explicit alternatives.

## Deployment gate

The package is `workers/astra-ai-proxy`. Deployment adds one SQLite-backed Durable Object class `Admission`, binding `ADMISSION`, and migration `v1-admission`. The stable object name is `global-v1`. Preserve this identity and its storage through redeployments. The configuration uses `keep_vars=true` and contains none of the four existing dashboard credential settings. Encrypted secrets remain on the Worker. Preview URLs are disabled. The shipped configuration disables forwarding and permits only one global Agent attempt per UTC day when enabled.

SQLite Durable Objects support Workers Free. Free limits include 100,000 requests/day and 13,000 GB-s/day, and exceeding limits fails operations. Deployment may allocate the named Durable Object namespace within that plan. Confirm the operator account and existing Worker before deployment. [Cloudflare pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/)

The owner selected gemini-3.1-flash-lite. It is configured centrally and remains subject to the actual Google project's model availability. Production version 234510ff-c691-4b59-b365-3127c94c2cea was deployed on 2026-11-26 with forwarding disabled. All four original dashboard bindings were preserved. ADMISSION and SQLite migration v1-admission were confirmed through production version metadata. Public health and a disabled local-to-Worker request passed with zero upstream attempts. The preceding template version is d140af7f-75d2-4e0b-a470-1e07741479e8.

For the current checkpoint, deployment is complete. The following commands remain the reference procedure for future approved deployments. Live enablement and inference still require separate authorization.

## Commands

From the feature worktree, regenerate/check the authoritative resources.

```powershell
& .venv-win/Scripts/python.exe scripts/export_worker_contract.py --check
Set-Location workers/astra-ai-proxy
npm.cmd ci
npm.cmd run check
npm.cmd test
npm.cmd run dryrun
```

The test command bundles the production entry and a separate local-only storage harness. Tests use local workerd with synthetic upstream responses and no remote inference. The harness is excluded from the production entry. Wrangler 4.168.0 uses the pinned matching Miniflare 5 beta runtime. The lockfile records all dependencies.

Use Wrangler's browser login when operator authentication is required.

```powershell
npx.cmd wrangler login
npx.cmd wrangler whoami
npx.cmd wrangler secret list --name astra-ai-proxy
npx.cmd wrangler deployments list --name astra-ai-proxy
```

Secret list returns names and types. Retain the prior deployment ID privately for rollback. Confirm the existing four dashboard settings and add the approved model in **Settings → Variables and Secrets**. Do not use placeholder values for existing settings.

After explicit deployment authorization, run from this package directory.

```powershell
npx.cmd wrangler deploy
Invoke-RestMethod https://astra-ai-proxy.letranhoanglong2227.workers.dev/health
```

The health result should identify `astra-intent-v1` and `forwarding=false`. It performs zero inference. Check that the existing Secret name is still present and the `ADMISSION` binding is SQLite-backed. Confirm Require provider credentials on the existing AI Gateway. The native endpoint uses `cf-aig-authorization`, BYOK alias, `cf-aig-no-wholesale=true` and `cf-aig-max-attempts=1`. [Native endpoint](https://developers.cloudflare.com/ai-gateway/usage/providers/google-ai-studio/) · [Headers](https://developers.cloudflare.com/ai-gateway/glossary/) · [Wrangler configuration](https://developers.cloudflare.com/workers/wrangler/configuration/)

## Enable and observe one authorized attempt

Forwarding enablement and live inference require owner authorization. Set `ASTRA_FORWARDING_ENABLED=true` in the production dashboard once model and quota settings are confirmed. Configured diagnostic limits are global=1, Agent=1, MAS=0, concurrency=1, IP=3/minute and global burst=10/minute. They are independent of provider token quotas. Increase them only after measuring the approved project's limits. The single allowance is shared across installations. An anonymous caller could consume it before the intended tester.

Start local ASTRA using `start-astra-worker.bat`. It forces the public Worker profile and demo MAS, preserving any existing diagnostic file. No local token or Codex login is used by that profile. The standard launcher remains available and the offline launcher disables chat inference. The default activation stays gated pending remote acceptance.

Open the browser Network panel in a fresh conversation. Once authorized, send exactly once.

> Cô muốn tạo một đề thi thử tốt nghiệp.

Source inspection shows this sentence falls outside the anchored zero-inference recipes. Confirm a real Worker request and upstream attempt before recording live success. Capture turn ID, Worker request ID, admitted flag, attempts, provider/model, upstream HTTP status, Worker elapsed time, full local chat elapsed time, semantic intake and visible clarification. Worker logs omit prompts, raw provider errors and credentials. The Python boundary reports validated intent IDs and elapsed time. Browser receipt traces require a build with `VITE_AGENT_TRACE=1`.

Expect THPT intake and a subject question. Observe zero exam-generation HTTP requests. Stop after failure and diagnose the returned category and upstream status without retrying. After success, manually test “Môn Toán.”, a change to Chemistry, V-ACT, recall, title preservation and confirmation gates under a separately approved expanded budget.

## Quota and security boundaries

A single persistent object atomically commits UTC daily attempts, fixed-minute IP/global rate counters and expiring concurrency leases. Requests reserve before upstream fetch. Attempts remain charged after timeout, malformed output or disconnect. Leases expire after 45 seconds and the upstream deadline is at most 30 seconds. Database transactions contain no upstream network requests. Storage or configuration failures block forwarding. Daily Agent and MAS counters are distinct; MAS admission is rejected and its route is absent until compatibility is established.

The public Worker validates the generated Turn contract, a 32 KiB actual body bound and the bounded context lists before admission. System instructions, schema, model, URL and credential headers are server-controlled. Responses are limited to 64 KiB and validated against both generated output and Decision schemas. This release enforces attempt/input/output limits. These limits do not guarantee a monetary provider billing ceiling.

The endpoint is anonymous. IP throttling uses Cloudflare connection metadata and is best-effort. Anyone discovering the URL can consume the bounded allowance. CORS and claimed workspace IDs provide no user identity.

## Disable and roll back

Set `ASTRA_FORWARDING_ENABLED=false` in the dashboard and verify health shows false. This blocks new requests. Already admitted upstream work remains counted and may complete.

For code rollback after authorization, use the prior verified protected deployment.

```powershell
npx.cmd wrangler rollback <previous-deployment-id>
```

Keep forwarding disabled during rollback. Retain `ADMISSION`, `global-v1`, and the migration history. A rollback to the original Hello World can restore availability of that template but cannot provide ASTRA interpretation. Never delete quota storage to reset usage.

## Fresh checkout

Ordinary runtime dependencies are Git, Python 3.13 as exercised, Node 22.12+ and package dependencies. RAG uses the pinned corpus release and PDF preview requires a detected supported LaTeX compiler. Neither is installed by the Worker package.

```powershell
python -m venv .venv-win
& .venv-win/Scripts/python.exe -m pip install -e . -c requirements-tested.txt
npm.cmd --prefix astra-frontend ci
.\start-astra-worker.bat
```

Open `http://127.0.0.1:8000/`. No private environment file is copied. Verify health, catalog and UI before any chat submission. A clean detached checkout with independent Python dependency installation, npm ci/build, and real HTTP UI/health/catalog was tested. Remote AI availability and full academic generation remain separate gates.

## Live checkpoint on 2026-11-26

One real UI turn reached the gateway with upstream HTTP 200 but failed schema validation. Production currently runs b0932058-bdf3-46ed-8ac0-e7977207bfec with forwarding disabled and the diagnostic allowance consumed. Health now reads the persistent ledger without reserving an attempt and reports UTC day, remainingAttempts and activeReservations. See NEXT_TASK.md before enabling another turn. Schema diagnostics report validation stage and safe metadata, while the first turn's exact invalid field was not recorded.

## Structured-output investigation and additional authorized turn

The additional authorized UI turn returned HTTP 200, one candidate, STOP, application/json, valid JSON, one final text part and 70 generated tokens. Both structural schemas passed. The application then rejected a semantic invariant. This establishes a provider/application cross-field contract mismatch. It supplies no evidence of timeout, overload or truncation. The first historical response remains unavailable.

The provider schema had accepted field combinations that the internal validator prohibited. The correction generates four exclusive alternatives for actions, intake, guidance and plain non-action decisions. Actions require a nonempty action list. Other alternatives allow an omitted or empty list. Intake and guidance cannot coexist, and their kinds are answer or clarify. Optional null fields normalize to omission before strict validation. Required fields, action IDs and per-action argument restrictions continue through the full internal schema. The provider-facing common argument object reduces repeated union branches. Final serialized schemas are 3,832 provider bytes and 11,014 internal bytes. Generation and normalization share the Python contract exporter and the deployed/client fingerprint.

The exact triggering combination among the former combined invariant checks was not recorded. The instrumentation now reports specific invariant names and safe decision shape flags. The correction enforces every member of that observed failing invariant class in the provider grammar. It has passed offline tests and awaits a fresh live verification.

### Parsing and diagnostic stages

- HTTP transport distinguishes quota, authentication, model, upstream transient errors and timeout. Error logs contain numeric code and bounded status identifiers.
- Envelope JSON parsing records success, MIME category and actual byte length.
- Candidate selection records count, prompt block reason and finish reason. Missing candidates and blocked prompts are rejected.
- Completion requires STOP. MAX_TOKENS and other incomplete results remain failures.
- Extraction joins final text parts and skips thought parts and signature-only metadata. Empty final text is rejected.
- Semantic JSON parsing accepts complete JSON. It supplies no fence removal, guessing or JSON repair.
- Provider schema validation identifies invalid values and unsupported fields by keyword and path.
- Application schema and invariant checks enforce each existing action's arguments and the exclusive semantic alternatives.
- The local Python Worker adapter validates the synchronized version and Decision. React then resolves intake against the real catalog and compiles eligible actions through existing guards.

Logs include safe token counts, final-text byte length, parsing stage, schema paths and provider elapsed time. Raw teacher text, unrestricted provider responses and credential values are excluded.

### Gemini parameter audit

The existing provider-native route uses v1 generateContent, responseMimeType application/json and responseJsonSchema. Google distinguishes responseJsonSchema from its OpenAPI-style responseSchema. The generated schema uses documented object, array, scalar, null, enum, anyOf, properties, required and additionalProperties constraints. Bounds remain enforced by the internal validator even where a provider supports only a subset. [Google structured outputs](https://aistudio.google.com/docs/structured-output) · [GenerateContent reference](https://aistudio.google.com/api-reference/generate-content)

Gemini 3.1 Flash-Lite documents MINIMAL as its lowest thinking level and its default. The public v1 discovery document confirms thinkingConfig.thinkingLevel=MINIMAL. The Worker sets it explicitly for this profile. The 1,024-token output limit remains unchanged. The observed completed 70-token response gives no basis for increasing it for this incident. Missing thought usage is reported as absent, not zero. [Thinking configuration](https://aistudio.google.com/docs/thinking) · [Model documentation](https://aistudio.google.com/docs/models/gemini-3.1-flash-lite) · [v1 discovery](https://generativelanguage.googleapis.com/$discovery/rest?version=v1)

### Future fallback evaluation

The Python InterpretationProvider protocol already returns the shared Decision. ProviderRouter permits bounded fallback only for transient or timeout failures and calls its reserve function before every attempt. The current Worker profile has one remote route and no fallback.

Small OpenAI API models with Structured Outputs and Anthropic's Haiku family with JSON structured output are candidates for a later latency benchmark. Both need an approved provider key, confirmed account/model access and a native adapter. Their actual ASTRA latency and accuracy have not been measured. [OpenAI structured output](https://developers.openai.com/api/docs/guides/structured-outputs) · [Anthropic structured output](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

A future Worker router must reserve the persistent global and operation allowance before each upstream attempt, including fallback. Retry eligibility must distinguish temporary overload and timeout from quota, authentication, schema and application-contract failures. The latter failures stop the turn. Any broadened quota/provider routing needs explicit approval. One accepted semantic result reaches the existing freshness checks and UI executor, retaining duplicate-action suppression. No fallback service or credential was added during this investigation.
