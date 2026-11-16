# ADR: Python ports-and-adapters core on the temporary backend baseline

## Decision

Implement a Python package at `exam_baseline.agent`, with Pydantic runtime contracts and no
HTTP route. Use protocols for backend-owned requirements/evaluation and an interface for
optional semantic candidates. Keep UI actions as typed plans/receipts, not React mutations.

## Rationale

- The inspected backend is Python/Pydantic and already defines strict contracts and provider
  infrastructure. This avoids duplicating business rules in TypeScript.
- The live UI branch is separate and its action protocol is proposed, so importing handoff TS
  would imply an integration that does not exist.
- An offline in-process harness makes dialogue, approvals, jobs, and edits testable without
  API keys or unreliable external systems.

## Branch/base tradeoff

The team rule says branches start from `origin/main`, but current main has no runnable backend.
The engineering prompt explicitly identifies `24a2d092` as the temporary generation baseline.
This feature branch starts there and records the exception. No RAG/UI merge is performed.

## Consequences

- Good: reuse packaging/test conventions; zero paid calls; easy backend adapter later.
- Cost: no live UI demo or durable multi-user state.
- Guardrail: fixtures use `mock` in types, user text, demo, and documentation.
- Future adapter work must implement existing ports rather than copying conversation rules.
