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
- Blanket negation and obsolete V-ACT guards prevent capabilities the application
  actually implements. The starting branch already rejects ambiguous named
  workspace matches; that guard was preserved, not claimed as a newly fixed bug.

## Verification boundary

All automated verification uses deterministic fakes/fixtures. Real inference,
real research and real exam creation are prohibited. The eventual local app
will be launched without submitting any chat or generation request.
Legacy Worker routes and hashes must remain compatible. New Worker code is
prepared locally only; deployment is a separate owner action.

## Delivered local implementation

Source milestones: `74068ba` (baseline), `a2e0d4f` (canonical pipeline),
`39fb43b` (grounded handlers and mounted verification), plus the final local
handoff commit reported in the session. Worktree:
`D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA.worktrees\longlth2297-agent-intelligence-v3`.
The final fetch still resolved `origin/main` to the starting base; local `main`
was left untouched. Nothing was pushed and no PR was opened.

The production turn now uses `agent/intelligence.ts`: admission → one local
canonical result or one configured interpretation → strict canonical validation
→ plan → actual typed adapters → observed receipts. There is no second lexical
draft extractor after a model question, invalid result, or provider failure.
Legacy `recipes`/`semantics` remain for compatibility and regression evidence;
they are not a second production authority after a V3 conclusion.

`resources/agent/registry-v3.json` owns 57 goals and 55 typed adapter contracts.
`agent/v3.py`, the native builder, generated Worker resources, and frontend read
the same registry. V1 catalogs/hashes are frozen. Scoped excluded goals, NO_WEB,
information/action boundaries, conflicting slot corrections, bounded parameters,
and optional title normalization are validated before effects.

`agent/examSpec.ts` owns source-linked requirements in `session.intake`. The card
and modal project that spec and use the same parameter builder. Requested counts
remain visible when a fixed preset differs; the effective Backend parameters use
the explicitly selected preset. Subject changes clear the old topic and preserve
compatible difficulty, requirements and source choices. UI edits revoke pending
confirmation. Removed/foreign selected document IDs fail closed at submission.
The modal no longer appends old raw chat instructions over an existing spec.

Each workflow step dereferences the current React runtime. Opening a target
workspace waits for its actual package before resolving a dependent question.
Reads of current status/library/documents tolerate unrelated progress; question
and write operations still bind the workspace, job, revision/hash, editor draft,
spec, document selection and confirmation expiry. Confirmation retains a bounded
remaining tail for synchronous successful steps. An accepted background operation
stops dependent execution and records the remaining objective in chat for a fresh
user-requested continuation; it does not promise automatic completion after a job.

Responses use catalog values, stored answers/explanations, actual candidates,
precondition failures and receipts. No response/title-only LLM call was added.
Actual V-ACT question regeneration is no longer rejected by obsolete frontend
math-only guards; the existing Backend group/passage safeguards still decide it.
Adjacent practice also persists its actual subtopic (for example SAT Math), counts,
time, difficulty, requirements and source preference. NO_WEB is distinct from
“attachments only”; it survives follow-up edits and takes precedence over the web
toggle. Its versioned limits are checked against the actual Backend schemas in a
test: 4–20 questions, 5–180 minutes without research, 5–120 with web research, and
zero attached files for adjacent practice. Unsupported file-based SAT/IELTS
requests stop before research or generation rather than failing after consent.

## Detailed adapter inventory

All paths below start at `astra-frontend/src/App.tsx` and existing service methods
in `services/examService.ts` / `state/examSessions.ts`. Parameters are semantic
names/numbers; internal IDs are resolved from the current application, not supplied
by the model. “Confirm” is an operation confirmation, not a budget approval.

| Adapters | Real effect / route | Required state and parameters | AI / confirm / gesture; failure |
| --- | --- | --- | --- |
| OPEN_SETUP, CLOSE_SETUP, HOME, CREATE_SESSION, SET_SIDEBAR | React navigation; workspace persistence via PUT `/api/workspaces/{id}` | Draft/error for setup; wide screen for sidebar | No AI; closed/missing/ineligible UI fails |
| SHOW_FORMATS, SELECT_FORMAT, FORMAT_DETAILS, PREPARE_GENERATION | GET `/api/exam-formats`, evaluate; V3 bridges preset IDs through the actual catalog into canonical spec slots | Available format/version; subject/family disambiguation; fixed limits | No AI for configuration; generation separately confirmed; no arbitrary Math fallback |
| LIST_SESSIONS, OPEN_SESSION, RENAME, DELETE_SESSION | workspace list/search/save/archive | Unique explicit name or unambiguous recent workspace; existing target | No AI; delete confirms; ambiguity lists/asks rather than choosing first |
| RECALL, SET_DRAFT, CHAT_MESSAGE | Transcript/draft, clipboard, branch/retract; existing workspace branch route | Current source-linked message number; user-only retraction | No AI; retract confirms; clipboard may require browser gesture/permission and can fail |
| STATUS, WARNINGS, RECOVERABLE_JOBS | Actual job state/package/library GETs | Current or uniquely resolved eligible job | No AI; no inferred completion from health or timeout |
| PAUSE_GENERATION, CANCEL_GENERATION | Existing job pause/stop routes | Actual job/execution version | No new AI call; receipts distinguish requested pause/stop from confirmed result |
| RESUME_GENERATION, RETRY_GENERATION | Existing same-job resume/retry | Paused/interrupted/recoverable state; current execution version | AI continuation; confirm; Backend leases/checkpoint fencing retained |
| SET_VIEW, FOCUS_SECTION, SCROLL_TOP, FOCUS_QUESTION | Existing paper/review/PDF canvas controls | Loaded current package; unique number/section; visible canvas | No AI; unavailable preview and duplicate numbers are explicit failures |
| INSPECT_QUESTION | Stored key, explanation, TF subitem, verification/approval/metadata | Source-linked recent reference or explicit unique question at current revision | No AI or navigation; never re-run solver to answer stored-key requests |
| OPEN_EDITOR, PATCH_EDITOR, CLOSE_EDITOR, SAVE_EDITOR | Existing editor; PUT question through `editQuestion` | Current stable ID/revision; valid explicit field/value; editor not busy | No AI; save confirms with draft snapshot; server validation errors retained |
| VERIFY_QUESTION, REGENERATE_QUESTION, APPROVE_QUESTION | Existing verify, regeneration and approval APIs | Current stable ID/revision; explicit instruction for regeneration; approval eligibility | Verify/regen use AI and confirm; approval confirms; no auto-approval or relaxed validation |
| ITEM_REGENERATION_STATUS, STOP_ITEM_REGENERATION | Existing question-operation map/API status and stop | Operation belongs to current workspace/job | No new inference; missing/untracked operation is reported, not replaced by whole-job stop |
| ADD_NOTE, CANCEL_NOTE, REVIEW_NOTES, APPLY_NOTES | Existing deferred-note workflow and bounded apply | Actual job/question, source message, eligible notes | Recording/reading/cancelling has no AI; applying confirms existing bounded academic work |
| OPEN_HISTORY, LIST_VERSIONS, INSPECT_VERSION, RESTORE_VERSION, UNDO_CHANGE | Existing history/read/restore and recorded-change undo routes | Actual job/version/change; unique candidate; revision/hash fences | Reads no AI; restore/undo confirm; ambiguous “old” never selects arbitrary version |
| LIST_DOCUMENTS, USE_DOCUMENT, DETACH_DOCUMENT, UPLOAD_GUIDANCE | Workspace document metadata/preview/selection, detach; existing upload UI | Unique actual filename in this workspace | No AI; detach confirms; actual upload requires user file picker; no fabricated content |
| PREPARE_PRACTICE | Existing adjacent practice and `/agent/research` | Supported topic; 4–20 questions; 5–180 minutes built-in / 5–120 with research; no attachments supported | Web only for relevant semantic goal; NO_WEB retained; actual generation separately confirmed |
| APPROVE, EXPORT, EXPORT_DOCUMENT, EXPORT_ARTIFACT, RETRY_PREVIEW | Existing approval/export/preview routes | Current approved revision/hash; PDF readiness; requested artifact/format | Export confirms; teacher JSON stays teacher JSON; unsupported matrix/format is explicit |

Existing durable checkpoint recovery, timeout/retry/concurrency, validation,
academic prompts/schemas, scoring, RAG, LaTeX and export business logic were not
rewritten. A previous real generation's academic quality or provider failure was
not reproduced here because live inference was prohibited.

## Verification and limits of the evidence

| Evidence | Observed result |
| --- | --- |
| Frozen 40-case routing baseline | 6 accepted, 6 correct for specified goals/slots; 15% local coverage |
| Revised same 40 cases | 18 accepted, 18 correct for specified goals/slots; 45% coverage; no incorrect accepted route observed |
| Development / challenge split | 18/24 development cases accepted; all 16 challenge cases deferred to the model |
| Python suite, external socket connections blocked | 551 passed + 7 subtests |
| Final versioned interpretation type/admission follow-up | 37 focused API/provider tests passed with fake transports |
| Frontend | 91 passed; TypeScript/Vite build and oxlint passed |
| Mounted V3 React / synthetic Backend fixtures | 17 scenarios, zero generation requests, zero real inference |
| Retained mounted adapter suite | 19 observed adapters; two fake verification/preview writes; zero upstream inference |
| Chat Worker | TypeScript check and 26 workerd tests passed; outbound inference replaced by deterministic fixtures |
| Shared resources / repository scanner | V1 and V3 generated contracts synchronized; no newly detected credential/artifact additions |
| Common `scripts/verify.sh` | Compile step passes; stops at 89 pre-existing Ruff findings in unrelated files |

`eval/agent-v3/local-results.json` contains the routing outcomes and engine hash.
`eval/agent-v3/verification.json` records the observed test logs, runtime negotiation
and source file fingerprints, separately from language-understanding scores.
The corpus remains frozen. It was authored and later inspected by the engineer;
it is not blind evidence. Later comparisons are regression measurements, not a
new independent challenge. The additional SAT grammar preserves an existing
product behavior; it did not turn the challenge examples into accepted routes.

The 100% figure applies only to the 18 accepted **specified goals and slots**.
It is not overall language accuracy, target accuracy in every state, or model
accuracy. All 16 harder challenge utterances require model interpretation, so
the requested generalization/95% challenge goal has **not been established**.
The target 800–1200 independent meaningful utterances has not been delivered:
this change adds 40 frozen scenarios alongside the retained 153 semantic,
144 local, 23 adversarial and workflow/context fixtures. Counts are not inflated
with punctuation variants or by relabeling deferred messages as understood.

Avoided model calls are a routing counterfactual (18/40 locally resolved versus
6/40), not measured bill savings. Cold local routing for the 40 cases took about
14–16 ms; this excludes HTTP, React and inference. Native fixture request/schema
sizes are 14,786/3,942 bytes versus V1's 10,031/2,745 bytes. No real token usage,
Gemini latency, exam quality, real generation success or V-ACT academic outcome
was measured. No paid research or inference smoke test was run.

## Cloudflare handoff — prepared, not deployed

Exact target: Worker **`astra-ai-proxy`**, directory `workers/astra-ai-proxy`,
existing gateway **`astra-gateway`**. New endpoint: `/v3/agent/interpret`.
Legacy `/v1` and `/v2` routes and hashes remain supported. The Durable Object
binding/name, caller credentials, admission/duplicate/rate/kill-switch state and
MAS Worker infrastructure were left in place; no billing/resource change occurred.

The running Backend reports `/agent/capabilities` as:
`clientContract=astra-semantic-v3`, `providerContract=astra-semantic-v1`,
`compatibility=explicit-legacy-bridge`, `workerDeploymentRequired=true`.
The bridge preserves the model's meaning, question/constraints and failure. It
cannot make the old production model contract understand newly added V3 goals.
Full model-assisted V3 acceptance is blocked on an authorized remote deployment.

Owner/operator procedure, **not executed by this task**:

1. Record the currently deployed Worker version ID for rollback. Review the local
   diff, then in `workers/astra-ai-proxy` run `npm ci`, `npm run check`, `npm test`.
2. After separate deployment authorization, run `npx wrangler deploy` from that
   directory, preserving the existing variables/secrets/DO namespace. Do not
   deploy `astra-mas-proxy`, reset admission state or create resources.
3. After the V3 route is published, set
   `$env:ASTRA_AGENT_SEMANTIC_VERSION='astra-semantic-v3'` for the local Backend
   launcher and restart only that intended app instance. Keep the same model,
   caller profile and MAS configuration. Owner submits all real acceptance turns.
4. Roll back the local setting to `astra-semantic-v1` first if required. Roll back
   Worker code with `npx wrangler rollback <recorded-version-id> --name astra-ai-proxy`.
   No deployed version ID was fetched or invented in this task.

Existing shared caller-token distribution in the repository predates this work.
It remains an owner security concern; no tokens are reproduced here, rotated,
expanded or copied into new files. The scanner's result is not a claim that this
pre-existing distribution issue has been redesigned or removed.

## Manual acceptance

Running URL: **http://localhost:8003**. Actual entry point:

```powershell
Set-Location -LiteralPath 'D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA.worktrees\longlth2297-agent-intelligence-v3'
.\start.cmd --port 8003 --no-browser
```

It is already running; do not start a duplicate instance on that port. The
launcher uses this worktree's `.venv-win`, the existing profile
`C:\Users\LENOVO\AppData\Local\ASTRA\worker.env`, real Chat/MAS configuration,
and `demoMode=false`. Health reported `providerConfigured=true`; that is a
configuration observation, not a successful inference/authentication test.
The actual served React landing screen was inspected with no console errors;
all non-GET/model/research requests were blocked during that read-only inspection.
No chat text was filled or sent and no generation request was submitted. Native
desktop browser automation was unavailable (native pipe missing); the screenshot
is from the actual served app in a separate headless browser, not a mocked UI.

Owner-only scenarios:

- “Soạn đề THPT” → ask for subject in the existing draft; “Hóa nhé em” → same spec.
- “Soạn đề tiếng Anh THPT cho tao” → English card; completed/paused old jobs stay intact.
- “Đề Hóa THPT có bao nhiêu câu?” / “Đừng tạo đề, chỉ xem cấu trúc Hóa THPT” → catalog answer, no draft/generation.
- Request 20 questions/30 minutes for Chemistry → preserve mismatch visibly; standard preset only on explicit user choice.
- Edit topic/difficulty/requirements, then select Biology → old topic clears, other compatible fields remain; old confirmation cannot run.
- With web enabled, “Tới đâu rồi?” → current status; no web search. SAT practice remains a separate bounded request.
- On a real completed paper, ask stored P2 question/subitem answer → stored data; fresh verification requires its own confirmation.
- After authorized V3 deployment, try indirect pause/cancel, named document selection, item-only stop, initial-version inspect versus restore, and teacher JSON versus student Word.

Known limits: no independent model evaluation; no matrix artifact in this Backend;
teacher artifact only JSON; adjacent practice does not accept attachments;
upload/clipboard/browser download can require a user
gesture; item-operation tracking is limited to operations known by the current
client; old/duplicate version/workspace/question names require clarification.
Mixed spec preparation plus unrelated control goals may still clarify rather than
execute a partial plan. Accepted background operations require an explicit fresh
continuation; there is no persisted executable workflow across application restart.
