# Merge sequence

For the integration owner. Recommendations based on cached ancestry, not GitHub PR status.

## Branch disposition

| Branch (`origin/` prefix omitted) | Relationship to inspected `main` | Action |
|---|---|---|
| `feat/ndmhuy/ct-rag-integration` | ancestor; 0 unique commits | Already included |
| `feat/chautanphat/mas-rag-handoff`, `feat/chautanphat/rag-workflow` | ancestors; 0 unique commits | Already included |
| `feature/mini-composer-illustrator`, `feature/optimize_multiagent` | ancestors; 0 unique commits | Already included |
| `feat/longlth2297/agent-ui-integration` | earlier chatbot work | Use newer M2 branch; do not merge both separately |
| `feat/longlth2297/m2-ui-agent-orchestration` | 43 unique commits; lacks 36 from main | Bring current main into integration; review backend overlap |
| `uiux2` | 44 unique commits; lacks 50 from main | Preserve latest presentation and navigation behavior |
| `staging/rag`, `feat/ndmhuy/rag-corpus` | corpus/data lineage | Consume pinned release; do not merge whole data history |
| `feature/MAS`, `multiagent`, `feature/team-d-proposal`, `merge-mas-and-uiux`, docs branches | historical/alternative work | No bulk merge; review only if owner identifies missing functionality |

## Small PRs, in order

1. Refresh all refs; record SHAs and clean/dirty state. Create an integration branch from latest
   `origin/main` in a separate permitted worktree. Keep current `uiux2` intact.
2. Integrate `uiux2`; verify current UI independently. Resolve shared files by reading both sides.
3. Integrate M2 chatbot changes. Prefer its protocol/controller/service/tests; manually port
   handlers into latest UI. Do not replace `App.tsx` or session state wholesale.
4. Backend supplies requirements descriptor/evaluator; connect one real validated draft fixture.
5. Connect pinned RAG release → intake → chosen engine with one supported request.
6. Add async job/result/edit adapters; connect UI service; implement review-bound export.
7. Run acceptance in [04_TEAM_TASKS.md](04_TEAM_TASKS.md); reviewer approves before main merge.

## Manual reconciliation hotspots

| Files | Preserve/resolve |
|---|---|
| `astra-frontend/src/App.tsx` | Latest direct detailed-setup flow, loading/transitions, full exam names; add Agent handlers |
| `src/state/examSessions.ts` (frontend) | Current workspace behavior + independent Agent pending/error state and origin-session correlation |
| Frontend `package.json`, lockfile, `vite.config.ts` | Merge scripts/deps; keep matching lockfile; add Agent proxy/dev launcher |
| Agent setup capability | Reconcile old `QuickPresetModal` assumption with current detailed/quick entry behavior |
| Root `pyproject.toml`, `README.md`, backend files/tests | Preserve main's RAG integration and newer engines while adding Agent package |
| `handoff/`, `docs/agent/` | Preserve history; point to current executable contract; avoid importing stale proposals as requirements |

These are overlap/review hotspots; a trial merge has **not** established exact Git conflicts.
Never use whole-file ours/theirs for teammate code. Keep logs/decisions from both sides.
