# Gemini AI Mode and Offline Mode Setup

Gemini is mandatory whenever Agent AI mode is selected. A separate, explicitly labelled offline mode supports deterministic UI commands without claiming Gemini inference. The browser never receives the key.

## Verified provider choice

Live checks on 2026-11-19 selected `gemini-3.1-flash-lite`: it completed the Agent structured plan in 3.3 seconds, while accessible `gemini-3.8-flash` repeatedly returned `504 DEADLINE_EXCEEDED`. Official structured-output documentation supports JSON Schema/Pydantic through the maintained `google-genai` SDK.

Runtime account/project access remains authoritative. The implementation never silently substitutes a model.

## Key-free default

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn astra_agent_ui.app:app --app-dir src --host 127.0.0.1 --port 8010
```

Default values:

```text
AGENT_MODE=offline
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_API_KEY=<absent>
```

The service health response exposes only `geminiKeyConfigured: false`, never a value.

## Explicit opt-in setup

1. Install the optional maintained SDK:

   ```powershell
   python -m pip install -e ".[agent,dev]"
   ```

2. Copy `agent-service/.env.example` to `agent-service/.env.local`.
3. Put the developer's key only in the ignored local file:

   ```text
   AGENT_MODE=gemini
   GEMINI_MODEL=gemini-3.1-flash-lite
   GEMINI_API_KEY=<developer supplies locally>
   ```

4. Verify ignore coverage without printing the file:

   ```powershell
   git check-ignore -v agent-service/.env.local
   ```

5. Start the Agent service, confirm `/agent/health`, then use one sanitized UI request. Do not send student data, private documents, answer keys or attachments.

## Model behavior and failure policy

- The model receives at most the teacher message, minimal workspace/screen/job/note summaries and current capability descriptions.
- It receives no Backend endpoint catalog, provider credential, full exam, answer key, arbitrary LocalStorage or attachment content.
- Output is constrained to `GeminiPlan` (maximum four decisions), then revalidated against the current callable registry.
- The model has no tools and cannot invoke the UI or Backend.
- Each attempt is limited to 15 seconds; one selected-5xx retry has a 32-second total budget. Output is capped at 900 tokens; temperature is 0.1.
- In Gemini mode, every natural-language turn calls Gemini before any action proposal is returned.
- Missing key, 401/403, 404, 429, timeout and other provider errors return explicit HTTP errors; there is no deterministic fallback.
- Offline mode returns `provider="offline"` and is never represented as Gemini-powered.
- Unknown/invented actions are rejected both in the Agent service and UI executor.

## Live smoke result

`LIVE VERIFIED`: direct Agent interpretation returned HTTP 200 in 4.83 seconds, and a Vite-proxied interpretation returned HTTP 200 in 2.77 seconds with `provider=gemini`. One separately authorized Backend job completed 22 questions using the same model through independently configured Backend credentials.

## Secret checks performed

- `agent-service/.env.local` is covered by existing `*.local`/`.env*` rules.
- Static scan found no `VITE_*GEMINI` variable.
- Production frontend build contained no `GEMINI_API_KEY` marker.
- Agent responses and health never return the secret.
- No real key was created, read, printed, committed or transmitted.

Teacher BYOK remains future work. Do not store keys in LocalStorage or add browser key settings to this slice.
