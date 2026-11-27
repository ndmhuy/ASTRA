# ASTRA AI credential gateway runbook

For the operator of the existing local ASTRA application. Cloudflare stores provider credentials and receives outbound model requests. React, FastAPI, MAS, RAG, SQLite and PDF compilation run locally.

Use [Worker runbook](WORKER_RUNBOOK.md) for the current keyless release, deployment gate, fresh-checkout procedure and live acceptance. Direct BYOK configuration below remains a private diagnostic option.

## Local startup

In the feature worktree, use Git, a project Python environment and Node 22.12 or newer. The offline checks used Python 3.13.5, which is in repository CI, and Node 24.19.0.

```powershell
python -m venv .venv-win
& .venv-win/Scripts/python.exe -m pip install -e '.[dev]' -c requirements-tested.txt
npm.cmd --prefix astra-frontend ci
.\start-astra-demo.bat
```

Open `http://127.0.0.1:8000`. The demo launcher forces mock MAS and disables model-assisted chat. Its content is fixture data. Exact local chat controls still work. PDF compilation requires a supported compiler. The Vite development server forwards `/api` and `/agent` to `ASTRA_API_PROXY_TARGET`, with loopback port 8000 as the default.

## Chat with AI while keeping MAS in demo mode

Set the Agent options below in the feature worktree's ignored `.env`. Use the regular launcher with MAS demo mode enabled.

```powershell
$env:EXAM_DEMO_MODE = '1'
$env:EXAM_PROVIDER = 'mock'
$env:EXAM_MODEL = 'mock-fixture-v1'
.\start-astra.bat
```

`start-astra-demo.bat` is always offline. The Worker profile uses public configuration and centralized admission. The private direct gateway profile requires its own positive attempt budget, approved Gemini model and gateway token. The chat distinguishes an off switch, invalid configuration and quota exhaustion. Restart the server after configuration changes.

## Operator configuration

Use the [current Cloudflare setup](CLOUDFLARE_GATEWAY_SETUP.md) for profile selection, exact environment settings and the bounded acceptance procedure.

1. In the Cloudflare dashboard, create or select an authenticated AI Gateway. Store the approved Google AI Studio key for Agent and, if using MAS BYOK, the approved OpenAI key under their intended aliases. Create Run tokens for the trusted ASTRA process. The Run permission is account-scoped. Confirm entitlement and actual provider model and quota before enabling either client. [Cloudflare authentication](https://developers.cloudflare.com/ai-gateway/configuration/authentication/) · [Cloudflare BYOK](https://developers.cloudflare.com/ai-gateway/configuration/bring-your-own-keys/)
2. Enable Require provider credentials in the gateway settings (`byok_only`). Configure provider-side quota and budget, disable gateway retries and automatic rerouting, and review logging and retention. ASTRA sets `cf-aig-no-wholesale: true`, `cf-aig-skip-cache: true` and disables gateway log collection and payload capture per request. BYOK can still incur provider charges. [BYOK-only setting](https://developers.cloudflare.com/changelog/post/2026-09-14-require-provider-credentials/) · [Cloudflare logging](https://developers.cloudflare.com/ai-gateway/observability/logging/)
3. Set values privately in the feature server's ignored `.env` or injected environment. The assistant and browser never need the provider keys. Agent uses native Google `generateContent` and structured JSON with the authenticated gateway header. MAS uses native OpenAI Chat Completions with the existing request format and no model substitution. [Google AI Studio endpoint](https://developers.cloudflare.com/ai-gateway/usage/providers/google-ai-studio/) · [OpenAI endpoint](https://developers.cloudflare.com/ai-gateway/usage/providers/openai/)
4. Restart with `start-astra.bat` for an authorized local run. Test the exact local path first. After separate approval for one Agent call, set the Agent daily attempt budget to 1, keep fallback disabled and send one paraphrase outside the curated local routes. Confirm the expected receipt and use the provider dashboard to verify request accounting. MAS generation and verification have separate usage and require their own approval.

| Agent settings | Purpose |
| --- | --- |
| `ASTRA_AGENT_ENABLED` | Enables gateway-backed interpretation. Default false. |
| `ASTRA_AGENT_DAILY_ATTEMPTS` | Default zero. Limits attempted calls, including fallback and timeouts, using the UTC day. |
| `ASTRA_AGENT_MODEL` | Operator-approved structured-output Gemini model; fixed on server. |
| `ASTRA_AGENT_GATEWAY_ACCOUNT_ID`, `ASTRA_AGENT_GATEWAY_ID`, `ASTRA_AGENT_GATEWAY_TOKEN`, `ASTRA_AGENT_GATEWAY_BYOK_ALIAS` | Cloudflare identifiers, Run token and stored BYOK alias. |
| `ASTRA_AGENT_FALLBACK_ENABLED`, `ASTRA_AGENT_FALLBACK_MODEL` | Optional separately approved model. Default false. Applies only to transient faults within the deadline. |
| `ASTRA_AGENT_PRIMARY_SECONDS`, `ASTRA_AGENT_TOTAL_SECONDS`, `ASTRA_AGENT_MAX_OUTPUT_TOKENS`, `ASTRA_AGENT_BUDGET_PATH` | Deadline, output bound and persistent attempt ledger. |

For MAS, set `EXAM_PROVIDER=chat_completions`, `EXAM_USE_AI_GATEWAY=true`, `EXAM_GATEWAY_ACCOUNT_ID`, `EXAM_GATEWAY_ID`, `EXAM_GATEWAY_TOKEN` and optionally `EXAM_GATEWAY_BYOK_ALIAS`. Preserve `EXAM_MODEL` and its existing output configuration. Configure `EXAM_SPEND_LIMIT_USD` with both positive token price fields. The application estimate is separate from the provider's billing limits. Gateway mode uses the stored OpenAI provider key and accepts no provider key header from ASTRA. A direct provider remains an explicit configuration option.

## Rotation and rollback

Rotate the provider key under its stored alias. Rotate the server Run token by updating it in the ignored environment, restarting ASTRA and revoking the old token once the new token is verified. Stop Agent inference by setting `ASTRA_AGENT_ENABLED=false`. To stop MAS inference without selecting a different approved provider, use the demo launcher. Keep the SQLite files if restarting or rolling back. Production tenant authorization and atomic job admission across devices remain backend work. Run ASTRA on loopback.

Wire requests were validated offline with HTTP fixtures. Account entitlement, deployed gateway settings and live provider response remain unverified.
