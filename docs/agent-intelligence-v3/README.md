# Agent intelligence V3 — engineering record

For ASTRA maintainers. Base: `dcc214d903102a23fd81727edb835ec840cdb873`.
Work is local on `feat/longlth2297/agent-intelligence-v3`; no push, PR or deployment is authorized by this task.

## Baseline frozen before implementation

`eval/agent-v3/scenarios.json`: 40 synthetic, engineer-authored stateful cases,
24 development and 16 challenge cases in separate families. This is not a blind
human evaluation. SHA256: `e7c82e123ae4c373a991d434bf0b301097a385f3dfa82f7b9151ddaae3f4f231`.
The challenge is frozen, not a tuning set. Any later use to fix behavior must be disclosed.
Existing semantic/local/workflow/adversarial corpora remain regression evidence.

`node --experimental-strip-types scripts/evaluate_agent_v3.mjs --output=eval/agent-v3/baseline.json`
observed 6/40 accepted local meanings, 6/6 correct among those accepted (15% coverage).
Neither a deferred request nor generic clarification is scored as understanding.
No provider, model, browser, generation or academic validation was invoked.
This routing baseline does not measure end-to-end safety or model quality.

## Capability grounding (source → effect)

| Surface / adapter | Service and backend | Preconditions, effect, failure |
| --- | --- | --- |
| Chat configuration / QuickPresetModal | format catalog → evaluate → start generation | Real catalog; fixed counts/time; user confirmation; generation costs AI |
| Library / ExamSessions | workspaceLibrary → `/api/workspaces` | Search candidates must be unique; draft writes; archive/branch/undo use backend revisions |
| Generation progress | ExamSessions pause/resume/retry/stop → existing job routes | Actual lifecycle; same-job resume; paid continuation confirmed; receipts distinguish pending from done |
| Paper / review | package questions and stored key/explanation | Read only; repeated question numbers need section; no new verification |
| QuestionEditor | update/verify/regenerate/approveQuestion | Stable question ID and current revision; verify/regen cost AI; existing Backend supports V-ACT group safeguards |
| Question progress | questionRegeneration status/stop | Actual operation ID scoped to workspace/job; stop request is not completed cancellation |
| ExamVersionHistory | history list/read/restore | Version includes job ID; read has no restore; restore confirms and invalidates approval |
| Attachments | inputDocuments upload + workspace documents | Upload requires user's file picker gesture; metadata/preview only, no arbitrary disk/file-content access |
| Export | downloadExport student/teacher/matrix | Current revision approval and supported formats; PDF readiness; never replace requested artifact |
| Web preference | researchAdjacentTopic → `/agent/research` | Explicit relevant semantic goal, supported adjacent topic; toggle alone must not trigger research |

Academic model, prompts, schema, retry, checkpoints, validation, rendering and
export business rules remain owned by the existing Backend.

## Confirmed root causes

- `App.sendTurn` performs research before interpretation and re-runs raw draft
  extraction after non-action meaning or provider failure.
- Frontend semantic registry merges 36 remote goals and seven local-only goals;
  Python/native/Worker see only the 36-goal contract.
- `chatDrafts` duplicates `session.intake`; confirmation closures capture old
  configuration while the visible card remains editable.
- Global render epochs invalidate unrelated read-only turns; writes still need
  strict target, revision/hash, editor and confirmation checks.
- First-match workspace search, blanket negation and obsolete V-ACT guards
  prevent capabilities the application actually implements.

## Verification boundary

All automated verification uses deterministic fakes/fixtures. Real inference,
real research and real exam creation are prohibited. The eventual local app
will be launched without submitting any chat or generation request.
Legacy Worker routes and hashes must remain compatible. New Worker code is
prepared locally only; deployment is a separate owner action.
