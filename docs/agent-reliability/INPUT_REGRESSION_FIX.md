# Fix ordinary exam requests after PR36

For the owner and reviewer. Branch `fix/longlth2297/agent-exam-request-intake` starts at actual `origin/main` **2119becda1b0ba3289449e5b2f1d3b179b5ff423**, which includes merged PR36. Existing worktrees, runtimes and jobs are preserved. No real inference or exam generation is used for this fix.

## Observed causes

- “soạn đề tiếng anh THPT cho tao” did not match the local catalog grammar. The semantic resolver rejects every multi-goal frame containing intake/guidance, including compatible preparation and generation goals for one exam. That condition produces the first reported message. The actual remote frame was not captured/replayed through Gemini; deterministic compatible frames reproduce the rejection.
- “tạo đề toán thpt mới” was not recognized as a fresh-workspace request. The execution adapter requires a draft/error workspace for format setup, so it rejects a completed/running workspace before preparing the requested new exam. A paused workspace has another preservation guard with the same practical obstruction.
- Both displayed rejection conditions already exist at98b1df5, before the pause/resume changes. This does not prove live interpretation never regressed; it establishes the source of these messages. The previous local dataset did not cover ordinary full creation sentences combined with completed/running workspace transitions. Its high fixture conformance was insufficient evidence of end-to-end usability.

## Changes

- Recognize creation structure from verbs, courtesy markers, optional “new/another”, family vocabulary and actual catalog subjects. Preserve unfamiliar topics/count/time requirements for the existing interpreter; do not silently discard them or infer a Math default for English. The word “mới” inside a stated topic such as “Đổi mới” is not a new-workspace instruction.
- Coalesce compatible preparation/configuration/generation goals into one intake while retaining every slot. Conflicting subjects/counts/families, unrelated business actions, references, negation, conditionals, questions and no-generation constraints retain their guards. No Worker schema or prompt change is required.
- Before binding a creation turn, use a fresh workspace for a completed exam or an explicit new-exam request on an existing workspace. Bind its transcript, confirmation and format selection to the new ID. Retain old exam/checkpoint/transcript; normal composer draft/revision saves still occur. Do not start inference or call resume/cancel as part of this transition.
- Backend generation, validators, credentials, Cloudflare/model configuration and pause/resume implementation are unchanged.

## Verification and owner test

- Frontend75 tests, production build and lint pass. Focused tests cover the reported inputs, other subjects/word orders, topics preserved for interpretation, compatible/conflicting semantic composition and target-state selection.
- `python scripts/agent_exam_request_smoke.py` mounts the actual compiled React app against the existing no-inference test server. Ten browser cases cover draft/completed/paused/running/failed states, both reported inputs, compatible/conflicting simulated model frames, negation and questions. Model and business responses are explicit fixtures; external fonts are suppressed; generation endpoints are forbidden. Real inference0, generated exams0.
- Existing semantic oracle harness passes153 frames,21 workflows/28 turns and23 adversarial cases; model metrics remain null. No new LLM accuracy claim is made.
- New test script passes Ruff check/format. Required common verify still stops on the89 previously recorded baseline diagnostics; none of those files is changed here.
- Fixed local UI is served at **http://localhost:5174**, proxying to the existing actual Backend8002. The original8002 tab remains open. Native Chrome observation confirmed the fixed start screen and existing shared library. The first reported sentence is prefilled, **not submitted**; no actual Chat or generation request was sent by the agent.

Owner: submit the prefilled English request and check the40-question/50-minute English preset. From an existing completed/running/paused/failed workspace, request a new Math exam and verify a separate draft opens while the old job remains. Only press the generation confirmation when personally ready to use Gemini.

Non-inference status inspection also found the owner's current failed Composer job has native `invalid_contract` errors (undelimited mathematics in solutions and a missing short-answer rounding instruction). That output-quality failure is separate from the two Agent/UI rejections. This patch does not relax academic validators or claim that live generation failure has been fixed; no retry was initiated.
