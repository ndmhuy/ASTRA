# ASTRA — UNIFIED SEMANTIC WORKFLOW ENGINE, PROVIDER-INDEPENDENT CONTRACTS, DUAL-API INFRASTRUCTURE AND CLONE-AND-RUN RELEASE

## 0. MISSION AND PRODUCT VISION

You are continuing the existing ASTRA Agent V2 implementation.

Act as a senior software architect, conversational AI engineer, application integration engineer and reliability engineer.

Your task is to turn the existing product vision into a functioning, maintainable application, not merely produce architectural proposals or passing fixture tests.

ASTRA is a domain-specific conversational assistant for teachers who create, review, revise and manage examinations.

The intended product experience is:

- Teachers communicate naturally in Vietnamese.
- ASTRA understands goals, context, corrections, incomplete requests and references to previous conversation turns.
- ASTRA identifies which requested operations are actually supported.
- ASTRA selects and composes predefined workflows.
- Existing React handlers perform the actual UI operations.
- Backend MAS remains responsible for academic generation and verification.
- Teachers can continue chatting while an examination is being generated.
- Users can clone and run ASTRA without receiving shared AI credentials.
- The team can replace AI providers and models without rewriting the application.

The central architectural principle is:

**OPEN-ENDED UNDERSTANDING, BOUNDED EXECUTION.**

Natural language is flexible.

Application capabilities are finite, stateful and verifiable.

AI should determine what the user means.

ASTRA should determine how that meaning can be translated into legitimate application operations.

The model must not independently reconstruct the application's execution logic on every request.

Implement this principle through a provider-independent semantic workflow architecture.

This document supersedes conflicting earlier Agent architecture, schema repair, provider configuration and single-API assumptions.

Preserve all compatible verified work.

---

## 1. RECOVER THE CURRENT IMPLEMENTATION CHECKPOINT

Existing repository:

https://github.com/ndmhuy/ASTRA

Existing worktree:

`D:\HCMUS\Year2\Computational Thinking\Lab\ASTRA.worktrees\longlth2297-agent-main-v2`

Existing branch:

`feat/longlth2297/agent-main-v2`

Latest historically reported HEAD:

`8ad3ccf`

The actual HEAD may have advanced. Verify it.

Read:

- AGENTS.md.
- Existing engineering specification under tmp/agent-main-v2/spec/.
- PROGRESS.md.
- NEXT_TASK.md.
- DECISION_LOG.md, if present.
- Capability inventory.
- Existing acceptance and implementation reports.
- Product intelligence refinement documentation.
- Cloudflare Gateway configuration.
- Worker deployment and rollback runbook.
- Actual Agent, Worker, React and Backend MAS source.

Inspect:

- Current Git branch and HEAD.
- Working tree.
- Staged and unstaged changes.
- Recent commits.
- Current running application processes.
- Current provider configuration without exposing credential values.
- Current deployed Worker version where accessible.

Fetch relevant remote refs to understand changes in main.

Do not automatically merge or rebase main.

If upstream has changed, assess relevant compatibility differences and preserve teammate-owned work.

Do not create a new branch or worktree unless genuinely necessary.

Do not discard, reset, clean or overwrite unfinished changes.

Save this master specification into the repository's existing Agent engineering documentation so future coding sessions can recover the latest requirements without depending on conversation history.

### 1.1 Established implementation history

The previous implementation reportedly contains:

- 34 registered semantic intent IDs.
- Instruction compiler.
- UI capability registry.
- React execution adapters.
- Conversation memory.
- Guided exam intake.
- Conversation title generation.
- Confirmation gates.
- Execution receipts.
- State freshness checks.
- Deferred revision notes.
- Cloudflare Worker transport.
- SQLite-backed Durable Object admission controller.
- Persistent atomic quotas.
- Concurrency controls.
- Emergency kill switch.
- Keyless distributed ASTRA profile.
- Direct Gateway diagnostic profile.
- Local Codex CLI diagnostic profile.

Verify these against the current source.

Do not recreate functionality that already exists and meets the requirements.

### 1.2 Established live evidence

The two reported live Cloudflare-backed attempts reached Google AI Studio and returned HTTP 200.

The latest reported attempt established:

- Model: gemini-3.1-flash-lite.
- Gemini finishReason: STOP.
- Complete and syntactically valid JSON.
- 70 output tokens.
- Total visible response time: 2.956 seconds.
- Failure stage: application semantic consistency invariant.
- No accepted semantic decision.
- Zero exam-generation requests.

The exact conflicting field combination was not retained.

The subsequent implementation reportedly introduced exclusive action, intake and guidance schema alternatives.

That correction was deployed and passed focused offline tests, but successful live THPT clarification remained unverified.

Do not claim the exact original conflicting fields are known.

Do not classify these observed failures as demonstrated Gemini overload or network timeout.

Do not spend another blind inference request merely to reproduce the already-established failure category.

Use the current evidence to improve the underlying architecture.

### 1.3 Scope of authority

You may autonomously:

- Inspect source.
- Refine Agent architecture.
- Modify provider adapters.
- Implement workflow resolution.
- Improve context and memory integration.
- Improve Worker request handling.
- Implement isolated quota policies.
- Modify integration and state-management code.
- Create fixtures and benchmark datasets.
- Run focused offline tests.
- Build the application.
- Make safe local commits.
- Update engineering documentation.

Do not autonomously:

- Redesign the existing UI/UX presentation.
- Rewrite teammate-owned academic business logic.
- Replace the Backend's academic model without agreement.
- Invent unsupported functionality.
- Provision new paid resources.
- Enable billing.
- Expose paid unrestricted inference.
- Execute unauthorized live inference.
- Deploy production changes without authorization.
- Push or merge branches.

Proceed independently through all work that does not require external authorization.

---

## 2. NON-NEGOTIABLE ARCHITECTURAL BOUNDARIES

Maintain the following responsibilities.

### Agent

Responsible for:

- Natural-language understanding.
- Conversation context.
- Semantic goal extraction.
- Workflow selection.
- Application guidance.
- Clarification.
- Task coordination.

### Workflow Resolution Engine

Responsible for:

- Mapping semantic goals to actual capabilities.
- Resolving missing information.
- Checking preconditions.
- Composing instruction recipes.
- Binding parameters.
- Evaluating current state.
- Determining next steps.

### React

Responsible for:

- UI state.
- Actual application handlers.
- Navigation.
- User confirmation.
- Application-owned business API calls.
- Execution receipts.

### Backend MAS

Responsible for:

- Exam-generation jobs.
- Academic requirements.
- Academic stage orchestration.
- Question generation.
- Solving and reviewing.
- Domain validation.
- Revisions.
- Artifact generation.
- Academic persistence.

### Cloudflare

Responsible for:

- Centralized credential management.
- Controlled AI inference transport.
- Provider routing.
- Request admission.
- Quota protection.
- Provider-level diagnostics.

Cloudflare must not become a second implementation of ASTRA's conversation, UI or academic workflow.

The Agent must not bypass React to execute business operations directly against MAS.

The AI model must not execute application operations itself.

---

## 3. SEPARATE THE FOUR CONTRACT LAYERS

The current contract consistency failures demonstrate the need for explicit separation.

Implement or formalize the following layers.

### Layer A — Provider-native contract

This contract is specific to the AI provider and model.

It includes:

- Provider request envelope.
- Provider-native structured-output mechanism.
- Generation parameters.
- Response envelope.
- Finish reason.
- Usage metadata.
- Provider-specific error handling.

Gemini, OpenAI and other providers may require different schemas or serialization.

Do not assume they all support the same JSON Schema keywords or structured-output guarantees.

### Layer B — Canonical semantic contract

This is the provider-independent ASTRA representation of user meaning.

It should express:

- Dialogue act.
- User goal or bounded ordered goals.
- Extracted semantic parameters.
- Explicit constraints.
- Corrections and cancellations.
- Relevant contextual references.
- Ambiguity or no-match.
- Optional conversational guidance.
- Optional title suggestion.

It must not require the model to provide executable UI instructions.

### Layer C — Internal execution contract

This is the precise internal representation required by the existing React executor.

It may contain:

- Registered capability IDs.
- Validated parameters.
- Target workspace or question identifiers.
- State version.
- Preconditions.
- Confirmation requirements.
- Idempotency keys.
- Execution dependencies.

These fields should be created by trusted application logic wherever possible.

Do not require the model to invent application IDs, state versions, backend routes or handler names.

### Layer D — Academic domain contract

This is defined by the existing Backend MAS.

It includes:

- Supported exam families.
- Format and subject requirements.
- Academic request schemas.
- Generation constraints.
- Stage-specific schemas.
- Validation rules.
- Job lifecycle.
- Exam revisions.
- Approval and export requirements.

The Agent must consume authoritative domain information without redefining it.

### Contract architecture

Provider-native output
→ Provider adapter
→ Canonical semantic frame
→ Domain and dialogue resolution
→ Existing execution contract
→ React executor
→ Actual application result.

Do not collapse these four layers into one large schema.

---

## 4. DESIGN THE COMPACT SEMANTIC FRAME

Inspect the actual current semantic contract before modifying it.

Determine which existing fields represent:

- User meaning.
- Dialogue decisions.
- Application state.
- Workflow selection.
- Execution parameters.
- Presentation text.
- Internal control metadata.

Move deterministic decisions out of the provider-facing schema when the application can derive them reliably.

### 4.1 Semantic responsibilities

The model should be able to express:

- A request to perform a supported task.
- A question about the application.
- A question about the current exam or job.
- Ordinary conversation.
- A request for guidance.
- A correction.
- A cancellation.
- A confirmation candidate.
- An ambiguous request.
- An unsupported request.
- An out-of-scope request.

It must be possible to produce a valid result containing no executable goal.

The model must never be forced to choose the closest supported action.

### 4.2 Example semantic result

For:

"Cô muốn tạo một đề thi thử tốt nghiệp."

A possible semantic frame is:

```json
{
  "dialogueAct": "REQUEST",
  "goals": [
    {
      "goal": "PREPARE_EXAM",
      "examFamily": "THPT"
    }
  ]
}
```

This is an illustrative design, not a mandatory replacement schema.

The actual representation should be chosen after inspecting the existing source.

The application should then determine that:

- THPT is a supported family.
- The subject has not been provided.
- The current catalog supports Mathematics.
- Additional clarification is required.
- Generation must not begin.

Do not require the model to independently generate all those deterministic consequences.

### 4.3 Schema design requirements

Prefer:

- Small schemas.
- Bounded arrays.
- Stable semantic goal identifiers.
- Clear field descriptions.
- Optional fields where information is genuinely absent.
- Explicit representation of unknown information.
- Minimal unnecessary nesting.
- Provider-compatible structured-output mechanisms.

Avoid:

- Excessive cross-field invariants in provider output.
- Redundant booleans expressing the same state.
- Requiring the model to select between execution and clarification when the application can determine that.
- Arbitrary dictionaries requiring complicated provider-specific validation.
- Internal UI metadata.
- Raw commands.
- Executable code.
- Arbitrary backend URLs.
- Model-generated confirmation tokens.

If a provider requires all schema properties to be present, adapt the provider-native representation without making that requirement part of the canonical contract.

Provider-facing schemas may differ.

Canonical semantics must remain stable.

### 4.4 Normalization and safety

Implement deterministic normalization for explicitly defined harmless representation differences.

For example:

- Known enum aliases.
- Whitespace normalization.
- Defined optional-field defaults.
- Provider-specific null or omitted-field representations.

Do not silently repair:

- Ambiguous user intent.
- Unsupported actions.
- Invalid academic parameters.
- Missing authorization.
- Fabricated target identifiers.
- Contradictory destructive operations.

Do not convert an invalid or uncertain response into the closest executable action.

Reject unsafe semantics or request clarification.

A syntactically valid JSON response is not automatically a valid application decision.

A valid application decision is not automatically authorization to execute.

### 4.5 Versioning and compatibility

Introduce or preserve explicit semantic contract versioning.

Maintain a compatibility strategy between:

- Worker request contract.
- Provider-facing schema.
- Canonical frame.
- Python validation.
- TypeScript contracts.
- Existing distributed clients.

Generate synchronized definitions from an authoritative source where practical.

Avoid manually maintaining multiple inconsistent schemas.

Do not break existing deployed clients silently.

Use a versioned endpoint or backward-compatible migration where appropriate.

Retain the existing execution contract through a compatibility adapter if a new semantic frame is introduced.

Do not perform a big-bang rewrite.

---

## 5. BUILD THE SEMANTIC GOAL CATALOG

Create or refine a central machine-readable catalog describing what users may want to accomplish.

This catalog is not a list of exact command sentences.

Each goal should describe:

- Stable goal ID.
- Semantic meaning.
- Supported dialogue acts.
- Required semantic parameters.
- Optional parameters.
- Relevant contextual references.
- Positive language examples.
- Confusable negative examples.
- Relationship to other goals.
- Possible ambiguity.
- Associated workflow or resolver.

Distinguish semantic goals from low-level executable capabilities.

A goal such as PREPARE_EXAM may involve several existing UI capabilities.

### 5.1 Initial goal families

Inspect the existing 34 intents and organize them into coherent goal families.

Potential families include:

- Application guidance.
- Exam intake.
- Exam configuration.
- Exam generation request.
- Generation progress.
- Workspace management.
- Conversation management.
- Memory recall.
- Exam navigation.
- Question inspection.
- Answer and explanation inspection.
- Question revision.
- Question regeneration.
- Answer verification.
- Deferred revision.
- Preview.
- Approval.
- Export.
- Cancellation.
- Capability inquiry.
- Unsupported request.

These are proposed families, not claims that every capability exists.

Map only to real functions supported by the current application.

### 5.2 Avoid overfitting

Do not map every example sentence directly to an action.

Examples should describe linguistic variation and help evaluation.

Support:

- Vietnamese with accents.
- Vietnamese without accents.
- Informal language.
- Typos.
- Synonyms.
- Indirect requests.
- Short contextual follow-ups.
- Negation.
- Corrections.
- Conditional requests.
- Multiple goals.
- References to prior messages.

The system must generalize from meaning and composition, not memorization.

Do not keep expanding a giant exact-phrase matcher to hide model interpretation failures.

---

## 6. BUILD THE EXECUTABLE WORKFLOW LIBRARY

Reuse the existing instruction recipe library and compiler.

The new semantic layer should connect to existing capabilities instead of replacing them unnecessarily.

### 6.1 Workflow structure

Each workflow should define:

- Workflow ID.
- Associated semantic goals.
- Required information.
- Optional information.
- Applicable application states.
- Preconditions.
- Missing-information behavior.
- Relevant domain validation.
- Available action sequence.
- Conditional branches.
- Expected receipts.
- Failure handling.
- Pause and resume behavior.
- Confirmation requirements.
- Cancellation behavior.
- Postconditions.

Prefer bounded deterministic state machines or existing equivalent orchestration patterns.

Do not introduce a large external orchestration framework unless the current implementation demonstrably requires it.

### 6.2 Example: exam setup

A PREPARE_EXAM workflow should:

1. Read the current dialogue state.
2. Read the authoritative exam catalog.
3. Resolve the exam family.
4. Determine whether a subject is necessary.
5. Ask for missing information.
6. Reject unsupported subjects truthfully.
7. Select the actual supported format.
8. Open or update the existing setup screen.
9. Bind supported fields.
10. Validate requested academic requirements.
11. Report the observed result.
12. Pause before generation when confirmation is required.

If the setup modal is already open, do not reopen it unnecessarily.

If the teacher already supplied the subject, do not ask again.

If the requested format is unsupported, do not substitute another format.

### 6.3 Workflow composition

Do not predefine every possible sequence of user requests.

Allow bounded composition of existing workflows.

For example:

"Mở đề gần đây nhất, cho cô xem câu 5 rồi kiểm tra đáp án."

Resolve the ordered goals.

Execute the workspace-opening operation.

Observe its receipt.

Resolve question 5 within the actual opened exam.

Execute the supported inspection or verification operation under its normal confirmation and inference requirements.

Stop or ask for clarification if an intermediate step fails.

Do not continue dependent actions when their prerequisites are not satisfied.

Do not reorder meaningful user constraints or destructive operations.

Check the entire request for cancellation, negation and contradictions before starting side effects.

Do not execute an early action merely because its phrase appears before a later correction.

### 6.4 Execution limits

Bound:

- Number of goals per turn.
- Number of workflow steps.
- Number of retries.
- Number of state transitions.
- Total execution duration.

A workflow must terminate, pause or report failure.

Never create an unbounded autonomous model loop.

Do not make another AI call after every execution receipt.

Use deterministic continuation wherever the next step is already known.

---

## 7. IMPLEMENT CONTEXT-AWARE SEMANTIC ROUTING

The intended routing architecture is:

Input admission
→ Contextual fast path
→ Optional candidate retrieval
→ Model interpretation when necessary
→ Canonical normalization
→ Abstention and workflow resolution.

### 7.1 Input admission

Reject or limit clearly invalid traffic before remote inference.

Handle:

- Empty input.
- Whitespace-only input.
- Excessively large messages.
- Abnormal repeated characters.
- Rapid repeated submissions.
- Duplicate turn IDs.
- Invalid request structures.
- Exhausted quota.
- Cancelled turns.

Do not treat all profanity, slang, mathematics notation or short messages as spam.

For example:

"Cái đề này khó vãi, giảm độ khó xuống."

This can be a valid application request.

A one-word message such as "Toán" can be meaningful when the system is waiting for a subject.

Use context before rejecting ambiguous short input.

Do not promise perfect spam recognition.

Apply important resource protections in the Worker because local clients can bypass frontend guards.

### 7.2 Contextual fast path

Use zero-inference handling when the meaning and execution context are sufficiently clear.

Examples:

- Reading authoritative job progress.
- Reading known format information.
- Resolving an exact supported subject during a pending subject question.
- Simple deterministic navigation.
- A valid confirmation of one clearly identified pending operation.
- Straightforward cancellation of a known pending task.

A fast path must consider:

- Negation.
- Question versus command.
- Conditional language.
- Current screen.
- Pending task.
- Pending confirmation.
- Corrections.
- Target identity.

If uncertainty remains, use the semantic model or ask for clarification.

Do not execute an action based solely on keyword presence.

### 7.3 Candidate retrieval

Assess whether goal retrieval materially improves the current system.

Possible lightweight methods include:

- Goal-family filtering.
- Normalized vocabulary matching.
- Context-aware lexical retrieval.
- Local semantic retrieval.

Use retrieval to identify relevant candidate goals, not to authorize execution.

Do not automatically pick the nearest instruction.

Do not exclude globally supported workflows merely because they are not available on the current screen. They may become available after navigation.

If retrieval confidence is insufficient, preserve a broad interpretation path or abstain.

Do not rely on an arbitrary similarity threshold.

Do not use model-reported confidence as a calibrated probability without evidence.

With the current relatively small intent inventory, prefer the simplest effective implementation.

Do not introduce a vector database, additional embedding API or model-training pipeline unless comparative evidence justifies it.

### 7.4 Model-assisted interpretation

Use the model when:

- Language is indirect or ambiguous.
- Multiple goals need semantic interpretation.
- Contextual references require reasoning.
- Corrections are complex.
- User wording is unfamiliar.
- The requested operation cannot be resolved safely through deterministic logic.

Send the minimum relevant context.

Normally use one remote model call per turn.

Do not send the complete execution schema of every React capability when compact semantic descriptions are sufficient.

### 7.5 Abstention

Provide explicit no-action paths.

Distinguish:

- Valid task.
- Information request.
- Ordinary conversation.
- Missing information.
- Ambiguous meaning.
- Unsupported product capability.
- Temporarily unavailable capability.
- Out-of-scope request.
- Invalid request.
- Cancellation.

Never require every message to produce an executable intent.

---

## 8. APPLICATION KNOWLEDGE AND ACADEMIC INTAKE

The Agent must understand the actual ASTRA application, not an imagined product roadmap.

Use runtime catalog and existing capability contracts as authoritative sources.

Maintain a compact application knowledge layer.

Separate:

- Stable terminology.
- Supported exam families.
- Supported subjects.
- Supported format versions.
- Locked and editable requirements.
- Available operations.
- Missing prerequisites.
- Temporarily unavailable operations.
- Unsupported functionality.

Do not create an independent academic configuration system.

### 8.1 THPT terminology

The Agent should understand natural references including:

- Đề thi thử tốt nghiệp.
- Đề thi tốt nghiệp THPT.
- Đề thi thử THPT.
- Đề ôn thi tốt nghiệp.
- Đề thi THPT quốc gia, where context supports this meaning.

A generic request such as "Tạo đề thi thử" may be ambiguous.

Use context to resolve it.

When context is insufficient, offer the relevant choices.

Do not silently select an exam family when ambiguity affects the intended result.

### 8.2 THPT subject intake

When the user requests a THPT examination without specifying a subject:

- Retain the THPT family in structured dialogue state.
- Ask which subject the teacher wants.
- Explain the subjects actually supported by the catalog.

When the user responds "Toán":

- Retain the previously established THPT family.
- Resolve Mathematics against the catalog.
- Select the actual supported format.
- Update the setup UI.
- Do not start generation automatically.

If the user requests Chemistry or another unsupported subject:

- Explain the unsupported status.
- Mention available alternatives if helpful.
- Do not silently substitute Mathematics.
- Do not fabricate a format.
- Do not submit invalid generation requests.

Mathematics is the historically reported supported THPT subject. Verify against the current catalog rather than hardcoding it permanently.

### 8.3 V-ACT terminology

Recognize references such as:

- V-ACT.
- ĐGNL ĐHQG-HCM.
- Đề đánh giá năng lực của Đại học Quốc gia TP.HCM.

Distinguish V-ACT from other competency examinations.

Explain the real supported V-ACT format and limitations.

Do not claim partial-exam generation is supported unless the current Backend and UI implement it.

### 8.4 Academic requirements

Preserve topic requirements, academic constraints and corrections.

Only validated academic information should be included in generation requests.

Exclude:

- Greetings.
- General conversation.
- Unrelated requests.
- Stale requirements.
- Cancelled requirements.
- Unsupported assumptions.

Do not invent question-bank availability, retrieval coverage, duplicate-prevention guarantees or random-exam feasibility.

Inspect how the Backend currently selects or generates questions.

Use its authoritative validation and feasibility results.

If a custom/random examination, external question source, upload workflow or partial format is unsupported, explain that clearly.

Do not implement new academic business functionality as part of this Agent integration unless separately authorized.

---

## 9. CONVERSATION STATE AND MEMORY

A conversation Agent cannot rely only on the latest user message.

Implement or preserve four independent state components.

### 9.1 Transcript

Preserve the actual conversation history.

Support existing:

- Message persistence.
- Conversation reopening.
- Retraction.
- Editing.
- Branching.
- Navigation.

Do not introduce a duplicate chat store.

### 9.2 Structured memory

Store important established facts, including:

- Current exam family.
- Subject.
- Selected format.
- Topic requirements.
- User preferences.
- Relevant referenced exam or question.
- Previous decisions.
- Corrections.

Maintain provenance linking important facts to conversation turns where practical.

Distinguish:

- User-provided facts.
- Inferred information.
- Confirmed decisions.
- Current application state.

Do not treat inferred facts as confirmed decisions.

### 9.3 Dialogue state

Track:

- Current conversational goal.
- Pending clarification.
- Missing information.
- Pending workflow.
- Confirmation state.
- Cancellation state.
- Latest correction.

A short answer should resolve against the question actually being asked.

Do not re-ask information the user has already provided.

### 9.4 Fresh application state

Use current authoritative state for:

- Active workspace.
- Active exam.
- Selected question.
- Current screen.
- Current job.
- Job lifecycle.
- Exam revision.
- Available capabilities.
- Pending confirmations.

Conversation memory is not a substitute for current application state.

If history conflicts with fresh state, resolve explicitly.

Do not execute using stale workspace or question references.

### 9.5 Context budget

Use a bounded combination of:

- Recent conversation turns.
- Relevant older messages.
- Structured memory.
- Dialogue state.
- Compact current application context.
- Relevant semantic goal descriptions.

Do not send unlimited conversation history.

Do not make additional remote calls solely to summarize every turn.

Preserve meaningful information when trimming context.

On retraction or branching, recompute or invalidate affected derived memory.

Do not copy pending confirmations blindly into conversation branches.

### 9.6 Memory acceptance

Support:

- "Nãy cô yêu cầu gì?"
- "Cô đã chọn loại đề nào rồi?"
- "Giữ yêu cầu giống lần trước."
- "Thôi bỏ yêu cầu đó đi."
- "Đổi sang V-ACT."
- "Cái câu hồi nãy ấy."

Resolve references when enough evidence exists.

Ask a concise question when multiple plausible references remain.

Never invent a target merely to avoid clarification.

---

## 10. CONVERSATION TITLE GENERATION

Preserve and refine the current title implementation.

The title should summarize the meaningful objective, not truncate the first prompt.

Examples:

- "Cô chưa biết bắt đầu soạn đề từ đâu." → "Hướng dẫn soạn đề".
- "Cô muốn tạo đề thi thử tốt nghiệp môn Toán." → "Đề thi thử Toán THPT".
- "Tập trung đạo hàm và tích phân." → "Đề ôn đạo hàm – tích phân".
- "Cho cô xem cấu trúc đánh giá năng lực." → "Cấu trúc đề V-ACT".

Requirements:

- Natural Vietnamese.
- Concise, informative titles.
- No fabricated academic information.
- No unnecessary personal information.
- Default title for meaningless greetings.
- Initial naming based on the first meaningful goal.
- Limited refinement during the first few meaningful turns.
- Stable title after the initial naming period.
- Manual rename takes precedence.
- Independent from the official exam package title.
- Persistence across reload, generation and revision.

Reuse the existing model interpretation response for optional title suggestions.

For deterministic cases, derive the title from structured goal metadata.

Do not make a separate paid model request just for the title.

A malformed optional title must not invalidate an otherwise valid semantic decision.

Sanitize and bound title text.

---

## 11. UI CAPABILITY RESOLUTION AND ACTUAL EXECUTION

The current capability registry and React executor are valuable existing implementations.

Preserve them.

### 11.1 Distinguish capability availability

Every requested operation should be classified as:

- Supported and currently executable.
- Supported but requires navigation.
- Supported but requires clarification.
- Supported but requires confirmation.
- Supported but temporarily unavailable.
- Unsupported.

Do not conclude that a function is unsupported just because the current screen does not expose it.

Determine whether a valid supported navigation path exists.

### 11.2 Capability coverage

Inspect all actual UI screens and handlers.

Map existing capabilities for:

- Workspace creation and navigation.
- Sidebar operations.
- Setup modal.
- Catalog selection.
- Academic intake.
- Generation submission.
- Generation progress.
- Chat during generation.
- Exam and answer viewing.
- Question selection.
- Revision.
- Regeneration.
- Rechecking.
- Preview.
- Approval.
- Export.
- Conversation management.

Record for each:

- Semantic goal.
- Workflow.
- Actual React handler.
- Required application state.
- Required parameters.
- Confirmation requirement.
- Whether Backend inference is involved.
- Observable success condition.
- Known blocker.

Do not create fake handlers or simulate production success.

### 11.3 Execution safety

Preserve:

- Confirmation gates.
- Context versioning.
- Workspace identity checks.
- Revision preconditions.
- Idempotency.
- State freshness.
- Execution receipts.

A semantic result does not authorize expensive or destructive actions.

An ambiguous confirmation must not execute a pending operation.

A correction must invalidate affected previous confirmation.

An expired or stale confirmation must be rejected.

### 11.4 Truthful responses

The Agent must distinguish:

- Proposed operation.
- Operation awaiting confirmation.
- Operation started.
- Operation completed.
- Operation failed.
- Operation unsupported.

Do not report success merely because an instruction was compiled.

Use actual execution receipts and observed UI state.

The model may generate natural guidance, but factual application claims must be grounded in catalog, state or verified receipts.

Use deterministic response assembly where possible for application outcomes.

Preserve useful natural-language responses instead of replacing every response with generic canned text.

---

## 12. PROVIDER-INDEPENDENT AI INFRASTRUCTURE

Design a shared infrastructure layer without forcing Chat and MAS to share domain contracts.

### 12.1 Provider adapter responsibilities

Each provider adapter should handle its own:

- Request construction.
- Authentication transport.
- Model configuration.
- Supported structured-output mechanism.
- Response envelope extraction.
- Finish reason.
- Usage metadata.
- Provider-native error mapping.
- Timeout handling.
- Normalization.

Provider-specific details must not leak into workflow resolution.

Inspect the existing Gemini adapter.

Preserve direct Gateway and Codex CLI diagnostic adapters.

Design a narrow extension interface for future providers.

Implement additional real provider adapters when their actual API contract is available and needed.

Do not create numerous speculative provider integrations merely to claim broad support.

Use representative alternative-provider fixtures to prove that different native outputs can normalize into the same canonical semantic representation.

### 12.2 Provider capability descriptors

Represent relevant capabilities where needed:

- Native structured output.
- Supported schema features.
- JSON-only mode.
- Tool-call output.
- Streaming.
- Context limits.
- Output limits.
- Cancellation behavior.
- Usage reporting.

Select the smallest reliable supported mechanism for each provider.

Do not blindly submit a Gemini schema to another provider.

Do not bypass strict validation merely because a model lacks a particular structured-output feature.

### 12.3 Provider-neutral errors

Distinguish at minimum:

- Configuration error.
- Missing credential.
- Authentication failure.
- Model unavailable.
- Rate limit.
- Quota exhaustion.
- Provider overload.
- Network failure.
- Timeout.
- Blocked response.
- Incomplete output.
- Invalid JSON.
- Provider schema mismatch.
- Canonical semantic mismatch.
- Application precondition failure.
- Execution failure.

These categories must remain distinguishable in development diagnostics.

User-visible messages should be clear and appropriate.

Do not expose sensitive provider internals unnecessarily.

### 12.4 Transport equivalence

Investigate why direct SDK requests and Worker-mediated requests may behave differently.

Compare:

- Actual model ID.
- API version.
- System instructions.
- Serialized conversation context.
- Schema representation.
- Generation parameters.
- Thinking settings.
- Output limits.
- Response extraction.
- Validation behavior.

Perform offline normalized payload comparison where possible.

Use equivalent response fixtures across adapters.

Do not claim that storing a key in `.env` inherently improves model intelligence.

Do not assume direct SDK and Worker request builders are equivalent without inspecting them.

Live comparison requires an authorized budget and a clearly justified purpose.

---

## 13. MANDATORY DUAL-API ARCHITECTURE

ASTRA must support two independently configured inference workloads.

A. AGENT_CHAT.

B. MAS_GENERATION.

This supersedes previous assumptions that both workloads should share one credential, model, quota or concurrency pool.

### 13.1 AGENT_CHAT

Responsibilities:

- Natural-language understanding.
- Semantic extraction.
- Context interpretation.
- Conversation guidance.
- Memory-related interpretation.
- Optional title suggestion.
- Workflow goal selection.

Requirements:

- Fast lightweight model.
- Compact semantic output.
- Low inference overhead.
- Independent provider credential.
- Independent model configuration.
- Independent rate limits.
- Independent request and token budgets.
- Independent concurrency allowance.
- Independent timeout policy.
- Independent circuit breaker.
- Independent kill switch.

Prefer zero or one remote inference per normal conversational turn.

### 13.2 MAS_GENERATION

Responsibilities:

- Existing academic pipeline inference.
- Question composition.
- Solving.
- Reviewing.
- Other model-dependent stages actually implemented by Backend.

Requirements:

- Independently configured provider credential.
- Independently configured model or existing stage-specific models.
- Actual Backend request and response contracts.
- Academic validation.
- Appropriate context and output limits.
- Independent budgets.
- Independent concurrency allowance.
- Stage-appropriate deadlines.
- Existing Backend-controlled retry and repair policy.
- Independent circuit breaker.
- Independent kill switch.

Do not impose the Agent semantic schema on MAS.

Do not silently change academic models.

Do not reduce academic output requirements merely to match Agent request limits.

### 13.3 Real workload isolation

Separate API credentials alone do not guarantee isolation.

Inspect actual provider quota boundaries.

Two API keys under the same provider project or organization may share limits.

Where real upstream resource independence is required, use independently provisioned quota pools in accordance with provider policies.

The two workloads must not compete for a single application admission pool that permits MAS to exhaust Chat capacity.

Separate:

- Credentials.
- Provider configuration.
- Model selection.
- Request quotas.
- Token budgets.
- Concurrency.
- Retry policies.
- Deadlines.
- Failure isolation.
- Circuit breakers.
- Kill switches.

If a shared global ceiling is required, reserve Chat capacity explicitly.

MAS must not consume that reserved capacity.

Inspect gateway-wide limits and shared infrastructure bottlenecks.

Use the existing Worker and Gateway initially where sufficient.

If they cannot provide effective isolation, document the need for separate gateway routes or resources.

Do not create those resources without authorization.

---

## 14. CONCURRENT CHAT DURING EXAM GENERATION

This is a primary product requirement, not an optional enhancement.

A teacher must be able to continue using ASTRA while a generation job is running.

Inspect:

- React disabled states.
- Chat submission handlers.
- Generation job state.
- FastAPI async behavior.
- Synchronous provider calls.
- Shared process pools.
- Thread pools.
- Background job architecture.
- SSE or polling behavior.
- Worker admission policies.

Identify whether any current implementation blocks Chat during generation.

Fix genuine integration bottlenecks without rewriting academic business logic.

### 14.1 Supported concurrent behavior

During active generation, teachers should remain able to:

- Ask for progress.
- Continue ASTRA-related conversation.
- Recall prior requirements.
- Navigate supported screens.
- Add deferred revision notes.
- Modify deferred notes.
- Cancel deferred notes.
- Ask for application guidance.
- Prepare future tasks.

Generation progress should come from authoritative job state, not a model estimate.

### 14.2 State integrity

Maintain separation between:

- Chat turn.
- Conversation task.
- Pending confirmation.
- Active generation job.
- Immutable submitted generation request.
- Exam revision.
- Deferred revision notes.

A chat turn must not silently mutate a submitted generation job.

If the teacher requests a modification during generation, use the existing deferred revision mechanism where appropriate.

If the user changes the entire generation requirement, explain whether cancellation, restart or later revision is supported.

Do not pretend the active job was modified when it was not.

### 14.3 Concurrent failure behavior

- Chat failure must not terminate MAS.
- MAS failure must not terminate Chat.
- Chat cancellation must not cancel an unrelated generation job.
- Provider timeout must not corrupt application state.
- Repeated chat messages must not duplicate jobs.
- Reconnection must not duplicate generation.
- Late responses must not affect another workspace.
- Quota exhaustion in one workload must not incorrectly disable the other.

Use actual identifiers, idempotency and state-version checks.

---

## 15. INSPECT AND PRESERVE BACKEND MAS CONTRACTS

Before implementing remote MAS transport, inspect the real current Backend source.

Do not infer academic contracts from historical reports alone.

Build a concise stage inventory.

For every model-dependent stage, identify:

- Actual stage name.
- Existing provider interface.
- Request type.
- Input schema.
- Output schema.
- System instructions.
- Context requirements.
- Academic constraints.
- Validation rules.
- Token requirements.
- Model capabilities.
- Retry and repair policy.
- Dependencies.
- Failure recovery.
- Expected number of upstream requests.
- Job and revision consequences.

Inspect existing abstractions such as CompletionRequest or their current equivalents.

Do not duplicate Composer, Solver, Reviewer or other academic components inside Cloudflare.

Do not rewrite the academic generation pipeline.

### 15.1 Academic integrity

Preserve Backend-owned rules concerning:

- Exam format.
- Subject.
- Question types.
- Question counts.
- Difficulty constraints.
- Topic requirements.
- Question-source feasibility.
- Retrieval and question-bank integration.
- Duplicate detection.
- Answer validation.
- Mathematical consistency.
- Review and revision.
- Approval.
- Export.

Only enforce rules actually present in the Backend.

Document genuinely missing capabilities instead of inventing guarantees.

If a requested rule is not implemented, mark it as a Backend dependency.

### 15.2 MAS transport

If the existing provider abstraction supports it, implement a Worker-backed transport adapter without modifying academic behavior.

Keep stage-specific academic request and response contracts intact.

Determine how the Worker can constrain expensive inference operations.

Do not trust a caller-supplied stage name as proof that the caller is an authorized MAS process.

If the existing contract requires arbitrary prompts or schemas that cannot be safely exposed through an anonymous Worker, implement a disabled adapter or a controlled integration boundary and document the blocker.

Do not replace domain validation with superficial JSON validation.

### 15.3 Separate release gate

MAS is currently historically reported to run in demo mode.

The second real provider credential has not yet been confirmed.

Complete feasible integration independently.

Keep live MAS forwarding disabled until:

- Actual provider compatibility is known.
- The independent credential is configured.
- Stage-specific contracts are preserved.
- Resource isolation is verified.
- An appropriate abuse-risk policy is approved.
- Live generation is explicitly authorized.

Agent completion must not be blocked by an unavailable MAS credential.

Do not claim keyless real exam generation is operational until it is separately verified.

---

## 16. EXISTING CLOUDFLARE INFRASTRUCTURE

Preserve the existing resources.

AI Gateway:

`astra-gateway`

Worker:

`astra-ai-proxy`

Worker endpoint:

`https://astra-ai-proxy.letranhoanglong2227.workers.dev`

Existing configured variables reportedly include:

- ASTRA_AGENT_GATEWAY_TOKEN — encrypted Secret.
- ASTRA_AGENT_GATEWAY_ACCOUNT_ID — non-secret configuration.
- ASTRA_AGENT_GATEWAY_ID — astra-gateway.
- ASTRA_AGENT_GATEWAY_BYOK_ALIAS — default.

Existing infrastructure reportedly includes:

- Google AI Studio BYOK credential.
- Gateway Run authentication token.
- Standard Workers AI billing configuration.
- SQLite-backed Durable Object ADMISSION binding.
- Persistent quota accounting.
- Public Worker without Gmail or Cloudflare Access authentication.

Verify against the actual current configuration.

Do not request secret values.

Do not recreate or delete resources.

Preserve existing dashboard variables and encrypted secrets across deployment.

Use the documented current Wrangler configuration mechanism.

Verify provider-native authentication, BYOK routing and supported headers against official documentation.

Prevent unintended Unified Billing fallback where applicable.

### 16.1 Two workload configurations

Preserve the current BYOK alias for Agent Chat unless the actual configuration requires otherwise.

Prepare independent MAS provider and credential configuration.

Use server-controlled:

- Provider.
- Model.
- BYOK alias.
- Endpoint.
- Schema policy.
- Request limits.
- Workload budgets.

The client must not be able to choose arbitrary provider credentials, aliases, upstream URLs or models.

The operator should be able to change models centrally without distributing new API credentials.

### 16.2 Scope of deployment

Deploy only the lightweight AI inference infrastructure when authorized.

Do not deploy:

- React website.
- FastAPI application.
- Backend MAS.
- SQLite exam databases.
- RAG corpus.
- LaTeX compiler.
- Conversation history.

The ASTRA application remains local.

---

## 17. PUBLIC WORKER SECURITY AND PAID API RISK

The current product decision is:

- Private GitHub repository.
- Public Worker.
- No mandatory Gmail authentication.
- No ordinary-user AI credential configuration.

Preserve this for the initial bounded Agent release.

However, a private repository does not authenticate callers of a public Worker.

All local ASTRA installations must be treated as untrusted clients.

An installation ID, claimed device ID, custom header, CORS policy or hidden endpoint URL is not sufficient authentication.

### 17.1 Required protections

Preserve and verify:

- Fixed upstream destinations.
- Explicit allowed operations.
- Provider/model allowlists.
- Strict request validation.
- Actual request-body size limits.
- Response-size limits.
- Input and output token limits.
- Server-controlled schema.
- Server-controlled system instructions where applicable.
- No arbitrary URL forwarding.
- No arbitrary credential forwarding.
- No secret exposure.
- Sanitized responses.
- Emergency kill switches.
- Bounded deadlines.
- Persistent quota enforcement.

Do not expose an unrestricted generic chat-completion proxy.

### 17.2 Paid MAS security gate

The team may purchase an expensive model API in the future.

Do not expose that credential through unrestricted anonymous inference.

A strict global quota limits potential damage but cannot ensure that only intended team members consume it.

If paid MAS inference needs strong caller authorization, propose a suitable trusted-server or user-scoped authorization mechanism.

Do not silently introduce mandatory Gmail authentication against the current product decision.

Do not hardcode a shared secret into the distributed application as a substitute.

Where secure paid anonymous deployment is not achievable under the current constraints, state the trade-off explicitly and keep the expensive route disabled.

Preserve the Agent-only release.

---

## 18. ATOMIC QUOTA, CONCURRENCY AND COST CONTROL

Reuse the existing Durable Object admission controller.

Do not replace it with simple in-memory counters or eventually consistent counters for strict global limits.

### 18.1 Separate accounting

Maintain:

- Global safety ceiling.
- Agent Chat attempt budget.
- MAS attempt budget.
- Agent concurrency limit.
- MAS concurrency limit.
- Appropriate request-size and token limits.
- Independent workload failure state.

Protect reserved Chat capacity from MAS consumption.

IP-based rate limiting is best-effort abuse protection, not authenticated per-user quota.

Use trusted Cloudflare connection metadata rather than arbitrary forwarded headers.

### 18.2 Atomic admission

Before contacting an upstream provider:

1. Validate the operation.
2. Validate configuration.
3. Check workload kill switch.
4. Check request limits.
5. Check rate limits.
6. Check global and workload budgets.
7. Atomically reserve the required admission.
8. Forward only after successful admission.

Persist counters across restart and deployment.

Handle UTC rollover correctly.

Do not reset historical usage when changing daily allowances.

Do not hold database transactions across remote inference requests.

### 18.3 In-flight lifecycle

Use bounded concurrency reservations.

Handle:

- Successful completion.
- Upstream failure.
- Client cancellation.
- Worker timeout.
- Process failure.
- Reservation expiration.

Prevent duplicate release.

Do not automatically refund an attempt when upstream consumption is uncertain.

Do not release concurrency capacity prematurely if an upstream operation may still be running.

Define the limitations of cancellation at the provider boundary.

Fail closed when admission storage is unavailable.

### 18.4 Cost accounting

Distinguish:

- Strict upstream attempt counts.
- Enforced request and output limits.
- Reserved estimated token allowance.
- Observed usage.
- Estimated monetary cost.
- Actual provider billing.

Do not claim an estimated token budget guarantees an exact billing ceiling.

Count actual MAS stage calls, including retries and repairs, rather than only counting exam jobs.

### 18.5 Diagnostic versus normal usage

The current deployment historically uses a one-attempt persisted diagnostic allowance.

Preserve it as an optional diagnostic profile.

Do not impose one inference per day on normal distributed users.

Prepare configurable normal workload budgets.

Do not silently select unlimited inference.

Do not activate the normal public budget before operator approval.

---

## 19. RELIABILITY, LATENCY AND FALLBACK

Optimize actual user experience, not just isolated routing time.

### 19.1 Latency policy

Coordinate:

- Browser deadline.
- Local Agent deadline.
- Worker deadline.
- Upstream provider timeout.
- MAS stage deadlines.

Avoid premature frontend cancellation.

Use the existing generous diagnostic timeout where necessary until reliable measurements exist.

Do not use the old aggressive fallback threshold as an unverified universal deadline.

Record:

- Admission time.
- Context preparation time.
- Request serialization time.
- Upstream inference time.
- Response parsing time.
- Canonical validation time.
- Workflow resolution time.
- UI execution time.
- Total visible latency.

Distinguish time spent understanding chat from time spent generating an academic artifact.

### 19.2 Performance targets

Initial evaluation targets:

- Local deterministic routing p95 near or below 150 ms.
- Normal model-assisted Chat p50 around 1–3 seconds where provider performance permits.
- Prefer zero or one remote call per normal Chat turn.
- No unnecessary inference between deterministic workflow steps.

These are engineering targets, not established performance guarantees.

Measure real behavior before tightening deadlines.

### 19.3 Provider fallback

Preserve a configurable provider-independent routing architecture.

Future alternatives may include a different Gemini model or another provider.

Do not assume another provider is better without evaluation.

Distinguish:

- Temporary overload.
- Rate limit.
- Quota exhaustion.
- Network failure.
- Timeout.
- Model unavailable.
- Authentication failure.
- Contract mismatch.

Do not trigger fallback merely because application validation is broken.

Do not automatically launch a second expensive inference while the first remains active.

If fallback is later enabled:

- Bound additional attempts.
- Respect remaining deadline.
- Reserve quota for every attempt.
- Prevent duplicate UI effects.
- Keep Chat and MAS fallback policies independent.

Do not automatically route normal distributed users to Codex CLI.

Keep automatic fallback disabled during initial controlled validation.

---

## 20. PRECISE DIAGNOSTICS AND CONTRACT FAILURE HANDLING

The previous live failures were difficult to diagnose because the exact conflicting semantic fields were not retained.

Correct this permanently.

Distinguish the following stages:

1. Input validation.
2. Admission.
3. Provider request.
4. Provider HTTP response.
5. Response envelope extraction.
6. Candidate or content extraction.
7. Finish reason.
8. JSON parsing.
9. Provider-native schema validation.
10. Canonical normalization.
11. Canonical semantic validation.
12. Domain resolution.
13. Workflow compilation.
14. UI execution.
15. Receipt observation.

Use stable error codes and invariant identifiers.

For validation failures, record sanitized:

- Contract version.
- Schema hash where useful.
- Failing field path.
- Missing field names.
- Conflicting field names.
- Relevant safe enum values.
- Expected category.
- Finish reason.
- Output length.
- Actual upstream status.
- Attempt count.
- Latency.

Never log:

- API keys.
- Gateway Tokens.
- Authorization headers.
- Full private teacher prompts.
- Full private exam content.
- Unrestricted raw model responses.
- Sensitive conversation history.

For reproducible contract tests, prefer synthetic fixtures and sanitized structural representations.

The next live failure must provide enough evidence to diagnose its category and relevant field-level cause.

Do not keep returning an undifferentiated schema or connection error.

---

## 21. CREATE THE CONVERSATION AND INSTRUCTION EVALUATION DATASET

The owner explicitly wants a structured dataset covering how users may interact with ASTRA.

Build this dataset as an engineering asset.

Do not merely create a list of exact commands.

### 21.1 Dataset A — Semantic intent corpus

Include:

- Natural paraphrases.
- Informal Vietnamese.
- Accentless Vietnamese.
- Typos.
- Indirect requests.
- Domain terminology.
- Short follow-up answers.
- Multi-goal requests.

Each record should contain:

- Input.
- Relevant context if needed.
- Expected dialogue act.
- Expected semantic goal or goals.
- Expected semantic parameters.
- Expected unsupported or ambiguous classification when applicable.
- Prohibited incorrect goals.

### 21.2 Dataset B — Contextual workflow scenarios

Represent realistic multi-turn sessions.

Include:

- Initial UI state.
- Initial application state.
- Conversation history.
- User turns.
- Expected state transitions.
- Expected workflow selection.
- Expected clarification.
- Expected actions.
- Expected receipts.
- Expected visible outcome.
- Prohibited side effects.

Cover THPT and V-ACT workflows from initial intake through supported completion states.

### 21.3 Dataset C — Adversarial and regression cases

Include:

- Spam.
- Repeated characters.
- Duplicate submissions.
- Excessively large messages.
- Prompt injection.
- Unsupported features.
- Ambiguous references.
- Negation.
- Conditional language.
- Contradictory requests.
- Stale confirmations.
- Invalid state.
- Provider failures.
- Malformed outputs.
- Contract consistency failures.
- Context switching.
- Concurrent generation.
- Quota exhaustion.
- Late provider responses.

Reuse the previous 90-case Edge-Case Atlas where appropriate.

Update expected behavior to match actual current application capabilities.

Do not treat historical edge cases as implemented functionality.

### 21.4 Dataset scale

Use approximately 700 labeled records or scenarios as an initial coverage target:

- 300 semantic intent and paraphrase records.
- 100 multi-turn workflow scenarios.
- 100 unsupported, out-of-scope and spam cases.
- 100 negation, ambiguity and conditional-language cases.
- 100 state, concurrency and safety cases.

These counts are coverage objectives, not permission to generate meaningless duplicates.

Prioritize:

- Coverage quality.
- Independent variation.
- Correct labels.
- Actual executable scenarios.
- Meaningful failure cases.

Start with the highest-value representative subset, then expand systematically.

Do not postpone the working vertical slice merely to reach a dataset count.

### 21.5 Dataset separation

Maintain development and independent evaluation partitions.

Avoid placing paraphrases from the same template or scenario family into both partitions.

Do not write exact rules for evaluation examples and then claim generalization.

Record dataset provenance.

Use synthetic data and permitted project fixtures.

Do not collect private teacher conversation data without authorization.

Do not train or fine-tune a model merely because a dataset exists.

The initial purpose is evaluation, regression testing and optional candidate retrieval.

---

## 22. MANDATORY BEHAVIORAL SCENARIOS

Implement and verify representative scenarios that expose real architectural weaknesses.

### A. Natural guidance

"Cô chưa biết bắt đầu soạn đề từ đâu."

Expected:

- Explain current supported workflows.
- Offer useful next steps.
- No generation.

### B. THPT intake

"Cô muốn tạo đề thi thử tốt nghiệp."

Expected:

- Resolve THPT.
- Ask for subject.
- Preserve pending dialogue state.

Follow-up:

"Toán."

Expected:

- Retain THPT context.
- Select real supported Mathematics format.
- Update UI.
- No unauthorized generation.

### C. Unsupported subject

"Thôi cô muốn môn Hóa."

Expected:

- Recognize the correction.
- Check actual supported subjects.
- Explain unsupported status if applicable.
- No silent Mathematics substitution.
- Invalidate affected pending confirmation.

### D. Exam-family correction

"Chuyển sang đánh giá năng lực đi, nhưng chưa tạo."

Expected:

- Resolve V-ACT where context supports it.
- Cancel obsolete THPT requirements.
- Update configuration.
- No generation.

### E. Information versus action

Test separately:

- "Mở cấu hình đề."
- "Cấu hình đề nằm ở đâu?"
- "Đừng mở cấu hình đề."
- "Nếu mở cấu hình đề thì sao?"

Do not treat them as the same intent.

### F. Composition

"Mở đề gần đây nhất rồi cho cô xem đáp án câu 5."

Expected:

- Resolve actual workspace.
- Open it.
- Observe receipt.
- Resolve question 5.
- Perform supported answer-view operation.

### G. Context ambiguity

"Cái câu hồi nãy ấy, làm dễ hơn đi."

If the target is not uniquely established, ask which question.

Do not guess.

### H. Unsupported operation

"Xuất đề thành Word."

If unsupported:

- Explain the limitation.
- Offer actual supported export formats if useful.
- Do not generate a fake Word artifact.

### I. Title and memory

Verify:

- Meaningful initial title.
- Contextual title refinement.
- Manual rename preservation.
- Reload persistence.
- Previous conversation recall.
- Correct behavior after retraction and branching.

### J. Chat during generation

Start a simulated MAS job.

Verify the teacher can:

- Ask for progress.
- Continue chatting.
- Add deferred revision notes.
- Modify or cancel notes.
- Navigate supported screens.

Generation must continue independently.

### K. Quota isolation

Exhaust MAS quota or concurrency.

Chat must retain its reserved capacity.

Exhaust Chat quota.

An unrelated admitted MAS job must not be terminated by that event.

### L. Provider failure isolation

Simulate independent failures for both workloads:

- HTTP 429.
- HTTP 503.
- Timeout.
- Invalid JSON.
- Semantic contract failure.

Verify appropriate independent handling.

### M. Concurrent state change

Switch workspace during a pending model request.

A late response must not execute against the newly active workspace.

### N. Confirmation

Test:

- Valid confirmation.
- Expired confirmation.
- Multiple pending confirmations.
- Cancellation.
- Correction after confirmation creation.
- Duplicate submission.

No unauthorized generation, approval or export.

### O. Provider interchangeability

Use two different provider-native response representations expressing the same meaning.

Normalize them into equivalent canonical semantics.

Verify they produce the same deterministic workflow outcome.

### P. Fresh clone

Start ASTRA from an isolated checkout without the owner's private environment.

Verify the intended keyless runtime profile.

Clearly identify features blocked by missing remote configuration or the disabled MAS credential.

---

## 23. TESTING AND EVALUATION STRATEGY

Do not use test counts as a substitute for product quality.

Do not repeatedly run unrelated hundreds of tests after every small change.

Maintain targeted tests for changed modules and critical regressions.

### 23.1 Layered verification

Distinguish:

1. Provider parsing tests.
2. Canonical semantic contract tests.
3. Domain resolution tests.
4. Workflow compiler tests.
5. Executor tests.
6. Mounted React interaction tests.
7. Worker admission tests.
8. Durable Object persistence and concurrency tests.
9. Fresh-clone startup tests.
10. Live provider acceptance.

Passing mocked model decisions proves the execution path, not actual natural-language understanding.

Passing HTTP health checks proves connectivity, not semantic correctness.

Passing structured-output parsing proves syntax, not correct user intent.

### 23.2 Core metrics

Evaluate and record:

- Semantic goal accuracy.
- Slot extraction accuracy.
- Dialogue act accuracy.
- Context resolution accuracy.
- Out-of-scope recall.
- False rejection of legitimate requests.
- Unsupported-feature classification accuracy.
- False execution rate.
- Task success rate.
- Confirmation violations.
- Schema failure rate.
- Local routing coverage.
- Remote calls per task.
- Input/output token usage.
- Latency p50 and p95.
- Concurrent Chat availability.
- Provider failure isolation.
- Academic contract regression.

### 23.3 Initial acceptance targets

Treat these as proposed engineering objectives:

- Semantic goal accuracy of at least 95% on a representative independent evaluation set.
- Out-of-scope recall of at least 95%.
- Guided workflow success of at least 95%.
- Zero observed unauthorized execution in safety scenarios.
- Zero observed unauthorized generation.
- Zero observed credential exposure.
- No regression in verified existing capabilities.

Report actual measured values.

Do not fabricate benchmark results.

Do not claim that zero observed failures implies zero real-world risk.

Do not claim a large live evaluation was performed when only a few model calls were authorized.

### 23.4 Efficient experimentation

Compare architectures using the same scenarios.

Evaluate:

A. Existing semantic interpretation path.

B. Compact canonical semantic path.

C. Context-aware fast path plus semantic model.

D. Optional candidate retrieval if justified.

Use offline fixtures for deterministic components.

Reserve actual provider inference for questions that cannot be answered by offline tests.

Do not add architecture merely because it sounds advanced.

Choose the simplest implementation that satisfies measured requirements.

---

## 24. IMPLEMENTATION AND MIGRATION PLAN

Follow these phases in order.

### Phase S0 — Recover and establish baseline

- Verify actual branch and HEAD.
- Read source and engineering documentation.
- Inventory existing modules.
- Identify the current contract boundary.
- Identify actual completed and unfinished work.
- Record baseline behavior and blockers.

Do not spend a full development cycle producing another redundant audit.

### Phase S1 — Provider and semantic contract separation

- Identify provider-specific fields.
- Design compact canonical semantics.
- Preserve internal execution contracts.
- Implement provider normalization.
- Establish contract synchronization and versioning.
- Improve precise diagnostics.

First acceptance gate: a representative valid semantic frame can enter the existing compiler without requiring Gemini-specific application invariants.

### Phase S2 — Semantic goal catalog and workflow library

- Map existing intents to semantic goals.
- Reuse existing recipes.
- Add deterministic workflow resolution.
- Implement missing-information handling.
- Support bounded goal composition.
- Add no-match and ambiguity outcomes.

First vertical slice:

Natural THPT request
→ Canonical semantic frame
→ Pending subject clarification
→ Follow-up subject
→ Actual setup UI
→ Observed receipt.

Complete this slice before expanding to every capability.

### Phase S3 — Context routing and memory

- Implement conservative zero-call paths.
- Improve input admission.
- Integrate structured memory and dialogue state.
- Preserve title generation.
- Support corrections, cancellation and reference resolution.
- Preserve useful natural guidance.

### Phase S4 — Capability coverage

- Inspect remaining actual UI operations.
- Map supported semantic goals to real handlers.
- Fix missing feasible integration.
- Preserve confirmation gates.
- Record genuine UI/Backend blockers.

Do not invent functionality to reach nominal 100% coverage.

### Phase S5 — Dual-API and concurrent execution

- Separate AGENT_CHAT and MAS_GENERATION profiles.
- Separate budgets and concurrency.
- Preserve Chat availability during generation.
- Verify failure isolation.
- Protect generation jobs and revisions.
- Preserve deferred revision workflows.

### Phase S6 — Backend MAS transport compatibility

- Inspect actual academic contracts.
- Prepare independent provider configuration.
- Implement feasible transport adapter.
- Preserve domain rules.
- Keep live MAS disabled when external requirements remain.

### Phase S7 — Dataset and independent evaluation

- Reuse existing edge cases.
- Create semantic corpus.
- Create contextual workflow scenarios.
- Create safety and regression corpus.
- Separate development and evaluation datasets.
- Run focused offline benchmarks.
- Record actual results.

Build representative tests throughout previous phases instead of deferring all verification until S7.

### Phase S8 — Cloudflare integration and security

- Preserve existing Worker infrastructure.
- Integrate updated provider-facing contracts.
- Verify persistent quota behavior.
- Add independent workload policies.
- Verify keyless client configuration.
- Prepare safe versioned deployment and rollback.

### Phase S9 — Runtime and deployment acceptance

- Build actual frontend.
- Start correct FastAPI application.
- Verify actual feature-worktree runtime.
- Verify keyless distributed profile.
- Run mounted UI integration checks.
- Prepare production deployment gate.
- Perform authorized live acceptance.

### Phase S10 — Final release and handoff

- Complete remaining product acceptance.
- Document live and offline evidence.
- Document operator configuration.
- Verify fresh-clone behavior.
- Record remaining academic provider dependencies.
- Prepare future provider-extension instructions.
- Update project progress.

Do not restart completed phases.

Continue from existing verified implementation wherever possible.

---

## 25. CONTROLLED LIVE ACCEPTANCE

Do not automatically spend tokens during implementation.

Do not perform another isolated schema retry before completing relevant architectural fixes and offline contract verification.

After the new semantic vertical slice, provider integration and Worker protections are ready, prepare a small staged live evaluation.

### Gate A — Deployment authorization

Before production deployment, report:

- Actual Worker target.
- Current deployed version.
- Proposed changes.
- Contract compatibility.
- Required configuration changes.
- Secret preservation.
- Durable Object migrations, if any.
- Current forwarding state.
- Rollback procedure.
- Free-plan compatibility.

Wait for owner authorization.

Keep existing production behavior safe during migration.

Do not activate an incompatible endpoint for existing clients without a compatibility strategy.

### Gate B — Controlled Agent inference

After deployment and explicit live inference authorization:

Use a bounded allowance.

Do not reset persisted usage history.

Disable automatic retries and fallback initially.

Choose a natural-language message that genuinely reaches the model.

A suitable case is:

"Cô đang muốn chuẩn bị một bài thi thử tốt nghiệp cho học sinh của mình."

Expected:

- Worker admits the request.
- Google AI Studio or the configured provider returns a real response.
- Provider adapter extracts and normalizes it.
- Canonical semantic frame resolves THPT.
- Workflow identifies the missing subject.
- The teacher receives an appropriate clarification.
- No generation request is triggered.

If the request is handled by the fast path, do not claim live provider acceptance.

### Gate C — Multi-turn manual acceptance

After the initial live path is verified and a further budget is approved, verify:

- Natural Vietnamese paraphrases.
- Subject follow-up.
- Unsupported subject.
- V-ACT correction.
- Memory recall.
- Meaningful title.
- Actual UI navigation.
- No unauthorized generation.

Prefer deterministic handling where correct, but record whether a remote call occurred.

Report actual end-to-end timings and upstream attempt counts.

### Gate D — MAS live acceptance

This is separate from Chat acceptance.

Requires:

- Configured independent MAS credential.
- Confirmed model compatibility.
- Verified academic contracts.
- Approved resource policy.
- Explicit generation authorization.

Do not trigger real exam generation merely to test the conversational Agent.

If a live request fails, diagnose the actual observed stage before deciding whether another attempt is justified.

Do not perform blind repeated retries.

---

## 26. CLONE-AND-RUN DISTRIBUTION

The intended ordinary-user experience is:

Clone repository
→ Install dependencies
→ Start ASTRA
→ Use available functionality.

The user must not need:

- Gemini API key.
- OpenAI API key.
- Gateway Token.
- Shared proxy secret.
- Cloudflare account.
- Wrangler login.
- Codex CLI authentication.
- Mandatory Gmail authentication under the current release policy.

The client may contain:

- Public Worker URL.
- Public contract version.
- Non-secret configuration.
- Supported operation identifiers.

It must never contain shared AI or management credentials.

Maintain private developer profiles:

- Direct Gateway diagnostic.
- Direct provider diagnostic where already supported.
- Codex CLI diagnostic.
- Explicit offline/demo mode.

Do not silently select a private developer provider during normal startup.

Do not pretend fixture responses are live AI responses.

Local application functionality should remain usable when remote AI is unavailable.

Document ordinary dependencies such as Python, Node.js, RAG resources and LaTeX.

Verify startup from a disposable checkout without copying the owner's private environment.

Do not claim complete keyless live MAS operation if the independent credential is still absent.

---

## 27. SECRET MANAGEMENT AND RELEASE SECURITY

Keep provider keys inside trusted Cloudflare infrastructure.

Keep Gateway Token inside Worker Secrets for the distributed architecture.

Preserve private local diagnostic credentials only in ignored configuration files.

Never expose:

- Gemini API key.
- Future MAS provider key.
- Gateway Token.
- Wrangler management credentials.
- Codex authentication data.
- Shared administrative credentials.

Audit:

- Git-tracked files.
- Staged changes.
- Outgoing commit history.
- Frontend bundles.
- Worker configuration.
- Environment templates.
- Test fixtures.
- Logs.
- Documentation.
- Generated artifacts.

Do not print secret values during the audit.

Ensure sensitive local files are ignored.

Commit placeholders only.

If an actual credential has entered outgoing Git history, stop before pushing and document the required rotation and remediation.

Do not delete or rotate credentials without authorization.

---

## 28. CONTINUOUS PROGRESS AND CONTEXT RECOVERY

The implementation must survive interruption, quota exhaustion and switching coding agents.

Maintain:

`docs/agent-main-v2/PROGRESS.md`

`docs/agent-main-v2/NEXT_TASK.md`

`docs/agent-main-v2/DECISION_LOG.md`

Update them at every meaningful implementation checkpoint.

Do not wait until the entire task finishes.

### PROGRESS.md

Record:

- Current phase.
- Current branch.
- Current commit.
- Completed requirements.
- Files changed.
- Tests actually executed.
- Actual observed results.
- Runtime evidence.
- External blockers.
- Remaining requirements.
- Deployment state.
- Live inference status.

### NEXT_TASK.md

Record:

- Exact next task.
- Relevant files.
- Required prerequisites.
- Expected acceptance result.
- Known risks.
- Whether owner authorization is needed.

### DECISION_LOG.md

Record:

- Architectural decision.
- Reason.
- Alternatives considered.
- Trade-offs.
- Evidence.
- Affected components.
- Whether the decision remains provisional.

Preserve the full current master specification in the repository.

If previous documents conflict with this specification, explicitly document which requirement is superseded.

Create small safe local commits after verified milestones.

Do not stage private credentials or sensitive logs.

Do not automatically push or merge.

A subsequent coding agent must be able to continue from these files without access to this chat.

---

## 29. REQUIRED DELIVERABLES

Use the existing project structure wherever possible.

Do not create redundant documentation for every minor change.

At minimum deliver:

### Implementation

- Provider-independent canonical semantic contract.
- Provider-native adapter boundary.
- Contract compatibility and normalization.
- Semantic goal catalog.
- Executable workflow library.
- Context-aware routing.
- Input admission and abstention handling.
- Dialogue state and memory integration.
- Conversation title behavior.
- Updated Worker integration.
- Dual inference workload configuration.
- Independent quota and concurrency policies.
- Feasible MAS transport integration.
- Accurate runtime diagnostics.

### Dataset

- Semantic intent corpus.
- Multi-turn workflow scenarios.
- Adversarial and regression corpus.
- Development and independent evaluation partitions.
- Reproducible evaluation harness.

### Documentation

- Updated architecture.
- Capability-to-workflow mapping.
- Provider-extension guide.
- MAS contract inventory.
- Dual-API configuration guide.
- Deployment and rollback runbook.
- Manual acceptance guide.
- Updated PROGRESS.md.
- Updated NEXT_TASK.md.
- Updated DECISION_LOG.md.

### Evidence

- Actual Git commit.
- Focused test results.
- Runtime startup evidence.
- Mounted UI execution evidence.
- Quota and concurrency test results.
- Actual benchmark values where measured.
- Live provider status.
- Fresh-clone status.
- Remaining blockers.

---

## 30. FINAL RELEASE GATES

Use separate, honest status classifications.

### SEMANTIC_CONTRACT_READY

Provider-native output can normalize safely into canonical semantics.

### WORKFLOW_ENGINE_READY

Canonical goals resolve into actual supported workflows.

### CONTEXT_AND_MEMORY_READY

Multi-turn dialogue, corrections, title behavior and state references pass representative checks.

### CAPABILITY_COVERAGE_READY

Actual supported UI capabilities have verified integration or explicit blockers.

### DUAL_API_ARCHITECTURE_READY

Chat and MAS have independent configuration and resource policies.

### CONCURRENT_CHAT_VERIFIED

Chat remains responsive during simulated or authorized real MAS work.

### WORKER_SECURITY_VERIFIED

Admission, quotas, concurrency and credential protections have meaningful evidence.

### LIVE_AGENT_VERIFIED

A real model response has passed the complete ASTRA interpretation path and produced the correct observable behavior.

### KEYLESS_MAS_VERIFIED

Real exam generation works through the independent configured provider without distributed shared credentials.

### FRESH_CLONE_VERIFIED

An isolated checkout starts with the intended keyless profile.

Do not mark a gate verified without the appropriate evidence.

Use separate statuses:

- VERIFIED.
- IMPLEMENTED_NOT_VERIFIED.
- IN_PROGRESS.
- BLOCKED_EXTERNAL.
- NOT_STARTED.

---

## FINAL EXECUTION DIRECTIVE

Implement the architecture.

Do not stop after another audit or conceptual report.

Do not restart ASTRA from scratch.

Do not add arbitrary hardcoded Vietnamese phrases to simulate natural-language understanding.

Do not treat the instruction library as a nearest-sentence lookup table.

Do not make the model responsible for application execution details that deterministic code can derive.

Do not force all providers into one incompatible native schema.

Do not modify Backend academic rules to fit the Agent.

Do not allow MAS to starve Chat.

Do not introduce unnecessary remote inference calls.

Do not expose shared credentials.

Do not deploy the website.

Do not activate expensive anonymous inference without an explicit approved policy.

Start by recovering the actual current source and checkpoint.

Then implement the smallest complete semantic-to-workflow vertical slice.

Expand through the remaining feasible phases.

Continuously verify behavior, correct discovered regressions and record progress.

Complete all work that can be performed independently before stopping for genuinely external requirements.

The final product must be a reliable Vietnamese conversational assistant that understands user goals, safely composes real application workflows, supports replaceable AI providers, and continues operating while an independently configured Backend MAS generates examinations.

**The model understands. The application decides. React executes. Backend MAS owns academic truth. Cloudflare protects shared AI infrastructure.**