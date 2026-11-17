# Owners and completion gate

For team leads. Assign a person to each team-owned row; check only after observed success.

Individual handoffs: [Backend/MAS](../TEAM_BACKEND.md), [Chatbot](../TEAM_CHATBOT.md),
[UI](../TEAM_UI.md), [RAG](../TEAM_RAG.md), [Corpus](../TEAM_CORPUS.md).

| Owner | Next deliverable | Acceptance |
|---|---|---|
| Integration lead | Pick first engine/scope, job facade and question model; record decisions | All boundary owners use same fixture/version |
| Backend/MAS | Real descriptor/evaluator + engine adapter + job/result endpoints | Invalid draft rejected; valid draft reaches chosen engine; retry returns same job |
| Chatbot | Replace fixture requirements/evaluation ports; emit approved generation plan | Missing fields requested; mock evaluation cannot authorize real generation; no duplicate start |
| UI | Port M2 adapters into latest `uiux2`; connect real exam service | Correct setup screen; chat remains usable during generation; late response stays in origin workspace |
| RAG | Orchestrator callable + intake fixture + pinned release | Scope checks pass; unsupported topic/level gives explicit gap; warnings/provenance retained |
| Corpus | Versioned portable release or reproducible Git snapshot instructions | Clean machine loads verified sources; approval/rights status stays explicit |
| Backend + UI | Stable item IDs/types, revisions, review and export | P1/P2/P3 render correctly for chosen scope; stale edit rejected; changed draft needs reapproval |

## Joint acceptance

- [ ] Clean installation starts UI, Agent and Backend; corpus loads without relying on an
  undocumented developer checkout. Browser proxy/CORS setup works.
- [ ] Chat navigates, creates workspace and opens correct setup; replay/stale plans cause no
  duplicate or wrong-workspace effect. Stop/restart Agent and verify visible retry recovery.
- [ ] One teacher request → validated matrix → real RAG evidence → chosen engine → real UI result.
  No mock progress/questions are presented as actual backend output.
- [ ] Duplicate start/reconnect resolves to same job; generation failures stop progress and show
  an actionable error. If restart durability is deferred, document the local-demo limitation.
- [ ] Counts/types/score totals match matrix; unsupported formats fail explicitly.
- [ ] Solver input excludes Writer answers; source warnings survive to review.
- [ ] Edit invalidates approval; student export contains no answer key; reviewed PDF/DOCX opens.
- [ ] Latest UI behavior survives: direct detailed setup, loading animation, readable exam titles.

## Verification commands after integration

From repository root (installed development environment):

```powershell
python -m pytest -q
python scripts/verify.py
python -m rag_workflow.eval --acceptance
```

From `astra-frontend`, after merging M2's package scripts:

```powershell
npm ci
npm run build
npm run lint
npm test
npm run test:browser
```

M2 browser tests cover local Agent/UI behavior; add the real generation/review/export scenario
above. Record commands/results in the integration PR and member AI log. This inspection ran no
application tests and makes no claim that the combined system passes.
