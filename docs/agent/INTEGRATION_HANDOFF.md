# Integration readiness handoff

## Delivered offline interfaces

- `RequirementsProvider` and versioned `RequirementsDescriptor`.
- `DraftEvaluationPort` with explicit mock implementation.
- `TurnRequest`/`TurnResponse`, dynamic revisioned draft, deterministic understanding.
- Trusted approval validation and idempotent mock start.
- Compact job snapshot, one-active-job gate, and deferred-change ledger.
- Disabled-by-default capability registry and receipt-driven mock navigation.
- Optional `SemanticUnderstandingPort`; no model implementation or network call.

## Backend checklist

1. Supply an authoritative teacher-facing descriptor, presets, versions, and errors.
2. Implement draft evaluation/conversion to a backend-owned resolved request/`ExamMatrix`.
3. Define trusted approval storage, actor authorization, expiry, hash, and supersession.
4. Implement idempotent job start/lookup, durable snapshot/events, final package semantics.
5. Define canonical question IDs/revisions and deferred batch validation/application.
6. State auth, quotas, persistence, retention, cancellation, and unknown-outcome recovery.

## UI checklist

UI sends the teacher's message and trusted context to Agent as transport. Agent decides the
semantic instruction; UI validates/executes it and returns a receipt. “UI calls Agent” must not
be interpreted as UI owning intent or orchestration.

1. Export fresh structured `ScreenContext` and state version; never send DOM/raw file objects.
2. Install and runtime-validate only agreed capabilities; keep registry flags false beforehand.
3. Return serial receipts after committed UI state and preserve partial success.
4. Replace placeholder chat response and separate chat loading from job generation state.
5. Implement trusted confirmation UI bound to the exact backend preview/hash.
6. Preserve conversation/workspace/job/exam/question identity across navigation and late replies.

## Joint gate

Choose an integration branch/worktree and test actual backend validation, approval, one start
caller, status/final package, UI context/executor, and edits. Until those tests pass, report:

- Offline conversational core: implemented.
- External boundaries: mock/proposed/blocked as listed.
- “ASTRA chatbot integrated”: **not complete**.

Do not guess endpoint names, modify teammate branches, overwrite `App.tsx`, or reinterpret the
current synchronous `/v2` response as an async job receipt.

## Next smallest milestone

Backend supplies one reviewed `RequirementsDescriptor` fixture and one supported evaluator
callable returning `needs_input`/`validated_ready`. Replace only the fixture adapters and add
contract tests; keep generation and UI execution mocked until their contracts exist.
