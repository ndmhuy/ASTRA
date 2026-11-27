# ASTRA — LIVE CHAT RELIABILITY, SEMANTIC ACCURACY AND PERFORMANCE COMPLETION

## 0. PRIMARY OBJECTIVE

Continue the existing ASTRA Semantic Workflow Engine release candidate and make Agent Chat genuinely usable through the existing Cloudflare Worker, AI Gateway and Gemini credential.

The current architecture has already been implemented and extensively verified offline.

The immediate objective is NOT another architectural redesign, another large audit, or another round of synthetic-only testing.

The immediate objective is:

**Natural Vietnamese input → Real AI interpretation → Valid canonical semantic frame → Correct workflow resolution → Actual React operation → Natural and timely user-visible response.**

Complete this path with real runtime evidence, correct observed defects and prepare the application for manual use.

Prioritize:

1. Successful real inference.
2. Correct understanding of user input.
3. Reliable UI orchestration.
4. Conversation context and response quality.
5. Low latency and unnecessary-call prevention.

The owner will arrange the independent MAS API later.

Do not block Agent Chat completion on MAS configuration or integration with the latest main.

---

## 1. RECOVER THE CURRENT CHECKPOINT

Repository:
https://github.com/ndmhuy/ASTRA

Worktree:
D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA.worktrees\longlth2297-agent-main-v2

Branch:
feat/longlth2297/agent-main-v2

Latest reported handoff commit: 37e5004.

Implementation checkpoint: 6951266.

Verify the actual current HEAD, working tree and existing runtime processes.

Read:

- AGENTS.md
- PROGRESS.md
- NEXT_TASK.md
- SEMANTIC_WORKFLOWS.md
- DECISION_LOG.md
- CAPABILITY_MATRIX.md
- MANUAL_ACCEPTANCE_V2.md
- WORKER_RUNBOOK.md
- UNIFIED_SEMANTIC_WORKFLOW_SPEC.md

Use the latest unified release-candidate sections as authoritative.

Older deployment instructions are historical and must not override the current candidate configuration.

### Established implementation

The existing implementation reportedly includes:

- astra-semantic-v1 canonical contract.
- 36 semantic goals.
- 34 React execution adapters.
- Compact Gemini provider-facing schema.
- Deterministic workflow resolver.
- Bounded ordered goal composition.
- Context-aware fast paths.
- Conversation memory and dialogue state.
- Source-linked question references.
- Conversation titles.
- Confirmation gates and execution receipts.
- Independent Agent/MAS admission policies.
- 197 evaluation records/scenarios.
- 56 focused Python checks.
- 39 frontend checks.
- 20 local workerd test groups.
- Mounted browser coverage of all 34 registered adapters.
- Credential-free isolated clone startup.

Verify and reuse these components.

Do not recreate them.

### Established live evidence

The two historical Cloudflare-backed attempts reached Google AI Studio and returned HTTP 200.

The second attempt returned:

- gemini-3.1-flash-lite.
- Complete valid JSON.
- finishReason STOP.
- 2,373 prompt tokens.
- 70 output tokens.
- Provider latency approximately 2.042 seconds.
- Total visible latency approximately 2.956 seconds.
- Failure at an application semantic invariant.
- Zero generation requests.

The exact original conflicting fields were not retained.

The new canonical semantic architecture has not yet been verified live.

Do not assume the historical failures were Gemini overload or timeout.

Do not assume the new implementation is correct merely because fixtures pass.

---

## 2. STRICT SCOPE

Complete Agent Chat first.

Preserve:

- Existing UI/UX presentation.
- Existing React handlers.
- Existing academic Backend logic.
- Existing workflow and confirmation safety.
- Existing conversation memory and persistence.
- Existing Cloudflare resources.
- Independent future MAS configuration.

Keep MAS in explicit demo mode.

Do not:

- Create a new Worker or Gateway.
- Implement another speculative architecture.
- Expand the dataset to 700 merely to satisfy a numerical target.
- Add vector databases or embedding services.
- Train or fine-tune a classifier.
- Add speculative AI providers.
- Enable paid fallback.
- Activate live MAS generation.
- Deploy the ASTRA website or Backend.
- Merge or rebase main.
- Push commits or create a pull request during this task.

The owner intends to review upstream compatibility and prepare a PR only after this Chat candidate works.

Record the current upstream divergence as a known limitation, but do not let it block the immediate live acceptance.

---

## 3. FOCUSED PRE-DEPLOYMENT REVIEW

Inspect the actual source of:

- semantic-catalog.json.
- semantics.py.
- Generated canonical and Gemini schemas.
- TypeScript semantic resolver.
- Instruction recipes.
- Worker request builder.
- Worker response normalization.
- Local Worker provider.
- React execution boundary.
- Existing Chat timeout and state handling.

Spend effort only on defects relevant to successful live Chat.

Verify:

- Every provider-accepted response can be safely interpreted or explicitly rejected at the canonical boundary.
- Harmless omitted/null optional metadata does not reject a valid user meaning.
- Optional title failure does not invalidate the entire turn.
- Required semantic fields remain strictly validated.
- Provider schema and canonical schema are synchronized.
- Domain resolution does not depend on model-generated application IDs.
- No-match, ambiguity and unsupported outcomes are valid results.
- The model does not produce executable React instructions.
- Existing confirmation and state-freshness protections remain intact.

Inspect the semantic prompt for redundant instructions, repeated schemas, unnecessary metadata and excessive history.

Remove only demonstrably unnecessary content.

Do not weaken semantic coverage to reduce token count.

Run the generated-contract checks and focused tests needed to establish deployment readiness.

Do not repeatedly rerun unrelated test suites.

---

## 4. DEPLOY THE EXISTING WORKER V2

I authorize deployment of the current Agent Chat implementation to the existing production Worker:

astra-ai-proxy

Existing Gateway:
astra-gateway

Existing model:
gemini-3.1-flash-lite, unless actual configuration has changed.

Use the existing stored Google AI Studio BYOK credential.

Do not request or expose its secret value.

The historically reported production version is:
bb165c28-5a06-4372-9c9e-b2bf758b9599.

Verify actual production metadata before deployment.

Deploy the updated Worker with forwarding disabled initially.

Preserve:

- Existing Gateway Token Secret.
- Existing account/Gateway configuration.
- Existing BYOK alias.
- Existing ADMISSION Durable Object.
- global-v1 object identity.
- v1-admission migration history.
- All consumed quota records.
- Legacy v1 endpoint compatibility.

Do not delete or recreate durable storage.

Verify the deployed health endpoint reports:

- astra-intent-v1 compatibility.
- astra-semantic-v1 compatibility.
- Matching semantic contract hash.
- Correct model configuration.
- Forwarding disabled initially.
- MAS forwarding disabled.
- Expected persisted quota state.

Verify that the actual deployed environment variables match the intended configuration. Do not assume a Wrangler configuration change necessarily updated existing dashboard settings.

Record a rollback target.

Do not activate billing or any new paid resources.

---

## 5. BOUNDED LIVE INFERENCE AUTHORIZATION

I authorize a maximum of 12 additional real Agent Chat upstream attempts for this entire acceptance session.

This is a maximum, not a requirement to consume all attempts.

Allocation:

- Up to 8 attempts for Codex-controlled diagnosis, corrections and acceptance.
- Reserve up to 4 attempts for subsequent owner manual testing.

Use the actual current UTC ledger day and preserved attempt history.

Do not assume the historical two attempts necessarily belong to the current UTC day.

Do not reset counters or repeatedly increase the allowance.

Do not allow UTC rollover or a process restart to silently expand the approved session allowance.

Every upstream attempt counts, including malformed output, timeout or provider failure.

Respect the actual provider quota and stop below the authorized maximum when required.

Disable:

- Automatic retries.
- Automatic fallback.
- Paid routing.
- Hidden duplicate inference.
- Live MAS inference.

Since the Worker is public, restrict the diagnostic exposure window and account for unrelated traffic consuming the allowance.

If unauthorized traffic prevents controlled testing, disable forwarding and report that specific blocker.

Do not request new permission after every individual attempt within this explicitly authorized budget.

However, stop before exceeding the budget or incurring unapproved costs.

---

## 6. ESTABLISH THE FIRST SUCCESSFUL REAL VERTICAL SLICE

Start the current ASTRA application using the explicit keyless Worker profile.

Use the existing launcher:

python scripts/start_agent_worker.py --port 8000

Build or refresh the frontend as required.

Verify:

- Correct feature worktree.
- Correct current frontend build.
- Correct Worker v2 endpoint.
- No local Gateway Token required.
- No private direct-provider fallback.
- Demo MAS.
- Actual mounted browser application.

Send a natural Vietnamese message that genuinely requires model interpretation.

Example:

“Cô đang muốn chuẩn bị một bài thi thử tốt nghiệp cho học sinh, em giúp cô bắt đầu với.”

Do not count a deterministic fast-path response as live AI verification.

Observe the entire chain:

Browser
→ Local Agent endpoint
→ Worker v2
→ AI Gateway
→ Gemini
→ Provider response extraction
→ Canonical semantic validation
→ Workflow resolver
→ Visible clarification.

Expected behavior:

- THPT family identified.
- Missing subject detected.
- Appropriate question asking which subject the teacher wants.
- No exam-generation request.

Continue with a subject follow-up using the existing conversation.

Example:

“Môn Toán nhé.”

Expected:

- Previously established THPT context retained.
- Correct supported Mathematics format selected.
- Existing setup UI updated.
- No generation without the existing confirmation.

A local subject follow-up is desirable when context is sufficient.

Verify actual UI state and execution receipts.

Do not report success merely because the model returned HTTP 200 or valid JSON.

---

## 7. FIX OBSERVED FAILURES WITHIN THE APPROVED BUDGET

If the live path fails, identify the exact failing stage.

Distinguish:

- Gateway authentication.
- Provider quota.
- Provider overload.
- Network timeout.
- Blocked/incomplete response.
- Provider response extraction.
- Invalid JSON.
- Native schema mismatch.
- Canonical validation.
- Incorrect semantic meaning.
- Catalog resolution.
- Workflow compilation.
- State freshness.
- React execution.
- Receipt observation.
- User-visible response assembly.

For contract failures, capture sanitized structural evidence:

- Field path.
- Invariant ID.
- Safe enum values.
- Missing or conflicting field names.
- Contract version/hash.
- Finish reason.
- Token usage.
- Upstream status.
- Actual latency.

Do not expose credentials, private prompts or unrestricted raw provider output.

Correct the verified root cause offline.

Add a regression test for the observed defect.

Rebuild and redeploy the affected Worker code if necessary, preserving disabled rollout and all quota accounting.

Only then perform another deliberately justified live attempt within the remaining authorized budget.

Do not blindly retry.

Do not hardcode the exact failed user sentence to make the next attempt pass.

Do not bypass canonical validation to force an apparent success.

Do not use a mock response while claiming live inference.

If a failure is clearly caused by exhausted provider quota or an external service outage, stop unnecessary inference rather than repeatedly modifying correct application logic.

The objective is a functioning product, not merely another diagnostic report.

---

## 8. OPTIMIZE NATURAL-LANGUAGE INTERPRETATION

Improve the existing semantic interpreter using actual evidence.

### 8.1 Context priority

Ensure the interpreter receives relevant:

- Current user message.
- Pending clarification.
- Current dialogue goal.
- Established exam family and subject.
- Relevant academic requirements.
- Recent corrections.
- Explicitly referenced previous conversation content.
- Current workspace and UI state.
- Compact semantic goal descriptions.

Avoid passing irrelevant complete history or execution metadata.

Use authoritative state and catalog rather than expecting the model to recall application facts.

Preserve enough context for ambiguous follow-ups.

### 8.2 Fast paths

Keep conservative deterministic paths for:

- Simple greetings.
- Exact contextual subject follow-ups.
- Authoritative job progress.
- Known catalog information.
- Unambiguous stored facts.
- Explicitly supported deterministic operations.

Never route based solely on keyword presence.

Distinguish:

- Request versus question.
- Negation.
- Conditional language.
- Correction.
- Cancellation.
- Quoted or hypothetical commands.

When the meaning is uncertain, use model interpretation or clarification.

Do not expand the rule system into a giant memorized phrase table.

### 8.3 Model output

Keep the model responsible for:

- Dialogue act.
- Semantic goal.
- Relevant parameters.
- Contextual references.
- User constraints.
- Ambiguity.
- Optional natural-language guidance.

Keep these responsibilities in deterministic code:

- Catalog lookup.
- Required-field resolution.
- Workflow selection.
- Actual application identifiers.
- Preconditions.
- Confirmation.
- Execution.
- Receipt-based success reporting.

Do not enlarge the provider schema unnecessarily.

Preserve provider independence.

### 8.4 Response quality

Responses should be concise, natural Vietnamese appropriate for teachers.

Avoid excessive generic error messages.

When the request is understood but unsupported, explain the actual unsupported feature.

When information is missing, ask a specific question.

When a stored answer or exam detail is available, answer from that data.

When an operation succeeds, report its actual result.

Do not claim execution before receipt.

Conversation guidance must not be replaced by rigid error text when the semantic result is valid.

---

## 9. PERFORMANCE OPTIMIZATION

Measure actual end-to-end latency.

Record separately where observable:

- Input admission.
- Local routing.
- Context construction.
- Request serialization.
- Worker admission.
- Gateway/provider elapsed time.
- Response extraction.
- Semantic validation.
- Workflow resolution.
- React execution.
- Total visible response time.

Compare current prompt/output token counts with the historical 2,373/70-token observation for comparable requests.

Do not claim an improvement using incomparable prompts.

Investigate:

- Duplicate system instructions.
- Redundant goal descriptions.
- Excessive conversation history.
- Repeated schema material.
- Unnecessary model reasoning.
- Repeated model calls.
- Blocking frontend or server operations.
- Avoidable network round trips.
- Duplicate submissions.
- Unnecessary conversation-title inference.

Use model-supported lightweight generation settings.

Preserve existing Gemini compatibility.

Do not change models simply to chase lower latency.

### Engineering targets

- Local fast-path routing p95: below 150 ms where practical.
- Normal model-assisted visible response: target approximately 2–4 seconds where provider performance permits.
- Normal chat: zero or one upstream inference call.
- No additional inference for deterministic workflow continuation.
- No separate title inference.

These are optimization targets, not guarantees.

Report actual individual timings and sample size. Do not present a small sample as a reliable population p95.

Do not sacrifice correctness or execution safety for latency.

### Perceived responsiveness

Show an immediate pending state after submission.

Keep the UI responsive while inference runs.

Allow safe cancellation or stale-result suppression according to existing application capabilities.

Do not display misleading success messages.

Avoid introducing streaming complexity unless the current runtime demonstrates a clear need.

### Setup interaction

Investigate the known limitation requiring the teacher to close the setup modal before continuing chat.

If the issue can be resolved through a small integration fix without changing teammate-owned presentation or weakening modal/confirmation safety, fix it.

Otherwise, document the exact UI limitation and defer it to the later team integration.

---

## 10. REPRESENTATIVE LIVE PRODUCT ACCEPTANCE

After establishing the real vertical slice, use the remaining Codex-controlled allowance efficiently.

Choose genuinely varied Vietnamese messages, including examples outside exact development phrases.

Cover as many of the following as the approved budget permits:

### A. Guided exam intake

Natural THPT request followed by subject selection.

Verify pending context and actual setup UI.

### B. Correction and unsupported subject

Request a different subject that the current catalog does not support.

Verify truthful unsupported handling and no silent substitution.

### C. Exam-family switch with negation

Switch from THPT to V-ACT while explicitly requesting no generation.

Verify obsolete state is cleared appropriately.

### D. Information versus action

Ask how an application operation works without requesting execution.

Verify no unwanted UI mutation.

### E. Contextual recall

Ask about an earlier established academic requirement.

Verify correct memory and no fabricated information.

### F. Existing UI orchestration

Use an unfamiliar natural paraphrase requesting an actual supported navigation or inspection operation.

Observe the real React state and receipt.

### G. Out-of-scope request

Verify the Agent can respond without forcing the nearest workflow.

### H. Spam and duplicate input

Verify obvious invalid input and duplicate submission handling without unnecessary live inference.

Use local/offline checks for cases that do not require a provider.

Before testing, define expected semantic meaning, observable application outcome and prohibited side effects.

Do not use only the exact phrases already hardcoded or exercised in fixtures.

Do not count the same successful case repeatedly as broad evidence of model accuracy.

If the model misinterprets a valid request, inspect whether the cause is:

- Missing context.
- Ambiguous goal descriptions.
- Poor prompt guidance.
- Incorrect slot extraction.
- Model capability.
- Deterministic resolver behavior.

Fix the demonstrated cause.

Do not conceal incorrect NLU with a special-case rule for the test sentence.

---

## 11. EVALUATION DATASET

Reuse the existing 197-record/scenario corpus.

Do not expand it to 700 during this task unless a small number of additional cases is necessary to capture real discovered failures.

Record actual live predictions separately from oracle semantic frames.

For each real evaluated turn, retain a sanitized result containing:

- Expected goal.
- Observed goal.
- Expected slots.
- Observed slots.
- Correctness.
- Workflow outcome.
- Unexpected side effects.
- Remote attempt count.
- Token usage.
- Latency.

Maintain development/evaluation separation.

Any previously held-out case used to tune a rule or prompt is no longer independent evaluation evidence for that change.

Do not claim 95% NLU accuracy from fixture-based tests or a handful of successful live requests.

The immediate purpose is to establish real usability and identify the largest remaining failure categories.

---

## 12. PRESERVE THE FUTURE DUAL-API ARCHITECTURE

The owner currently has only the configured Chat API available for testing.

The independent academic API will be selected later.

Preserve:

- AGENT_CHAT provider profile.
- MAS_GENERATION provider boundary.
- Independent attempt/token/concurrency policies.
- Reserved Chat capacity.
- Separate failure handling.
- Existing academic CompletionRequest and response contracts.

Do not use the Chat credential to perform live academic generation.

Do not create a second Worker or Gateway during this phase.

For future handoff, briefly evaluate whether MAS should use:

- A separate operation within the existing Worker; or
- A separate MAS Worker and Gateway.

Consider academic request size, longer deadlines, deployment isolation, independent budgets, paid API risk and caller authorization.

Do not implement speculative remote MAS forwarding now.

The paid or expensive MAS route must remain unavailable until its actual provider and security policy are approved.

---

## 13. OWNER MANUAL TEST HANDOFF

Once Codex-controlled live acceptance is successful:

Start the actual ASTRA application from the current feature worktree.

Provide the working local application URL.

Reserve up to four unused authorized attempts for owner manual testing.

If existing server-side configuration can safely enforce a bounded manual test window, make that allowance available under the existing quota protections.

Otherwise, leave forwarding disabled and provide the shortest safe activation procedure for the reserved manual allowance.

Do not leave unrestricted public inference enabled.

Do not consume the owner's reserved test allowance during automated checks.

Provide a short manual test script covering:

1. Natural THPT request.
2. Subject follow-up.
3. Correction or family switch.
4. Memory or supported UI operation.

Include expected observable behavior, not just expected chatbot text.

Clearly identify which messages use local fast paths and which require the remote model.

If the product still has a serious live defect, report the actual blocker instead of handing over a misleading “ready” state.

---

## 14. PROGRESS, COMMITS AND RELEASE STATUS

Update:

- PROGRESS.md.
- NEXT_TASK.md.
- DECISION_LOG.md where a new architectural decision is genuinely required.

Record progress at meaningful checkpoints.

Make safe local commits.

Do not push or merge.

Keep implementation changes focused.

At completion, produce one concise result summary containing:

### Live integration

- Actual Worker deployment version.
- Active contract version/hash.
- Provider/model.
- Successful real interpretation evidence.
- Actual workflow/UI evidence.
- Zero unauthorized generation.

### Performance

- Number of actual upstream attempts.
- Successful/failed attempts.
- Failure categories.
- Measured visible response times.
- Prompt/output token observations.
- Unnecessary calls removed.

### Product quality

- Real scenarios that passed.
- Real scenarios that failed.
- Verified corrections.
- Remaining NLU limitations.
- Manual test instructions.

### Next phase

- Remaining owner test allowance.
- Current forwarding state.
- Whether Agent Chat is ready for PR preparation.
- Known main divergence.
- Independent MAS API dependency.

Mark each release gate according to actual evidence.

Do not report full production readiness if live MAS, latest-main compatibility or independent NLU evaluation remain unverified.

---

## FINAL DIRECTIVE

Use the existing architecture and infrastructure.

Do not stop after another offline-only implementation report.

Deploy the current Worker v2 under the authorized conditions.

Establish a successful real semantic interpretation and actual application response.

Investigate and correct demonstrated failures within the bounded live budget.

Improve meaningful input handling and latency without overfitting to test phrases.

Keep MAS in demo mode.

Preserve existing safety protections.

Leave the application in a clearly documented state suitable for the owner's manual acceptance.

Do not merge, push or start another major development phase.

The required outcome is a genuinely usable Agent Chat candidate, ready to be reviewed with the team before integration into main.