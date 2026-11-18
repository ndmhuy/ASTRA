# Optional Gemini Local Setup

Gemini is optional. ASTRA's deterministic UI commands, unsupported-feature answers, status explanation and registry-based help work with no key. The browser never receives the key.

## Verified provider choice

As checked on 2026-11-18, Google's official model catalog lists `gemini-3.8-flash` as stable, and official structured-output documentation supports JSON Schema/Pydantic through the maintained `google-genai` SDK: [Gemini model catalog](https://aistudio.google.com/docs/models), [structured outputs](https://aistudio.google.com/docs/structured-output), [API key security](https://aistudio.google.com/docs/api-key), and [rate limits](https://aistudio.google.com/docs/rate-limits).

Runtime account/project access remains authoritative. The implementation never silently substitutes a model.

## Key-free default

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn astra_agent_ui.app:app --app-dir src --host 127.0.0.1 --port 8010
```

Default values:

```text
AGENT_LLM_ENABLED=false
GEMINI_MODEL=gemini-3.8-flash
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
   AGENT_LLM_ENABLED=true
   GEMINI_MODEL=gemini-3.8-flash
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
- Output is constrained to `GeminiDecision`, then revalidated against the current callable registry.
- The model has no tools and cannot invoke the UI or Backend.
- Inference timeout is 15 seconds; output is capped at 500 tokens; temperature is 0.1.
- Missing key/disabled mode falls back to deterministic clarification.
- 401/403, 404, 429, timeout and other provider errors return bounded safe fallback text. UI actions are not retried automatically.
- Unknown/invented actions are rejected both in the Agent service and UI executor.

## Live smoke result

`BLOCKED_EXTERNAL / NOT RUN`: no developer key or explicit live-inference opt-in was supplied during this implementation. No Gemini quota was consumed and no claim of live model success is made. The fake-provider, missing-key, quota and invented-action tests passed offline.

## Secret checks performed

- `agent-service/.env.local` is covered by existing `*.local`/`.env*` rules.
- Static scan found no `VITE_*GEMINI` variable.
- Production frontend build contained no `GEMINI_API_KEY` marker.
- Agent responses and health never return the secret.
- No real key was created, read, printed, committed or transmitted.

Teacher BYOK remains future work. Do not store keys in LocalStorage or add browser key settings to this slice.
