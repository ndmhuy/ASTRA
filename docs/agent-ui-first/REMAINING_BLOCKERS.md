# Remaining Blockers

1. **Live Gemini remains unverified.** The current health endpoint reports configured Gemini mode/model, but no authorized inference was made in this implementation. Model access and quota must be checked separately before one controlled Agent turn.
2. **Live Backend generation remains unverified and potentially costly.** It requires explicit authorization after provider quota review. No health/config flag is proof of an outbound model request.
3. **Backend runtime unavailable in this shell.** The README command references `.venv-win`, which is absent in this worktree. Recreate/install the documented Backend environment before the three-service run; do not substitute an unreviewed interpreter for a paid job.
4. **Fresh browser integration evidence is absent.** Build and state/executor integration tests pass, but question scroll/highlight and modal interaction need a manual browser pass or restored browser automation.
5. **Approval/export remain teacher controls.** The real handlers exist, but their security/confirmation contracts were not expanded for Agent execution, so the Agent only reports their state.
6. **Application Knowledge artifact is still missing.** Registry-only knowledge remains intact; no document was invented.
7. **Only the existing single-question revision is supported.** Notes are applied sequentially one at a time; no batch Backend capability was fabricated.

Future controlled live test: start the three services, verify quota/model access without exposing keys, authorize one safe Agent interpretation, inspect the returned provider and UI receipt, then separately authorize one Backend generation if cost is accepted.
