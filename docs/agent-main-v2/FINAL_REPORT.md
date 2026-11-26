# ASTRA Agent V2 final handoff

For ASTRA reviewers and the operator. The local Agent is integrated into the current React workspace and native FastAPI app. The branch is `feat/longlth2297/agent-main-v2`. Its parent baseline is `7523c79556a9935df5008c92043f1e38d6e5d2a2`, confirmed again by the P8 fetch. The reference Agent was `fb834b976cb62eb7292fa839cdaf1d8738e1ec50`. Implementation tip before the report: `fbc951bade177dcea0d6e19079d17238dcd5b495`. The engineering pack is available within the worktree at `tmp/agent-main-v2/spec/`.

## What changed

- Vietnamese chat uses exact local routes and a versioned same-origin interpretation service for other requests. React validates and compiles semantic intents, controls the mounted UI, checks revision and confirmation bindings, and reports observed effects.
- THPT and V-ACT intake use the actual preset catalog and evaluate path. Only validated academic requirements enter Agent-managed generation. The existing start handler stays with React. Chat remains open during generation. Job-bound notes are reconciled to stable question identities on completion.
- The session store retains chats, titles and bounded context for recall. The editor still handles question writes. Agent-prefilled drafts require teacher review and save. Opening PDF via chat does not unlock approval.
- Native authenticated BYOK adapters are prepared for Agent Gemini and optional MAS OpenAI transport. The Agent defaults to disabled with zero inference attempts. Existing MAS academic behavior stays on its established runtime and its own model configuration.

## Evidence

- Full Python suite, 408 passed with 7 subtests. After the final Python admission changes, the 16 focused Agent route/provider/gateway checks passed. Ruff check and format passed. Local HTTP smoke passed with the mock provider. The built UI, health and disabled Agent decision were also served over loopback by the native web factory.
- Frontend, 23 tests passed with lint and production build. Vite retains its bundle-size warning.
- Mounted browser smoke used the current catalog/evaluate endpoints for THPT and V-ACT, a semantic intent fixture, and intercepted exam HTTP. It exercised one confirmed THPT start, the original manual V-ACT start, job progress, deferred notes, stable question focus, teacher PDF review gate, approval, JSON download, revision-changing editor save, stale export rejection and persisted title/recall. The fixture uses a dummy PDF response.
- The local routing benchmark matched 16 curated inputs across 800 timings, p50 0.006 ms and p95 0.022 ms. It measures input processing and routing only. Model-assisted latency and semantic accuracy remain unmeasured.
- Dependency compatibility and wheel build passed. The shared catalog is packaged in the wheel. Repository and browser asset credential checks were run before handoff.

## Release verdict

| Gate | Result |
| --- | --- |
| LOCAL_APP_READY | VERIFIED_OFFLINE |
| ORCHESTRATION_OFFLINE_VERIFIED | PARTIAL, 18 of 34 registered intent IDs observed in mounted browser |
| LIVE_AGENT_VERIFIED | BLOCKED_EXTERNAL, operator configuration and inference authorization |
| LIVE_GENERATION_VERIFIED | BLOCKED_EXTERNAL, separate authorization |
| KEY_GATEWAY_READY | VERIFIED_OFFLINE, wire fixtures for both native providers |
| KEY_GATEWAY_LIVE_VERIFIED | BLOCKED_EXTERNAL, account provisioning and authorized live check |

The native app lacks authenticated tenant ownership and cross-device atomic workspace admission. Browser locks guard same-origin local generation. V-ACT per-question regeneration, custom/random generation, browser file upload and web search, Word export and job cancellation have no current integrated contract. General negated/conditional instructions seek clarification. Pending confirmations are runtime-only and require preparation again after reload. The acceptance report lists the remaining fixture gaps and historical cases.

## Start and exercise locally

Run `start-astra-demo.bat` from the feature worktree after installing dependencies. Visit `http://127.0.0.1:8000`. For a controlled local smoke, greet the Agent, select V-ACT, inspect the fixed 120-question and 150-minute setup, and close the dialog. Then open the manual template controls and verify the same catalog. Run `scripts/agent_browser_smoke.py` with Playwright and a local Chromium/Edge install to exercise the full fixture path.

No branch changes were pushed. Cloudflare account setup and live inference were left for operator authorization. [Gateway runbook](DEPLOY_RUNBOOK.md) · [Capability matrix](CAPABILITY_MATRIX.md) · [Acceptance results](ACCEPTANCE_RESULTS.md) · [Progress](PROGRESS.md)
