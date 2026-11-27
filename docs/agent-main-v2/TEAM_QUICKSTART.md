# Run this branch on a teammate's machine

For trusted ASTRA developers checking out feat/longlth2297/agent-main-v2. Cloudflare Workers/Gateways are already deployed. Teammates do **not** need Wrangler, a Cloudflare account, a Gemini API key or a Gateway Token to run the local application. They do need the revocable internal caller credentials supplied privately by the owner; these are deliberately absent from Git.

## One-time local setup

1. Check out the feature branch and use Python3.13 and Node24, matching the observed development runtime. Install Python app dependencies with `python -m pip install -e ".[dev]"` in a virtual environment. Root requirements.txt covers the older standard-library RAG tool, not the full FastAPI application.
2. Build the frontend: in astra-frontend run `npm ci`, then `npm run build`. Built dist and dependencies are ignored and do not arrive with Git.
3. Receive `.env.agent-worker` privately from the owner and place it in the repository root. It contains only ASTRA_AGENT_WORKER_CALLER_TOKEN, the Backend's restricted Worker access credential. Never commit/paste its value into chat or frontend config. Without it, budgetless remote Chat is rejected even though the UI opens.
4. For real MAS too, receive the ignored `.env.mas-worker` profile privately. It contains the separate MAS caller credential and non-secret academic model/transport settings. This is not a Gemini/Gateway credential. The local profile used by this branch selects gemini-3.1-flash-lite and real MAS.

No deployment or Cloudflare dashboard change is needed per teammate. Local credentials remain required whenever a teammate runs their own Backend. Caller rotation/revocation affects machines holding that credential; the owner supplies the replacement through a secure channel.

## Start locally

Activate the virtual environment first. From the repository root:

```powershell
# Real Chat, MAS demo:
python scripts/start_agent_worker.py --port 8000

# Real Chat and real MAS, requires both ignored profiles:
python scripts/start_mas_worker.py --port 8001
```

Choose one command for the desired profile. Open http://localhost:8000 or http://localhost:8001 respectively. These commands start the server without making an inference request. Default generic startup can load an old .env or leave Chat disabled; use the explicit launchers above.

`localhost` refers to the machine opening the address. A teammate's browser cannot reach the owner's localhost by opening that URL on their own machine. A future shared deployment would let browsers use its Backend without holding caller credentials; no shared website/Backend hosting is deployed by this work.

The same existing Workers serve the team. Actual provider quota and technical rates/concurrency are shared; Chat currently allows3/IP/minute,10 globally/minute and one active inference. ASTRA total/session/token/expiry budgets are disabled in the current authenticated development profile. Gemini quota or technical throttling can still reject requests. Academic validation and teacher approval remain active.

Only the owner/user initiates live model calls or exam generation. There is no startup/live smoke-generation requirement. See WORKER_RUNBOOK.md and MAS_WORKER_RUNBOOK.md for current deployment state and kill switches.

## Push verification checkpoint

Implementation and focused checks are recorded in PROGRESS.md. Before this branch backup, scripts/verify.py was run: compilation completed, then Ruff stopped on91 pre-existing findings in unchanged rag_workflow files. The full repository gate is therefore not green; do not describe this push as merge-ready. Current upstream main has not been merged/rebased into the feature branch.
