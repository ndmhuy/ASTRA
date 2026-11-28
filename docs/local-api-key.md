# Local shared API connection

For teammates reviewing the local key onboarding change. This is pending manual
provider testing and PR review, not a recorded team-wide architecture decision.

`start.cmd` now prepares the app and starts `scripts/start_local.py` on loopback.
It does not read `worker.env`, `config/team-worker-access.env`, Worker caller tokens
or Cloudflare routing flags. The previous Worker scripts and remote resources are
preserved for rollback. Existing V3 semantic behavior is included in this branch.

## Configuration path

The initial dialog masks the key, provides an explicit reveal button, and offers
URL/model settings. The defaults match the supplied compatible API configuration:

```dotenv
EXAM_PROVIDER=chat_completions
EXAM_MODEL=nghi/claude-haiku-4.5
ASTRA_GEMINI_API_KEY=
EXAM_BASE_URL=https://api.nghimo.com/v1
```

The variable name is historical; the credential belongs to the selected provider.
Saving requires a key on first setup; later, a blank key retains the current one.
The API validates configuration locally and atomically replaces only these four
fields, preserving other `.env` settings/comments. Saving, reload and startup make
no inference request. A saved key is not reported as authenticated until a real
user action receives a usable provider completion.

The shared runtime injects the same credential, model and URL into Chat, baseline
and Composer/Illustrator/Solver/Reviewer. It reuses the existing compatible HTTP
adapter and Claude forced-tool encoding, with the original academic schemas.
Chat retains V3 canonical meaning and uses its bounded semantic output/timeout;
the exam pipeline retains its existing generation limits and academic checks.
There is no automatic model fallback or Cloudflare fallback.

## Recovery and boundaries

- Before setup, AI requests are rejected before creating a generation job.
- While a request or background exam/question task runs, connection changes return
  conflict. A task cannot change keys halfway through its pipeline.
- Provider errors are surfaced with fixed messages, HTTP category and an
  allowlisted invalid parameter. Remote error prose is not reflected.
- Reconfiguration resets the old credential's Chat cooldown. Drafts, messages,
  existing outputs and checkpoints are not reset; retry/resume remain explicit.
- Technical concurrency, replay protection and bounded Backend retries remain.
  No total-request allowance or two-hour access window is added by this flow.
- The server binds to `127.0.0.1`. The configuration API checks local peer/host,
  same-origin metadata and a per-process setup nonce; it never returns the key.
  Redirects to another provider host are not followed.
- The key is absent from browser storage and command-line arguments. Root `.env`
  stays ignored by Git. It is plaintext on disk, not an OS credential vault.

The explicit `start-astra-demo.bat` offline walkthrough remains separate.

## Verification and manual handoff

Offline API tests use `httpx.MockTransport`. They cover first startup, atomic file
updates, unchanged academic settings, shared role credentials, invalid configuration,
same-origin/nonce boundaries, active-task conflicts and credential repair after
400/401/403/404/429/503, timeout, malformed JSON and redirect responses.

`python -m scripts.local_connection_smoke` requires Playwright and a frontend build.
It runs desktop/mobile UI flows against an owned temporary configuration and a
synthetic provider. It blocks exam generation and external connections. Fixture
keys never enter the real app's `.env`. The observed flows include masked input,
save without a probe, reload persistence, failed fake Chat, key repair, retained
messages and successful fake Chat after repair.

The final Python run passed 579 tests and 7 subtests with external socket
connections blocked. Frontend build/lint and 91 frontend tests passed. The repository-wide verifier
stops at 89 pre-existing lint errors outside this change; changed Python files
pass Ruff. The actual `start.cmd` entry point was observed serving port 8001 with
the empty masked key dialog. No real provider call or exam generation was initiated
by the agent. Provider authentication, compatible endpoint behavior and academic
quality remain for the owner to test through the UI. No PR, push or deployment is
part of this handoff.
