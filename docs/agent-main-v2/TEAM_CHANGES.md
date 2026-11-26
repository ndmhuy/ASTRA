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
