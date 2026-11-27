# ASTRA Agent V2 product intelligence refinement

For product and engineering reviewers. Work continues on `feat/longlth2297/agent-main-v2` from `7e63bd1`. The latest fetched main remained at `7523c79`.

## Observed causes

The earlier authorized Codex turn reached the real CLI and failed when the upstream service rejected the strict output schema. The adopted correction makes optional fields required and nullable for Codex and keeps application validation. The prior running process later logged two real manual responses parsed successfully, one OPEN_SETUP and one clarification. The log records decisions but omits teacher prompts, so the exact sentences cannot be identified. Live acceptance of the expanded response schema is still pending. Separately, source inspection showed that the model's `answer` was reduced to a generic clarification, intake required a selected format ID, context omitted assistant questions, and automatic title behavior copied the first recognized message.

## Product behavior

- The shared vocabulary maps exam-family expressions and common subject aliases. The live format catalog supplies runnable families, subjects, locked fields, format versions, sections and prerequisites. Current THPT supports Mathematics. Current V-ACT supplies the full competency assessment with five catalog sections. ASTRA has no custom or random generation contract at this checkpoint.
- The provider may return a bounded intake proposal, a guidance category and a title suggestion in the same turn. React resolves proposals against the current catalog. Missing data produces clarification. Catalog checks prevent unsupported-subject substitution and reject conflicting locked counts, durations or grades. Structure and capability answers give current catalog facts through a read-only path.
- The browser saves partial intake, confirmed choices and topic requirements in the existing conversation store. Facts reference their source messages. Retraction and branching discard facts whose sources no longer exist. Recent assistant questions and selected older user messages are bounded and scrubbed before interpretation. A correction clears pending generation confirmation, while the existing topic and format evaluation path controls whether a new one can be prepared.
- Automatic names summarize guidance or the selected academic objective. Topic titles can refine the name within the first three meaningful user messages. Manual and legacy titles take precedence. The official exam title remains on the exam package. A branch inherits title provenance when its source remains available.
- The shared compiler still uses 34 intent IDs. Intake selects or prepares existing setup actions, and application guidance prepares no action. The binding and cancellation checks fence stale model responses. The existing evaluation endpoint and explicit confirmation gates govern generation.

## Limits

Semantic accuracy depends on the selected provider and remains a manual acceptance item. Retraction conservatively discards the saved intake if it loses a supporting message. Remaining transcript context lets a later turn collect it again. Catalog availability describes supported presets. Evaluation, RAG and model availability determine whether a particular request can proceed. Codex and gateway account acceptance both require a live result. [Manual acceptance](MANUAL_ACCEPTANCE_V2.md) · [Gateway setup](CLOUDFLARE_GATEWAY_SETUP.md)
