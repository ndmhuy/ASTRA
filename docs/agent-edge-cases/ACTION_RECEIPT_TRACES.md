# Cost-free receipt traces

Test source: `astra-frontend/tests/browserActions.mjs`, Chrome + actual React/Vite. Synthetic exam fixture; Agent HTTP and business API intercepted. No external inference. Baseline f9523e9.

| Cases / given state | Input and typed fixture | Observed effect/receipt | Type/result | Limit |
|---|---|---|---|---|
| NL01, completed synthetic workspace | Vietnamese request to view answers -> ui.exam.view_mode `{mode:review}` | review button aria-pressed=true, visible answer label, task completed | REAL_UI_PASS | fixture selects action; live NLU not tested |
| NL04, current paper | review then focus question 1 | answer remains visible, focus class set, 2 completed steps and last receipt success | REAL_UI_PASS | synthetic question |
| IN01/IN10, setup closed | open_setup -> configure_setup with real resource format fixture | actual catalog request, selected radio, 2 successful receipts, awaiting_confirmation | REAL_UI_PASS | no generation submission |
| NL07, synthetic question | editor open then fill stem | actual editor textarea contains updated draft; no save call | REAL_UI_PASS | provider output injected |
| SAFE09/SRC07/RND10 | random/bank request -> unsupported fixture | message shown, paper tab unchanged, no generation | REAL_UI_PASS | Python source guard separately UNIT_PASS |
| IN12, request in flight | hold response, click new exam, release old action | original workspace receives stale message, start screen stays open, no old action executed | REAL_UI_PASS | browser navigation rather than server ownership revocation |
| JOB10 UI-task portion | cancel pending setup confirmation | toast removed; no generation | REAL_UI_PASS | Backend cancellation remains blocked |

Additional executed units: wrong target returns TARGET_CHANGED without calling handler; same actionId with changed params returns ACTION_ID_CONFLICT; cancelled async task remains cancelled and never dispatches second step; invalid mixed dependency plan returns clarification only; BANK_ONLY returns unsupported; Q5 request with proposed Q8 clarifies. Failure receipts retain sanitized provider_unavailable/network/stale codes. No unit fixture is described as real model output.
