# Actionable owner handoffs

The atlas describes desired behavior, not existing contracts. Current source evidence is at baseline f9523e9 plus this narrow Agent/UI change.

| Owner / cases | Missing contract and actual evidence | Impact | Minimum negative acceptance |
|---|---|---|---|
| Backend: JOB03/04/14, SAFE05/06 | `ui/storage.py:27` idempotency is global key, not user/workspace; `routes_ui.py` lacks owner authorization | two tabs/devices may submit separate keys; valid UUID is not resource permission | same workspace concurrent requests: one permitted logical job; wrong user cannot read/edit/export |
| Backend: JOB07/08/09/10/12 | `jobs.py:94/100` process-local locks/tasks/semaphore; `storage.py:56` interrupts unfinished jobs on manager init; no event seq/cancel/resume route | UI cannot guarantee order, distributed ownership, provider cancellation or true resume | second manager must not fail live work; terminate/restart; delayed events; timeout with unknown inference result |
| Backend: REV07/08/09/11, SRC13 | full-row save has no CAS; mutation endpoints lack durable idempotent operation receipts | lost revision acknowledgement and multiworker races cannot be repaired by React | same op ID returns same revision after lost response; concurrent same-revision edits have one winner |
| Backend/UI: REV10/12/13/14 | preview cache hashes exist, but export returns mutable path and Backend approval does not require viewed PDF; deleting UI workspace does not cancel server job | UI consent stronger than server authority; artifact streaming/cancel lifecycle gaps | mutate during export; stale approval; unavailable compiler retains ready exam; explicit workspace deletion/cancel semantics |
| Backend/data: SRC01–14, RND01–10, IN04–09/13/14 | `core/models.py` has bank/matrix data validation, but `ui/contracts.py` accepts only THPT and no bank inventory/preflight/random service exists | RAG documents are not approved eligible item families; no feasibility, rights, exposure or seeded bank replay | insufficient unique approved families fails before cost; BANK_ONLY never AI-fills; no automatic bank promotion |
| UI/Agent: NL03/08/11/12 | only compact task and setup draft; no full structured intake/history/navigation contract | arbitrary historical or ambiguous references cannot safely resolve | ambiguous identical workspace labels clarify; reload cannot reuse consent; corrected constraints revalidated |

Bank/random contract to agree (proposal only): approved bank item/version/family IDs, raw import/QA state, rights/owner/share policy, exact/near/family dedup policy, question/passage/testlet grouping, enemy-item restrictions, eligibility-filter snapshot, blueprint deficits per slot, source_mode BANK_ONLY/AI/HYBRID, explicit AI-fill consent/budget, seed+algorithm version, selected content snapshots and model/prompt provenance, revocation policy, item-exposure/overlap limits, provisional vs empirical difficulty, immutable operation receipt and quality metrics.

Do not “enable random” by rebranding the current THPT job, treating RAG theory as a bank, inventing 15 eligible items from 10, or calling Gemini to fill without consent. Current Agent guard refuses these unsupported business paths. All endpoints/schema names above are proposed responsibilities, not routes added by this task.

Teammate-owned wiring touched: App.tsx, state/examSessions.ts, existing executor/tests; changes described in IMPLEMENTATION_REPORT. Business Backend, provider adapter, RAG, domain rules and credentials are untouched.
