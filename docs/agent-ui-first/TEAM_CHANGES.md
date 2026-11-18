# Team-Owned Wiring Changes

This file is the review checklist for teammates whose merged UI files were changed. No ASTRA business Backend, RAG, generator, validation schema, storage, preview, approval, or export implementation was modified.

| File | Before | After / reason | Verification | Review risk |
|---|---|---|---|---|
| `astra-frontend/src/App.tsx` | Chat appended a canned response; composer disabled while generating; handlers were not Agent-callable | Connects chat to `AgentClient`; exports sanitized context; maps eight allowlisted capabilities to existing App/store handlers; executes proposals and reports observed receipts; keeps chat available during generation; renders notes | Build/lint, executor tests, real browser create/open/setup/help | Largest wiring change. Review React state/ref timing and desired response wording |
| `astra-frontend/src/state/examSessions.ts` | `sendMessage` appended user plus canned assistant; no note state | Separates user/assistant appends; persists UI-owned deferred notes; add/update/cancel methods; completion asks for review and says notes are not applied | Existing session tests plus note/completion tests | LocalStorage schema gains optional `agentNotes`; migration supplies `[]` |
| `astra-frontend/src/components/Workspace/ChatPane/ChatHistory.tsx` | Suggestions advertised unsupported subjects/counts | Suggestions now cover setup, verified help, and status only | Build/lint and browser observation | Product wording review |
| `astra-frontend/src/components/Workspace/ChatPane/ModernChatBar.tsx` | Attachment and web-search controls appeared usable; generation could disable all chat | Unsupported controls are disabled and labelled; `busy` only blocks duplicate in-flight Agent turns | Build/lint; browser accessibility tree confirmed disabled labels | Product may prefer hiding instead of disabling |
| `astra-frontend/src/styles/integratedWorkspace.css` | No note-ledger styles | Adds compact visible pending-note styling | Build and browser-rendered app | Visual review at mobile breakpoints |
| `astra-frontend/vite.config.ts` | Proxied only `/api` to business Backend | Adds independent `/agent` proxy to loopback port 8010 | Real browser requests returned 200 | Dev-only proxy; deployment needs an explicit equivalent |
| `pyproject.toml` | No conversational Agent package/command | Adds optional `agent` extra for `google-genai` and `astra-agent-ui` console entrypoint | Python import/tests and direct Uvicorn launch | Dependency lock/review before team install |

## New integration-owned files

| Area | Files | Purpose |
|---|---|---|
| Frontend protocol | `astra-frontend/src/agent/contracts.ts` | Typed snapshot, decision, proposal, note and receipt contracts |
| Runtime registry | `astra-frontend/src/agent/capabilities.ts` | Real/unavailable manifest, input validation and observed-effect rules |
| Freshness | `astra-frontend/src/agent/context.ts` | Monotonic version over sanitized state fingerprint |
| UI executor | `astra-frontend/src/agent/executor.ts` | Default-deny execution, stale checks, idempotency, receipts, plan dependency stop |
| Transport | `astra-frontend/src/agent/client.ts` | Same-origin session bootstrap and typed Agent turn request |
| Note UI | `astra-frontend/src/components/AgentNotes.tsx` | Visible pending ledger with cancel and prepare-edit controls |
| Agent service | `src/astra_agent_ui/*` | Loopback service, deterministic Vietnamese interpreter, optional Gemini, future knowledge boundary |
| Safe config | `agent-service/.env.example` | Credential-free local configuration template |
| Tests | `astra-frontend/tests/agentUi.test.mjs`, `tests/test_agent_ui_service.py` | UI executor/store, service security, language, Gemini-failure and knowledge fixtures |

## Behavior intentionally unchanged

- `ExamSessions.generate` still calls the existing `IExamService` path and retains its one-job-per-workspace guard.
- `QuickPresetModal` still fetches catalog truth through `examService` and its ordinary `/api` route.
- Question edit/regenerate, preview, approval and export still use the existing UI service adapters and backend invariants.
- The Agent service does not import or receive `examService`; the React UI remains the sole business caller.
- The setup modal's existing **Tạo đề thi** button remains the only confirmation that can launch generation. Agent opens the modal but cannot click or bypass it.

## Suggested reviewers

- UI owner: `App.tsx`, chat components, note presentation and responsive behavior.
- Agent/integration owner: protocol, deterministic interpreter, model adapter and trace wording.
- Security reviewer: loopback/origin/session-token policy and local deployment assumptions.
- Backend owner: confirm by inspection that no business-core file changed and no new Agent business path exists.
