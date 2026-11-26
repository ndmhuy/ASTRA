# ASTRA Worker deployment and acceptance

For the operator deploying the credential proxy. The target is the existing `astra-ai-proxy` at `https://astra-ai-proxy.letranhoanglong2227.workers.dev`. React, FastAPI, exams, RAG and LaTeX run locally.

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
