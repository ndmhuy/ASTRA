# Existing UI adapter hardening

Baseline: `bb7f59e30b832adb428f819aa56ecc0ad25f4453`, branch `feat/agent-ui-first-merge`. Historical audit files are retained unchanged as baseline findings.

Implemented in this follow-up:

- Added shared deterministic confirmation bindings: workspace/exam/revision/hash, generation format/prompt/catalog, selected editor draft and revision-note contents. Confirmations expire after ten minutes; mismatched or legacy confirmations fail closed.
- Vietnamese `đồng ý` now matches explicit consent; negative phrases do not. Model-visible tokens remain stripped before React authorizes a confirmed action.
- Changing setup selection, editor or workspace invalidates pending consent. Editor save cannot reuse consent for another question/draft.
- Generation progress percentages no longer invalidate an otherwise unchanged action scope. Job identity, revision, navigation and drafts still do.
- Added controller cancellation epochs. Cancellation stops further dispatch and preserves cancelled outcome after a handler returns; it cannot undo an already submitted Backend operation.
- Executor coalesces concurrent identical action IDs as well as reusing completed receipts.
- Note apply verifies the approved job/exam/revision/stable-question binding. Direct note apply errors are routed through the existing UI error handler.
- Availability hints now include closed editor/setup, missing reviewed preview/approval, running generation and missing applicable notes.
- Gemini receives a compact active-task/last-receipt summary for continuation context; credentials and full prior conversation are not added.

Verification: 24 frontend tests, 37 Agent tests, frontend lint/build passed. Chrome fixture test passed six turns covering paper/answers, focus, solution disclosure, editor open/fill/close, supported setup and cancellation. No Gemini inference or Backend generation was executed. Existing build chunk-size warning remains.

Reproduce with Vite running on 5173:

```powershell
npm --prefix astra-frontend test
npm --prefix astra-frontend run lint
npm --prefix astra-frontend run build
node astra-frontend/tests/browserActions.mjs
.\.venv-agent-ui\Scripts\python.exe -m pytest tests/test_agent_ui_service.py -q
```

Boundaries still present: external PDF/log tabs and individual disclosure targeting; no autonomous model replan; pending confirmation is invalidated rather than restored after page reload; approval/export/regeneration require actual Backend state and teacher consent. Multi-tab persistence and multi-worker transactions are Backend/shared-state roadmap items, not repaired here. V-ACT remains unavailable in the UI job contract. This change does not advertise universal control or live language accuracy based on fixture tests.
