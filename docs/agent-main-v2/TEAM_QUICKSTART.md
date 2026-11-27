# Run ASTRA locally with the team's Workers

For teammates reviewing `feat/longlth2297/agent-main-v2`, and clones containing this change after merge. Run **`.\start.cmd`** from the repository root. The launcher prepares dependencies, builds the frontend and opens **http://localhost:8001** with real Chat and MAS configured. It never submits a Chat request or generates an exam during startup.

Workers/Gateways are already deployed. Teammates need neither a Cloudflare account nor Wrangler, Gemini API key or Gateway Token. First use on a new machine requires the two revocable **Worker caller tokens**, supplied privately by the owner. No login or per-user permission system is added for the course submission.

## First use on a machine

Install Git, Python (observed runtime: Python 3.13) and Node.js 24 with npm, then clone/check out the branch. The launcher creates a virtual environment when needed, installs the Python application with the repository constraints, ensures the Backend's pinned RAG commit is available, runs `npm ci` and builds the UI. Missing corpus objects are fetched without changing the branch or working files. Existing dependencies/builds are reused until their inputs change. Initial setup needs internet access for packages, but makes no inference request.

```powershell
.\start.cmd
```

If access is missing, the terminal asks for these two values with hidden input:

- `ASTRA_AGENT_WORKER_CALLER_TOKEN`: Chat Worker access.
- `ASTRA_MAS_CALLER_TOKEN`: MAS Worker access.

These are **not** Gemini keys or Cloudflare account/API/Gateway tokens. The owner provides them privately once. Do not paste them into a PR, commit, screenshot or frontend configuration.

Alternatively import privately supplied legacy files once:

```powershell
.\start.cmd --import-profile C:\private\.env.agent-worker C:\private\.env.mas-worker
```

Import copies only the two caller fields; provider/Gateway keys in a source file are ignored. Existing ignored legacy profiles in the checkout are automatically imported on first use. The original files and private root `.env` are preserved.

The new shared local profile is `%LOCALAPPDATA%\ASTRA\worker.env`, outside the checkout. It survives branch switching and new clones under the same Windows user. On other systems it uses `$XDG_CONFIG_HOME/ASTRA/worker.env` or `~/.config/ASTRA/worker.env`; run `python scripts/run_app.py` instead of `start.cmd`.

## Subsequent runs and branch changes

Run `.\start.cmd` again. No repeated token entry or Cloudflare dashboard setup is needed while those caller tokens remain valid. Changes to dependency inputs or frontend sources trigger installation/build refresh. The branch being run must contain the launcher; older branches do not acquire this behavior until the change is merged.

Stop the previous app with Ctrl+C before switching branches. If port 8001 is occupied, the launcher stops with an explanation; it never kills another app or an active exam. Use `--port 8002` to start separately. `localhost` always refers to the teammate's own machine.

```powershell
# Update caller access after the owner rotates it:
.\start.cmd --configure

# Read-only local configuration check, no install/start/API call:
.\start.cmd --check
```

Optional PDF compilation still needs an installed LaTeX compiler, as documented in the [main setup guide](../../README.md#run-the-web-app). The launcher does not install an OS-level compiler. Chat and generation use the existing Backend; academic prompts, model, schemas, validation and teacher approval are preserved.

## Credential boundary and shared usage

Gemini API keys and Gateway credentials stay on Cloudflare. The caller profile is a local plaintext credential file, **not encrypted storage**. Keeping it outside Git prevents accidental branch commits; it does not hide the token from someone controlling the machine. A holder can call the permitted Worker routes and consume shared quota. The owner can revoke/rotate the Worker caller secrets; local profiles must then be updated with `--configure`.

Do not commit the shared tokens or bundle them into the UI to remove the first-use step. Private Worker authorization and kill switches remain enabled. The existing Workers serve the team with shared Gemini quota and technical limits; ASTRA's total/session/token/expiry budgets are currently disabled in authenticated development mode. Technical throttling and actual Gemini quota can still reject calls. No billing is enabled by this launcher.

Only the user initiates live Chat requests or exam generation on the UI. Operator details: [Chat runbook](WORKER_RUNBOOK.md), [MAS runbook](MAS_WORKER_RUNBOOK.md).

## Verification checkpoint

The launcher was observed installing/building and serving the real application on isolated port 8002, with `demoMode=false`, `providerConfigured=true`, private Chat access configured and the UI responding HTTP 200. The next preparation reused its caches. Verification made only local readiness/static GETs and offline tests; zero model calls and zero exam jobs were submitted.

Focused checks are recorded in [PROGRESS.md](PROGRESS.md). The repository-wide `scripts/verify.py` still stops on 91 existing Ruff findings in unchanged `rag_workflow` files. Upstream `main` has not been integrated; this checkpoint does not establish a green merge gate.
