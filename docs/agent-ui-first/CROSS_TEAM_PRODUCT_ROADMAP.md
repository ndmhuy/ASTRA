# Cross-team roadmap — evidence from bb7f59e

This is a proposed delivery order with observable acceptance criteria, not code implemented by the audit. Owners are team roles; no teammate assignments or external messages were sent.

## Priority 0: dependable current THPT workflow

| Work package | Agent responsibility | UI/UX responsibility | Backend responsibility | Required contract and acceptance |
|---|---|---|---|---|
| Confirmation identity | preserve teacher goal/target; never infer consent from generic model output | store confirmation as specific operation + draft digest; invalidate on target/format/editor changes; support Vietnamese affirmative/cancel | validate resource revision/hash and authenticated owner where deployed | Confirmation: nonce, operation ID, workspace/job/question, params hash, draft hash, expected revision/content hash, creation/expiry. Tests: switch editor/format/job, unrelated yes, đ/diacritics, reload; no wrong target mutation |
| Durable mutation receipts | resume by receipt rather than repeat command | show pending/unknown/committed state and reconcile after network failure | idempotency on regenerate/edit/approve; immutable operation receipt and request fingerprint | same op ID after lost acknowledgement yields same result/usage, no duplicate generation/revision |
| Single vs multiworker policy | explain unavailable state from typed errors | display reconnect/server-restart accurately | immediately document/enforce one worker; then worker leases, CAS updates, task ownership and crash recovery | start two managers while a job runs; no false interruption or lost revision; forced crash recovery fixtures |
| Publication correctness | bind export request to teacher's reviewed artifact | show exact revision/hash; download receipt wording | immutable source/export snapshots; prevent path-streaming race; enforce chosen preview requirement and owner identity | stale revision export rejects; edit racing stream never changes published bytes; unviewed preview approval follows explicit shared policy |
| Multi-tab workspace state | scope active task to originating workspace | storage event/version reconciliation or server workspace store; completed exam refresh | server workspace/job ownership/list/recovery if adopting durable workspaces | simultaneous tabs preserve notes/messages, one active generation invariant, no stale approved export |
| Truthful runtime status | distinguish unsupported, missing binding, unavailable, failed, unknown | show coarse stage vs mock per-item simulation | typed failure/retryability/terminal state; cancellation policy | disconnect/reconnect, poll failures, Backend restart do not falsely claim job failed/cancelled or start duplicates |

Acceptance gate for this milestone: fixture-driven two-tab browser tests and HTTP/DB race tests, then a separately authorized controlled live job. Passing unit tests alone is insufficient.

## Priority 1: finish product workflows

| Work package | Agent | UI/UX | Backend | Acceptance |
|---|---|---|---|---|
| V-ACT integration | recognize current staged state; conversational profile-specific constraints after catalog enables it | use Backend catalog as authority, replace fallback duplication; render shared passages/tables/group IDs and 120 questions | introduce profile dispatcher/typed UI request, adapter to existing vact.Orchestrator, correct RAG/evidence policy, persisted package/revision/preview/export/repair | cost-free 120-item fixture through UI API; group/passage bindings intact; invalid profile rejected; approved PDF/JSON work; enable available only after gate |
| Structured intake | keep confirmed/missing/changeable fields and bounded conversation memory | visible editable draft and summary | authoritative format/profile schema, feasibility validation | paraphrases and changed constraints persist; no repeated known question; no invented matrix; unsupported count explained |
| Note lifecycle | resolve edits/cancel/apply by stable identity and task | review queue, general-note targeting, clear approval/failure/retry UX | decide browser-local vs durable note contract; enforce expected job/question/revision; operation receipts | notes from old exam cannot modify new exam; each approved note applies once; partial batch failure preserves outstanding notes |
| Capability contracts | consume complete parameter schemas and task/receipt summary | one authoritative typed registry with dynamic availability and handler evidence | expose domain prerequisite/permission facts through normal UI services | closed editor not advertised executable; schema drift fails before dispatch; every listed action has a handler and observable result |
| Orchestration recovery | bounded replan from receipts, not blind rebasing; intent change and cancellation semantics | persisted pending operation and scoped state versions; abort UI tasks safely | explicit job cancellation endpoint only if implemented with provider/lease semantics | 5+ actions handled transparently, safe prefix on failure, relevant-state refresh, cancelled task never overwritten by late result |
| Reachable control completion | explain browser-owned actions accurately | new-tab/log and individual disclosures, direct note error handling, accessible confirmations | artifact IDs/URLs with correct owner checks | popup denied/download failed reported truthfully; no claimed click/save without evidence |

V-ACT is not “just set available=true”: current JobManager Request/renderer/package/slots are THPT-specific. Reuse native V-ACT domain classes instead of copying its business rules into Agent or React.

## Priority 2: CUSTOM_RANDOM and measured quality

Follow `CUSTOM_RANDOM_FEASIBILITY.md`. Backend/data owners first supply approved, versioned item inventory and a constrained seeded assembler; UI then exposes source mode/distributions/reproducibility summaries; Agent fills that contract conversationally. AI/hybrid is a later extension after deterministic assembly and eligibility/lineage tests.

Do not set a timeline from code inspection alone. Relative scope: confirmation-language/field-binding fixes are small focused changes; durable operation receipts/multiworker consistency are medium cross-layer work; V-ACT end-to-end adaptation is a separate medium-to-large slice; bank curation/empirical difficulty and generic hybrid exam generation are large data/domain initiatives. Each slice should ship with its own review and acceptance evidence.

## Required shared contracts before expanding autonomy

1. **Format/Profile schema**: version, supported subjects/types, locked/flexible fields, availability reason, template, evidence/retrieval policy, question/group IDs, score rules, export combinations.
2. **Workspace/task schema**: owner, workspace version, task ID/goal, target binding, current step, receipts, pending operation, cancellation epoch and durable/resumable scope.
3. **Mutation/receipt schema**: operation ID, request hash, expected revision/hash, status pending/committed/failed/unknown, result revision/artifact identity, retryability and sanitized errors.
4. **Publication schema**: immutable artifact ID/hash, exam revision, human reviewer identity, policy-specific preview proof, approval time and export provenance.
5. **Question/evidence schema**: stable ID vs display number, shared passage/table/image references, source approval/license/version, difficulty source/confidence, independent solution/review state.
6. **Quality/evaluation schema**: deterministic checks vs semantic judgement, measured vs target values, unresolved flags, teacher edits, latency/calls/tokens and unknown-cost status.

## Realistic acceptance suite

- Every capability category: browser submits a natural-language fixture, validated HTTP response reaches actual handler, DOM/store effect and receipt agree. Separate live-language benchmark must be authorized and labelled.
- UI-only fake success prevented: no handler, wrong params, missing prerequisite, stale target, wrong revision and unsupported product requests all produce accurate errors.
- THPT full fixture: RAG evidence -> 22 correct IDs/types -> generation progress -> review -> edit -> preview -> approval -> exact approved export; mutation invalidates approval.
- V-ACT fixture: 120 ordered IDs, correct passage groups/tables, batched solving, no answers in student view, no accidental THPT rendering/22-item assumptions.
- Concurrency suite: same/different idempotency key, lost POST receipt, two-tab conflicting edits, two workers, restart mid-write, restart mid-model, export vs edit race.
- Note suite: create/update/cancel while generating, reconcile stable IDs on completion, approve/apply sequentially, timeout after commit, old-note/new-exam conflict.
- CUSTOM_RANDOM suite: seeded replay, insufficient pool, incompatible blueprint, no replacement, shuffled key integrity, provenance/review eligibility, immutable bank snapshot.

All roadmap endpoints/contracts above are proposals. Existing routes are listed only in `CURRENT_CAPABILITY_INVENTORY.md`; no unimplemented route is presented as available.
