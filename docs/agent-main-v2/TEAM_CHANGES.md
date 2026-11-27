# ASTRA Agent V2 team changes

For UI, Agent, and MAS reviewers.

| Legacy reference | Decision |
|---|---|
| plan_safety, interpreter | Adapt accent normalization and conservative guards. Current catalog includes V-ACT. |
| UI contracts and capability registry | Adapt the typed action and receipt pattern for the current handlers. Semantic payloads use a single shared catalog. |
| executor, orchestrator, confirmation | Adapt observed effects, 4-step budget, target bindings and exact confirmation. Discard the version overwrite before dispatch. |
| context, client | Adapt bounded context and same-origin transport. Rebind to the current session model. |
| Gemini provider | Adapt structured output and safe error classification. Use bounded async transport in place of SDK thread and long retries. |
| legacy service app/config | Adapt admission patterns to existing app. Opaque browser identifiers do not establish authenticated tenant identity. |
| App, store, UI components | Use the versions from current main with narrow wiring. |

## Review surfaces

- UI and conversation changes are in `astra-frontend/src/agent/`, `App.tsx`, the existing components, and `state/examSessions.ts`.
- The same-origin transport and Gemini configuration are in `src/exam_baseline/agent/`. The shared typed catalog is under `resources/agent/`.
- MAS transport changes are confined to settings and the existing Chat Completions adapter. The pipeline, prompt, orchestration, jobs, storage and academic contracts stay on the existing implementation.
- New backend work for shared hosting would require ownership scoping on job access and atomic admission by workspace. The local branch has no public deployment change.
- Model and operator-dependent work is recorded in the runbook. The branch is local for review.
