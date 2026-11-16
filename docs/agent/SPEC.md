# Conversational interaction orchestrator specification

## Purpose and scope

The module helps teachers who prefer natural dialogue or have incomplete requirements. It
collects a teacher-facing draft, explains verified ASTRA capabilities, proposes only enabled
semantic actions, and remains usable while generation is active. It does not create an
`ExamMatrix`, generate/solve/review content, mutate React, or invent live jobs and edits.

## Supported message classes

1. Create/correct an exam request, including Vietnamese without diacritics.
2. Ask for job status from a trusted compact snapshot.
3. Ask about application functions from versioned facts.
4. Request an enabled UI action such as navigation.
5. Make an explicit deferred edit while generation runs.
6. Make an ambiguous difficulty comment, which is not an edit.
7. Chatter, unknown, unsupported, or untrusted content-as-data.

## Requirements and ownership

| Rule | Required behavior | Owner | Evidence/test |
|---|---|---|---|
| R01 | Classify help/task/status/edit/remark/noise independently during a job | Agent | `test_orchestrator.py`, `test_jobs.py` |
| R02 | Descriptor drives grouped missing fields; presets need acceptance | Backend descriptor + Agent dialogue | `test_requirements.py`, IN01-IN10 tests |
| R03 | One active job per workspace, chat stays available | Backend later; Agent/mock gate now | `test_second_generation_in_active_workspace_is_blocked` |
| R04 | Queue target-bound changes without mutating the run | Agent ledger; Backend applies later | JOB04-JOB12 tests |
| R05 | Plan only enabled typed capabilities and wait for receipts | UI executor + Agent planner | `test_capabilities.py` |
| R06 | Status is snapshot-grounded; UI renders backend events | Backend/UI | mock status test; live integration blocked |
| R07 | Product answers disclose implemented/mock/proposed state | Team docs + Agent provider | app-help test |
| R08 | Offline baseline; model output could only be a candidate | Agent | no network/key dependency; interface only |

## Generation-time invariants

- The running request is immutable.
- Conversation, workspace, job, exam, question, and revision IDs are distinct.
- A second generation is not started or auto-queued in the same workspace.
- “Câu 3 khó quá” does not create a pending change.
- “Sửa câu 3 dễ hơn” needs a trusted display-index mapping; `3` is never guessed as ID.
- Completion without a final package produces no revision proposal.
- A proposal is never marked applied without a registered edit receipt.

## Nonfunctional requirements

- Pydantic validation with `extra="forbid"` at contracts.
- 10,000-character turn limit and at most five actions per plan.
- Stable request/action/idempotency keys and in-process replay deduplication.
- No secret values in state or trace; no raw file paths/objects in turns.
- Python 3.10+; no paid model, browser, or network required.

## Explicit limitations

State is in memory and is lost on process restart. There is no authentication, durable action
ledger, backend converter, live job stream, real UI executor, or edit API. All Phase 1 external
effects are marked mock.
