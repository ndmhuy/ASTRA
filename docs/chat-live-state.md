# Chat grounding and live workspace state

For reviewers of the local Chat reliability change. Real model quality remains
for the owner to evaluate through the UI; the agent performs no real inference.

## Observed problems

Form-created exams had submitted parameters and Backend metadata but often no
Chat intake. The Chat context and requirement-recall handler relied on intake,
so they could miss the actual subject, count and duration. Status replies reported
progress without identifying the exam. The interpreter only returned routing
meaning and could not carry an ordinary conversational reply. A malformed model
interpretation also cooled down later unrelated turns for twenty seconds.

## State and interpretation

The Backend builds one versioned, read-only projection from persisted workspaces
and jobs. `/agent/workspace-state` serves it to the local UI; the same projection
is injected into V3 Chat context after admission and before interpretation. The
projection contains the selected workspace, up to five background active jobs,
actual submitted subject/count/time, saved progress, errors and artifact approval.
It does not start/resume jobs or mark them complete, and does not send question
bodies, answer keys, executable IDs or credentials to the interpreter.

The client-message fingerprint is calculated before hydration, preserving replay
semantics as job progress changes. A new turn receives a fresh observation. UI
status reads prefer the Backend projection over stale browser state; legacy or
browser-only job links can still read their actual job status. Drafts, artifacts,
messages and inference checkpoints retain their existing owners.

The local Claude interpreter now supplies per-goal tool variants instead of the
compact union of every parameter. This prevents the schema from advertising
another goal's slots for a selected goal. Invalid goals/parameters remain rejected.
Safe validation diagnostics retain field/type metadata without raw replies or
prompt text. A schema error neither triggers an extra paid repair call nor cools
down the next independent user turn. Authentication/quota controls remain.

V3 additionally permits a bounded conversational `reply`. It is text, never a
command or proof of execution. Read goals still produce receipts from actual
state. Statements such as “đề này đã soạn xong rồi” read the job's status rather
than approving, generating or changing its lifecycle. New clients opt in with
`X-Astra-Dialogue: grounded-v1`; strict older V3 clients do not receive new reply
or status-scope fields. Unknown or malformed meaning does not become an action.
The UI shows the interpretation failure together with current verified state.

Chat context and requirement recall also include form parameters and job metadata
when intake is absent. Status replies identify the subject, family, requested
count/time and saved progress, and distinguish completion from teacher approval.
Academic generation prompts, validators, model choice and shared key are unchanged.

## Verification

- 612 offline Python tests and 7 subtests passed with external socket connections
  blocked; 96 frontend tests, frontend build/lint and changed Python Ruff passed.
- Mounted Chat tests used a fenced fake Anthropic provider and synthetic job
  metadata, generating no exams. Seven flows cover form-based recall, current and
  active status, completion statements, ordinary discussion, stale browser state,
  a malformed interpretation and an immediately successful subsequent turn.
- Synthetic credential-repair coverage passed on desktop/mobile. The existing
  mounted capability adapter coverage also passed without upstream inference.
- The existing repository-wide verifier remains blocked by its previously
  recorded 89 lint errors outside this task. No push, PR or deployment is included.

These are boundary/state/workflow observations, not measured live-model accuracy.
The owner should refresh the real app and exercise natural requests manually.
