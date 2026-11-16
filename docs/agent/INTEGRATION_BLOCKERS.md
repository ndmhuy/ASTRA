# Agent integration blockers

| Blocker | Owner | Verified state | Phase 1 fallback |
|---|---|---|---|
| Authoritative teacher requirements and presets | Backend | Not implemented | `FixtureRequirementsProvider`, labeled fictional/mock |
| Draft to `ExamMatrix` conversion and semantic validation | Backend | Not implemented | `MockDraftEvaluationPort`; never authorizes real generation |
| Trusted approval service and actor binding | Backend + UI | Proposed only | Typed `TrustedApproval` supplied directly by test/demo adapter |
| Idempotent async generation start and lookup | Backend | `/v2` is synchronous | `MockJobManager` with deterministic idempotency key |
| Job snapshot/events/final-package contract | Backend + UI | Not implemented; UI progress is mock | Compact mock snapshot, manually advanced in tests/demo |
| Runtime screen-context exporter and capability executor | UI | Proposed only | Registry defaults disabled; isolated mock navigation executor |
| Display index to stable question ID bridge | UI + Backend | Not implemented | Accept explicit test mapping; otherwise `needs_target` |
| Deferred revision batch API | Backend | Not implemented | Consolidated proposal only; `applied=false` |
| Authentication, permissions, retention, multi-process persistence | Backend/Infra | Not found | In-memory single-process limitation documented |
| Shared UI + backend + Agent source branch | Tech lead | Integration branch created; functional wiring absent | Keep ports independent until reviewed contracts are implemented |

None of these blockers prevents the offline core. They prevent any claim that the chatbot is
integrated with production ASTRA.
