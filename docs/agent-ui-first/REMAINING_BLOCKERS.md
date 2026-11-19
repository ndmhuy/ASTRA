# Remaining Blockers

1. **Account quota remains externally managed.** Live Agent and Backend calls succeeded on 2026-11-19, but future availability still depends on Google project quota/billing.
2. **The responsive configured model is `gemini-3.1-flash-lite`.** Access to `gemini-3.8-flash` was valid, but inference repeatedly hit `504 DEADLINE_EXCEEDED`; it is not an implicit fallback.
3. **The shared `.venv-agent-ui` currently runs both services.** The README's historical `.venv-win` path remains absent.
4. **Fresh browser integration evidence is absent.** Build and state/executor integration tests pass, but question scroll/highlight and modal interaction need a manual browser pass or restored browser automation.
5. **Approval/export remain teacher controls.** The real handlers exist, but their security/confirmation contracts were not expanded for Agent execution, so the Agent only reports their state.
6. **Application Knowledge artifact is still missing.** Registry-only knowledge remains intact; no document was invented.
7. **Only the existing single-question revision is supported.** Notes are applied sequentially one at a time; no batch Backend capability was fabricated.

Live verification completed on 2026-11-19. Repeat generation only when additional quota/cost is intended.
