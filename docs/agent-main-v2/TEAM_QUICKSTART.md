# Run ASTRA locally with the team's Workers

For teammates reviewing `feat/longlth2297/chat-mas-main-review` (the existing Agent feature integrated with latest main), and clones containing this change after merge. Run **`.\start.cmd`** from the repository root. The launcher prepares dependencies, builds the frontend and opens **http://localhost:8001** with real Chat and MAS configured. It never submits a Chat request or generates an exam during startup.

Workers/Gateways are already deployed. Teammates need neither a Cloudflare account nor Wrangler, Gemini API key or Gateway Token. At the owner's explicit request, the two shared **Worker caller tokens** are now included in `config/team-worker-access.env`; a fresh clone needs no credential entry. No login or per-user permission system is added for the course submission.

## First use on a machine

Install Git, CPython 3.11 (matching main's compiled MAS planning package) and Node.js 24 with npm, then clone/check out the branch. The launcher creates a virtual environment when needed, installs the Python application with the repository constraints, ensures the Backend's pinned RAG commit is available, runs `npm ci` and builds the UI. Missing corpus objects are fetched without changing the branch or working files. Existing dependencies/builds are reused until their inputs change. Initial setup needs internet access for packages, but makes no inference request. `start.cmd` prefers an existing Windows venv; otherwise it selects Python 3.11 through `py` when available.

```powershell
.\start.cmd
```

The launcher automatically reads Chat and MAS access from the repository profile and starts the existing Backend. It does not copy credentials into the frontend or print their values. An existing personal profile remains preferred; use `--profile config/team-worker-access.env` to explicitly select the repository profile.

## Optional private access override

The previous private profile/import workflow is retained for development and future rotation. To import separate caller access into a personal profile outside Git:

```powershell
.\start.cmd --import-profile C:\private\.env.agent-worker C:\private\.env.mas-worker
```

Import copies only `ASTRA_AGENT_WORKER_CALLER_TOKEN` and `ASTRA_MAS_CALLER_TOKEN`; provider/Gateway keys in a source file are ignored. The original files and private root `.env` are preserved. Private profile import is optional for the bundled course setup.

The personal profile is `%LOCALAPPDATA%\ASTRA\worker.env`, outside the checkout. It survives branch switching and new clones under the same Windows user. On other systems it uses `$XDG_CONFIG_HOME/ASTRA/worker.env` or `~/.config/ASTRA/worker.env`; run `python scripts/run_app.py` instead of `start.cmd`. Without a personal profile, the repository profile is used directly and no local credential file is created.

## Subsequent runs and branch changes

Run `.\start.cmd` again. No token entry or Cloudflare dashboard setup is needed while the included caller tokens remain valid. Changes to dependency inputs or frontend sources trigger installation/build refresh. The branch being run must contain the launcher and repository profile; older branches do not acquire this behavior until the change is merged.

Stop the previous app with Ctrl+C before switching branches. If port 8001 is occupied, the launcher stops with an explanation; it never kills another app or an active exam. Use `--port 8002` to start separately. `localhost` always refers to the teammate's own machine.

```powershell
# Optional: configure a personal override with hidden token input:
.\start.cmd --configure

# Read-only local configuration check, no install/start/API call:
.\start.cmd --check
```

Optional PDF compilation still needs an installed LaTeX compiler, as documented in the [main setup guide](../../README.md#1-install). The launcher does not install an OS-level compiler. Chat and generation use the existing Backend; academic prompts, model, schemas, validation and teacher approval are preserved.

## Credential boundary and shared usage

Gemini API keys and Cloudflare/Gateway credentials stay on Cloudflare. The repository profile contains real plaintext Worker caller tokens. **Anyone who can read this repository or its Git history can call the permitted Worker routes and consume the team's Gemini quota.** Worker authorization remains enabled, but the committed tokens no longer distinguish teammates from other repository readers. This is the owner's explicit exception to the earlier private-only caller setup and the repository's general no-secrets guidance.

Deleting the file in a later commit does not revoke historical copies: rotate/revoke the Worker secrets on Cloudflare, then replace the repository caller values for continued clone-and-run access, or remove the bundled access and restore private setup. Personal overrides must be updated separately with `--configure`. Never commit Gemini API keys, Cloudflare account tokens or Gateway credentials. Existing kill switches, technical limits and actual Gemini quota remain; ASTRA's total/session/token/expiry budgets are currently disabled. No billing is enabled or changed by this launcher.

Only the user initiates live Chat requests or exam generation on the UI. Operator details: [Chat runbook](WORKER_RUNBOOK.md), [MAS runbook](MAS_WORKER_RUNBOOK.md).

## Verification checkpoint

The launcher was observed installing/building and serving the real application on isolated port 8002, with `demoMode=false`, `providerConfigured=true`, caller access configured and the UI responding HTTP 200. Cached preparation skipped installation/build. The repository-profile follow-up is checked without personal/legacy credentials and without prompting. Verification makes only local readiness/static GETs and offline tests; zero model calls and zero exam jobs are submitted.

Focused checks are recorded in [PROGRESS.md](PROGRESS.md). The review branch includes latest main c0fbdaf, with eight conflicting files resolved.46 focused Python checks,50 frontend fixture tests, frontend lint/build, CI Python Ruff/format, generated contracts, dependency checks and wheel build passed. The repository-wide `scripts/verify.py` still stops on91 existing Ruff findings in unchanged `rag_workflow` files. No live model quality or generation acceptance is claimed; a teammate must review and approve before merge.
