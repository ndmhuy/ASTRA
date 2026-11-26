# Cloudflare AI Gateway setup for ASTRA

For the operator responsible for Agent V2 credentials. ASTRA's server connects to Cloudflare over HTTPS from its existing runtime.

## Configure BYOK

1. Create or select an authenticated gateway in **AI → AI Gateway**. Record the account ID and gateway ID. Preserve separate gateway and provider budgets for interpretation and MAS.
2. In **Provider Keys**, add the team's Google AI Studio API key. Give it an alias such as `astra-agent`, then use the same alias in the ASTRA server configuration.
3. In the gateway settings, enable **Require provider credentials**. Disable gateway-level provider retries or fallback for the initial acceptance and turn off payload logging and caching. Confirm the upstream project is authorized for the intended model and usage.
4. Create an account-scoped token with **AI Gateway Run** access for the trusted ASTRA server. Cloudflare's Run permission applies across the account's gateways. Use an account restricted to the intended workloads if wider access is unacceptable. [Authentication](https://developers.cloudflare.com/ai-gateway/configuration/authentication/) · [BYOK and aliases](https://developers.cloudflare.com/ai-gateway/configuration/bring-your-own-keys/) · [Unified Billing fallback](https://developers.cloudflare.com/ai-gateway/features/unified-billing/)

Put the following in the feature worktree's ignored `.env` or the trusted server's environment. Confirm the Gemini model on the BYOK project before using it. A direct Gemini model query cannot establish that the gateway is ready.

```dotenv
ASTRA_AGENT_ENABLED=true
ASTRA_AGENT_TRANSPORT=gateway
ASTRA_AGENT_GATEWAY_ACCOUNT_ID=<account-id>
ASTRA_AGENT_GATEWAY_ID=<gateway-id>
ASTRA_AGENT_GATEWAY_TOKEN=<restricted-run-token>
ASTRA_AGENT_GATEWAY_BYOK_ALIAS=astra-agent
ASTRA_AGENT_MODEL=<project-approved-gemini-model>
ASTRA_AGENT_PRIMARY_SECONDS=12
ASTRA_AGENT_TOTAL_SECONDS=12
ASTRA_AGENT_DAILY_ATTEMPTS=1
ASTRA_AGENT_FALLBACK_ENABLED=false
ASTRA_AGENT_BUDGET_PATH=runs/agent-gateway-acceptance.sqlite3
```

The request uses `https://gateway.ai.cloudflare.com/v1/<account>/<gateway>/google-ai-studio/v1/models/<model>:generateContent` with native Gemini JSON and schema. It sends `cf-aig-authorization: Bearer <token>`, `cf-aig-byok-alias`, and `cf-aig-no-wholesale: true`. The adapter disables payload logging and cache per request and omits the Google credential header. The unified REST route uses standard Cloudflare `Authorization` and its own payload, routing and alias rules. ASTRA uses the provider-native route. [Google AI Studio route](https://developers.cloudflare.com/ai-gateway/usage/providers/google-ai-studio/) · [Gateway authentication](https://developers.cloudflare.com/ai-gateway/configuration/authentication/) · [Logging](https://developers.cloudflare.com/ai-gateway/observability/logging/)

## Start from the feature worktree

```powershell
$env:EXAM_DEMO_MODE = '1'
$env:EXAM_PROVIDER = 'mock'
$env:EXAM_MODEL = 'mock-fixture-v1'
$env:VITE_AGENT_TRACE = '1'
.\start-astra.bat
```

Use `http://127.0.0.1:8000/`. This keeps MAS in demo mode. Decode errors, quota, timeouts, upstream rejections and credential errors are separate Agent responses. The attempt budget is reserved before inference and persists by UTC day. The initialized test limits above are starting values. Measure live latency before adjusting them. [Acceptance procedure](MANUAL_ACCEPTANCE_V2.md)

## Runtime profiles and rotation

| Profile | Entry point or setting |
| --- | --- |
| Official gateway | `ASTRA_AGENT_TRANSPORT=gateway` with operator credentials |
| Direct Gemini diagnostics | `scripts/start_agent_local.py` or explicit `ASTRA_AGENT_TRANSPORT=direct` and a server-only `ASTRA_AGENT_API_KEY` |
| Private Codex CLI | `scripts/start_agent_codex.py` and an existing local CLI login |
| Offline | `start-astra-demo.bat` or `ASTRA_AGENT_TRANSPORT=offline`. The browser smoke script injects a semantic fixture. |

To launch the private Codex profile from the feature worktree, build the frontend and start the local launcher.

```powershell
npm.cmd --prefix astra-frontend run build
& .venv-win/Scripts/python.exe scripts/start_agent_codex.py
```

Use a fresh process when switching profiles. Keep Codex local and out of production settings. Rotate upstream keys in Provider Keys, rotate the Run token in the trusted server environment, then restart and revoke the old credential after validation. If revoking access immediately, stop the interpreter with `ASTRA_AGENT_ENABLED=false` and revoke the token or provider alias in Cloudflare.

Browser clients call the existing same-origin route. End users need no key. Distributing ASTRA to untrusted machines requires a separate authenticated, narrowly scoped intermediary running on a trusted server. Keep Cloudflare credentials and Codex login material under their respective operators' control.
