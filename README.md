# ASTRA

ASTRA generates and verifies THPT and V-ACT practice exams. This guide runs the
teacher workspace, FastAPI backend, retrieval and four-agent pipeline together
on Windows with a live model.

## 1. Install

Open PowerShell in the repository root. Use Git, CPython 3.11.1 and Node.js
22.12 or later.

```powershell
python -m venv .venv-win
$astraPython = '.\.venv-win\Scripts\python.exe'
& $astraPython -m pip install -e '.[dev]' -c requirements-tested.txt
git fetch --no-tags origin 8b8fb7b09182b3d9d1eee0b95818027f52ab004d
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

The Git fetch loads the pinned corpus used for Math retrieval. For PDF preview,
use XeLaTeX, LuaLaTeX or Tectonic. If none is installed, run the Windows installer.

```powershell
& $astraPython scripts/install_latex_compiler.py
```

## 2. Configure the model

Edit the root `.env` and replace the existing provider and model settings. This
example uses the OpenAI Chat Completions endpoint. Use a model ID enabled for your
API project and keep your key in `.env`.

```dotenv
EXAM_PROVIDER=chat_completions
EXAM_MODEL=<YOUR_MODEL_ID>
EXAM_API_KEY=<YOUR_API_KEY>
EXAM_BASE_URL=https://api.openai.com/v1
EXAM_TOKEN_LIMIT_FIELD=max_completion_tokens
EXAM_RESPONSE_FORMAT=json_object
EXAM_MAX_OUTPUT_TOKENS=16384
EXAM_TIMEOUT_SECONDS=120
```

Use the provider-specific settings in [`.env.example`](.env.example) for Gemini
or Anthropic. Restart ASTRA after changing `.env`.

## 3. Run and generate

```powershell
.\start-astra.bat
```

The launcher installs frontend dependencies on first use, builds the UI and
starts the backend in the same terminal. Open [ASTRA on port 8000](http://127.0.0.1:8000/).

1. Choose **Soạn từ mẫu**, select a subject and generate a draft.
2. Review the questions and answers, then open **Xem trước PDF**.
3. Approve the current revision and download the student paper and teacher key.

Use Ctrl+C to stop. If port 8000 is busy, set `$env:ASTRA_PORT = '8001'`
before starting and open port 8001. For an offline Math or V-ACT walkthrough,
run `.\start-astra-demo.bat`.

[Integration and troubleshooting](docs/integration/CONNECTED_THPT_UI.md) · [CLI guides](docs/guides/) · [Project report](docs/reports/ASTRA_Trial_and_Success_Report.md)
