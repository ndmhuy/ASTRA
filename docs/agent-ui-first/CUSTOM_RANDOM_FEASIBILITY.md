# CUSTOM_RANDOM feasibility — audit/design only

At audited SHA `bb7f59e`, CUSTOM_RANDOM is **MISSING as a format, route, UI workflow and persisted exam mode**. React `ExamType.CUSTOM` is only a broad type value (`types/exam.ts:3`); it does not establish a working generation path. UI GenerateRequest only permits THPT (`ui/contracts.py:18`). No random assembler, bank CRUD/versioning or reproducibility manifest was found in mounted application services.

## Reusable source, with limits

- `core/models.py:65` ExamMatrix validates totals, topics, type/difficulty distribution, points and duration; `QuestionBank/:152`, `BankQuestion/:145`, `GenerationRequest/:194` support input banks and generic constraints.
- `core/validation.py:39` validates generated shape/counts/distributions, duplicate IDs/stems, source references and faithful bank reuse (`:186`). It explicitly does **not** certify semantic correctness or difficulty (`:208`).
- `/v1/exams/generate` is one model call with strict parse, not a deterministic bank selector (`baseline/agent.py:27`). `/v2/exams/generate` provides a generic four-role pipeline, not the current UI job manager's THPT-specific persistence/package contract.
- Existing RAG retrieves observations/examples/curriculum context; it is not automatically an approved question bank with teacher-approved reusable items, calibrated difficulty, licensing and selection eligibility.
- `Settings.seed` can be sent as a provider option (`config.py:31`, `providers/chat_completions.py:36`). That does not create deterministic bank sampling, and does not guarantee byte-identical LLM output.

## Three possible implementations

| Strategy | Feasibility from current source | New Backend responsibilities | Quality/reproducibility consequence |
|---|---|---|---|
| Bank assembly | Best initial candidate **if** curated approved items exist; current storage/selector MISSING | versioned bank records, eligibility filter, deterministic constrained selection, insufficient-pool errors, item/option permutations with answer remapping | Can replay exact output from bank snapshot + algorithm + seed + selection manifest; no AI call required |
| AI generation | Generic matrix/schema/roles reusable; UI adapter and arbitrary-format renderer MISSING | generalize format dispatch without weakening THPT/V-ACT contracts; declared topic/score/time constraints; generation budget and quality gates | Seed alone insufficient; store exact accepted question/artifact snapshot, prompt/model/provider/versions and reported usage |
| Hybrid | Feasible after bank mode; highest integration complexity | allocate reused/new slots, preserve source_question_id lineage, dedup both sets, use remaining blueprint quotas, budget only novel slots | Manifest must identify assembly vs generated provenance and independent validation for each item |

Recommended sequencing is an **engineering inference**, not an implemented decision: begin with bank assembly for one supported subject/type after data owners supply approved items; then AI fill for uncovered slots. A fully generic “random exam in any subject” is a separate larger scope.

## Proposed versioned contract (not an existing API)

Agree a format-neutral `ExamCreationRequest` with schema_version, format_profile=CUSTOM_RANDOM, subject/curriculum version, language, exact item count, type mix, points policy, duration, topic/objective distribution, difficulty policy, source_mode, bank snapshot, algorithm_version, seed, replacement policy, duplicate/exposure constraints, question/option shuffle flags and teacher instructions.

Do not put educational rules in Agent code. Backend must reject infeasible combinations deterministically before model calls or selection. Examples: total counts disagree, mixed subjects without blueprint, not enough eligible distinct items, unsupported response type, incompatible points, shared-passage group split, required diagrams absent, zero remaining token/cost budget.

Persist an immutable `AssemblyManifest`: request hash; bank release/content hashes; accepted item versions; ordered stable IDs; generator/selector versions; random seed and PRNG algorithm; choice permutations and remapped keys; prompt and model provenance for generated items; source licensing/approval; resulting exam revision/content/artifact hashes. Replay from this manifest, not from current mutable bank state.

## Difficulty and quality evidence

- Keep cognitive level and difficulty separate. Store difficulty **source** (author judgement, model estimate, pilot estimate, empirical response data), scale/version, confidence and review status.
- Do not advertise current NB/TH/VD/VDC or easy/medium/hard labels as calibrated difficulty.
- Minimum deterministic checks: exact blueprint/score totals; unique item/version/stem; eligible source; no broken passage groups; correct option mapping after shuffle; finite valid numeric answers; rendered text/TikZ hygiene; complete answer-key bindings.
- Independent solving/review is an additional signal, not proof. Require teacher acceptance and flagged-item workflow.
- Measure blueprint satisfaction, duplicate rate, bank reuse fraction, answer disagreement, unresolved flags, teacher correction time, render/export success, elapsed time, calls/tokens and unknown-usage share. Empirical item difficulty/discrimination need student-response data and an explicit collection/privacy process, which is absent.

## Responsibilities and acceptance

Backend/domain: own schema/validation, assembly, immutable bank versions, seeded randomization, rendering, mutation/publication and metrics. UI/UX: expose source mode and supported constraints, show feasibility/quality/provenance summary, explicit confirmation, reproducible exam history. Agent: conversationally fill only schema-approved fields, explain infeasibility, request grouped missing constraints and dispatch existing React handlers.

Acceptance tests: identical seed+snapshot+algorithm produces identical IDs/order/keys/artifact hash; changing seed yields another valid assembly when feasible; no-replacement never duplicates; insufficient bank fails before inference; option shuffling preserves correct answers; shared passages stay atomic; generated fill cannot change preserved bank content; stale bank hash is rejected; unsupported mix never silently degrades; teacher approval remains bound to final revision/hash.

No feature or endpoint was added by this audit.
