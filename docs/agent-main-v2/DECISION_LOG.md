# Unified semantic workflow decisions

For engineers continuing Agent V2. These are local implementation decisions, not team-ratified entries in docs/DECISIONS.md. The full current specification is UNIFIED_SEMANTIC_WORKFLOW_SPEC.md.

Current live evidence and authorization: [completion specification](LIVE_CHAT_COMPLETION_SPEC.md), [results](LIVE_CHAT_RESULTS.md). Earlier undeployed-route statements describe their original checkpoint.

## S-001 ? Separate meaning and execution

Use astra-semantic-v1 goals and extracted parameters. Reuse Decision/Intent and React receipts as the execution boundary. Missing domain data pauses in deterministic intake. The alternative was more provider schema cross-field repair; two historical complete JSON responses failed application invariants, so execution-shaped output is being migrated. Live NLU remains unverified.

## S-002 ? Additive wire migration

Preserve generated.json and the legacy hash. Add semantic.generated.json and /v2/agent/interpret. Local clients negotiate semantics with X-Astra-Semantic; old clients receive a conservative compatibility decision. This avoids a big-bang replacement and does not activate a production route.

## S-003 ? Independent admission policies, shared durable ledger

Keep ADMISSION/global-v1 and its consumed counters. Partition attempts, estimated tokens, rates, leases and circuits by workload; reserve Chat daily capacity from MAS. Existing leases without an operation are treated as Chat. Timeout does not refund the attempt or prematurely release uncertain upstream capacity. MAS public forwarding stays absent; internal quota tests are not authorization to expose academic prompts.

## S-004 ? No speculative goal retrieval infrastructure

The 36-goal catalog remains small. Send compact meanings/parameters and structured context with one model call when needed. Exact subject answers use pending-context catalog matching. No vector service, embedding call, model-training pipeline or extra title inference is warranted by current evidence.

## S-005 — Bind remembered questions to observed revisions

Keep the last successfully observed question target in the existing conversation metadata, with source turn, job ID, stable question ID and revision. Resolve an implicit previous-question goal only when all bindings remain current. Branching clears it; retraction and revision changes invalidate it. This permits useful contextual follow-ups without trusting a model-generated question ID or a number copied from stale history. Mixed implicit-reference compositions still ask for clarification.

## S-006 — Share semantic field bounds and retain safe diagnostic invariants

The canonical goal catalog declares subject/topic/grade bounds. Python, TypeScript and generated native/canonical Worker schemas consume them; a regression check compares them with the retained execution intake contract. This prevents an accepted semantic subject from creating a dialogue fact that fails on the next turn. Private adapter failures expose a field path and whitelisted invariant, never the rejected private value. The alternate was unbounded semantic slots followed by later execution validation, which makes contract failures harder to diagnose and recover from.

## S-007 — Answer information requests from current application data

A QUESTION about a question/answer is a read-only inspection workflow. Use the current package, explicit question/part grounding or a valid observed reference, and label the stored key/explanation truthfully. Do not navigate or invoke academic inference to answer it. A mounted test caught the old broad “là gì / như thế nào” routing shortcut replacing such a request with generic guidance; narrowing that shortcut fixes the cause and leaves unfamiliar language to the semantic model. The regression expectation now requires that the old shortcut abstain, while negated operations remain blocked.


## S-007 - Preserve a bounded acceptance session across UTC days

The owner authorized 12 additional upstream attempts total, eight automation plus four manual. Daily counters alone could silently renew that allowance at UTC rollover. Keep per-session usage in the existing ADMISSION/global-v1 ledger, require an absolute expiry, never refund attempts, and archive old daily counters on rollover. A single manual phase raises the same session cap from 8 to 12 without resetting used=8. No new resource or public MAS operation. SQLite restart/rollover, expiry and oversized-limit regressions pass; production usage was preserved through disabled deployments.

## S-008 — Private development Chat can bypass budgets without opening anonymous inference

The owner later requested removal of Chat call limits for development, like MAS. Preserve the bounded implementation and usage, but allow ASTRA_AGENT_BUDGETS_ENABLED=false to bypass daily/session/token/expiry checks. Require an independent revocable Backend caller token whenever this switch is false; bounded legacy clients remain compatible. Retain rate/concurrency/replay/circuit/kill-switch protections and the existing semantic/provider wire. This avoids replacing finite public allowances with an unrestricted anonymous endpoint. Verification is offline plus GET-only readiness; the owner exclusively initiates real inference.
