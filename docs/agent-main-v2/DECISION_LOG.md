# Unified semantic workflow decisions

For engineers continuing Agent V2. These are local implementation decisions, not team-ratified entries in docs/DECISIONS.md. The full current specification is UNIFIED_SEMANTIC_WORKFLOW_SPEC.md.

## S-001 ? Separate meaning and execution

Use astra-semantic-v1 goals and extracted parameters. Reuse Decision/Intent and React receipts as the execution boundary. Missing domain data pauses in deterministic intake. The alternative was more provider schema cross-field repair; two historical complete JSON responses failed application invariants, so execution-shaped output is being migrated. Live NLU remains unverified.

## S-002 ? Additive wire migration

Preserve generated.json and the legacy hash. Add semantic.generated.json and /v2/agent/interpret. Local clients negotiate semantics with X-Astra-Semantic; old clients receive a conservative compatibility decision. This avoids a big-bang replacement and does not activate a production route.

## S-003 ? Independent admission policies, shared durable ledger

Keep ADMISSION/global-v1 and its consumed counters. Partition attempts, estimated tokens, rates, leases and circuits by workload; reserve Chat daily capacity from MAS. Existing leases without an operation are treated as Chat. Timeout does not refund the attempt or prematurely release uncertain upstream capacity. MAS public forwarding stays absent; internal quota tests are not authorization to expose academic prompts.

## S-004 ? No speculative goal retrieval infrastructure

The 36-goal catalog remains small. Send compact meanings/parameters and structured context with one model call when needed. Exact subject answers use pending-context catalog matching. No vector service, embedding call, model-training pipeline or extra title inference is warranted by current evidence.
