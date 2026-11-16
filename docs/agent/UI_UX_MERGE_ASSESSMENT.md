# Agent + UI/UX merge assessment

**Date:** 2026-11-16 (Asia/Bangkok)
**Integration branch:** `feat/longlth2297/agent-ui-integration`

## Revisions combined

- UI/UX first parent: `origin/uiux@eb673e33ab667369489307bc8974ff3d2904d86b`.
- Agent/backend second parent: `feat/longlth2297/agent-orchestrator@52ebad671b39e9e78925a0cd976eb5b9d683accb`.
- Merge commit: `cb6dd8ff064875f8544d3b5e5c8f9e1f4cdee8fa`.

The source histories had no merge base. The merge therefore required
`--allow-unrelated-histories`. A merge-tree simulation was run first. The only common path and
the only conflict was root `.gitignore`; it was resolved by preserving both Python and Node
rules. No Agent, backend, or UI source file overlapped.

## Verdict

**Repository-level merge: ready for teammate review.** Both projects coexist, install, lint,
build, and pass their existing tests on the merged tree.

**Functional Agent-to-UI integration: not implemented and must not be presented as complete.**
The React app still uses its placeholder chat response and mock generation service. The Python
Agent currently exposes an in-process API only; no HTTP transport, runtime UI executor, trusted
approval service, or backend teacher-draft converter has been added.

## Verification on the merged tree

| Check | Observed result |
|---|---|
| `python -m ruff check .` | pass |
| `python -m pytest -q` | 318 passed, 1 dependency deprecation warning |
| `npm ci` in `astra-frontend/` | 32 packages installed; 0 vulnerabilities |
| `npm run build` | pass; Vite warns the main JS chunk is 556 kB |
| `npm run lint` | exit 0; two pre-existing unnecessary-escape warnings |
| UI store/service tests | 6 passed, 0 failed |

No LLM, paid API, real generation provider, or external ASTRA service was called.

## PR size and review risk

Against `origin/uiux`, the integration branch adds the existing backend baseline plus the Agent:
294 files, 24,203 insertions, and 7 deletions. This is large because the UI and backend were
developed as unrelated Git histories, not because source conflicts were resolved by overwriting
files.

Recommended PR description: **“Combine UI and backend/Agent histories for integration review”**.
Reviewers should first verify repository layout, merge parent provenance, `.gitignore`, and both
test commands. Do not ask reviewers to treat this PR as a completed chatbot integration.

## Functional blockers for the next PR

1. Replace `ExamSessions.sendMessage` placeholder with a typed Agent transport while preserving
   conversation/workspace addressing.
2. Add a runtime `ScreenContext` exporter and disabled-by-default capability executor.
3. Keep informational chat enabled during generation; current composer is disabled.
4. Agree on Backend `RequirementsDescriptor` and real `DraftEvaluationPort`; the Agent fixture
   cannot authorize generation.
5. Implement trusted request confirmation and exactly one generation-start owner.
6. Reconcile UI job/SSE expectations with the backend's synchronous `/v2/exams/generate`.
7. Add integration tests before enabling any proposed capability flag.

## Suggested review decision

- **Approve this branch as a shared integration baseline** if the team accepts the unrelated
  history merge and large one-time repository import.
- **Request changes** if the team instead wants a clean new root repository or subtree strategy;
  that is a repository-history decision, not a source-code conflict.
- Create a smaller follow-up PR for the first real vertical slice: UI turn transport → Python
  Agent clarification response, with generation still mocked and visibly labeled.
