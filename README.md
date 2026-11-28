# ASTRA

ASTRA generates and verifies THPT and V-ACT practice exams. The local app serves
the teacher workspace, FastAPI Backend, retrieval and four-agent pipeline together.

## Run locally

Install Git, CPython 3.11 and Node.js 24 or newer, then run from the repository:

```powershell
.\start.cmd
```

The launcher prepares dependencies, builds the UI and opens
[ASTRA at localhost:8001](http://localhost:8001). First startup may take a few minutes.

1. Paste your API key into the masked **Kết nối AI** dialog.
2. The default endpoint is `https://api.nghimo.com/v1`, model `nghi/claude-haiku-4.5`.
   Expand **URL & model** if your compatible API uses different values.
3. Press **Lưu và vào ASTRA**. The Backend saves the shared key in the ignored root
   `.env`. Chat and exam generation now use this same local connection.

Saving or starting the app makes **no model request**. Your own chat/generation
actions call the API and use your provider's quota. There is no Cloudflare account,
Worker token or CLI chat login to configure in this startup flow.

The sidebar's **API key đã lưu** button lets you update the connection later.
An empty key field retains the existing key. Wait for active Chat/generation tasks
to finish, or stop them, before changing it. Restarting or switching branches in
the same checkout retains `.env` and the local `runs/` workspace data.

Use Ctrl+C to stop. Choose another port with `.\start.cmd --port 8004`.
On macOS/Linux, use `python3.11 scripts/run_app.py`. `--check` reports installation
metadata only; it never installs, starts or probes a model.

## Local credentials and failures

The app writes `EXAM_PROVIDER`, `EXAM_MODEL`, `ASTRA_GEMINI_API_KEY` and
`EXAM_BASE_URL`, preserving unrelated settings/comments. Despite its historical
name, `ASTRA_GEMINI_API_KEY` holds the key for the selected compatible provider.
The key remains in the local Backend and `.env`; it is never returned by the
configuration API or stored in browser storage. `.env` is plaintext local storage:
anyone able to read your files can read it. Keep it out of Git and shared folders.
See [`.env.example`](.env.example) for credential-free optional settings.

API authentication, quota, timeout and invalid-response failures keep saved
workspaces and existing generation checkpoints. Correct the connection, then use
the UI's retry/resume controls. The app does not silently switch model or generate
a replacement exam. Actual credentials and provider compatibility are only checked
when you initiate a real action; **API key đã lưu** is not an authentication claim.

The local server binds to loopback. Configuration saves require the local page's
setup nonce and same-origin checks. Existing Cloudflare scripts remain available
for rollback, but `start.cmd` does not read Worker profiles or shared caller tokens.
No Cloudflare resources are modified or deployed by local setup.

## Exam review and PDF

Choose **Soạn từ mẫu**, select a subject and prepare a draft. Review the questions
and answers, open **Xem trước PDF**, approve the current revision, then export the
student paper and teacher key. Academic checks, bounded retries, concurrency and
checkpoint/resume remain part of the existing Backend.

PDF preview needs XeLaTeX, LuaLaTeX or Tectonic. The optional Windows installer:

```powershell
.\.venv\Scripts\python.exe scripts/install_latex_compiler.py
```

The launcher fetches the pinned Math retrieval corpus when a shallow clone lacks
it. This downloads Git objects without switching branches or running inference.
The [MAS planning backend](docs/mas/) is included in the standard install.
For a separate offline fixture walkthrough, use `.\start-astra-demo.bat`.

[Integration guides](docs/integration/CONNECTED_THPT_UI.md) ·
[CLI guides](docs/guides/) · [Project report](docs/reports/ASTRA_Trial_and_Success_Report.md)
