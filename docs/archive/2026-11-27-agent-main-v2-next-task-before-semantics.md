# Resume after Gemini application-contract failure

Continue on feat/longlth2297/agent-main-v2 in the existing feature worktree. Fetch origin, inspect HEAD and preserve local files. The correction checkpoint is d588368, followed by documentation commits.

## Current deployment

Worker astra-ai-proxy runs version bb165c28-5a06-4372-9c9e-b2bf758b9599 with forwarding disabled. Model remains gemini-3.1-flash-lite. Global and Agent daily ceilings are two for the completed diagnostic allowance, preserving both consumed attempts. Remaining allowance is zero. ADMISSION, global-v1 and migration v1-admission remain unchanged.

Local ASTRA runs at http://127.0.0.1:8000 with synchronized Worker contract, no distributed credential requirement, fallback disabled and demo MAS. Its current process was restarted after the final contract export.

## Latest real evidence

The owner authorized exactly one additional attempt. It was entered once in a fresh real chat.

> Cô muốn tạo một đề thi thử tốt nghiệp.

- Local turn 0a3ee1db-6a10-45ca-a04e-50dd655ab6d8.
- Worker request 6a66b6fb-b5bc-41ce-84cf-147bd3cc4dc2.
- Admission true, upstream attempt count one, HTTP 200, model gemini-3.1-flash-lite.
- One candidate, STOP, application/json, complete parsed JSON, one final text part and 158 text bytes.
- Prompt tokens 2373, output tokens 70, total 2443. Thought tokens were not reported.
- Provider elapsed 2042 ms, Worker elapsed 2228 ms, browser interpretation 2897 ms, visible response 2955.7 ms.
- Both structural validators passed, then application_contract rejected semantic_invariant.
- Local HTTP 200 carried temporarily_unavailable/schema. The UI displayed “Kết quả từ AI chưa đọc được. Thầy cô có thể gửi một yêu cầu ngắn, ví dụ ‘Chọn V-ACT’.”
- Exactly one Agent request and zero business/exam-generation writes. No accepted THPT intake or subject question.

The first historical turn's exact payload remains unavailable. The second trace establishes a cross-field consistency failure. It did not retain the subtype among the formerly combined invariant checks, so do not invent the model's exact conflicting fields.

## Correction completed offline

The provider schema had allowed combinations forbidden by the application. It now defines exclusive action, intake, guidance and plain non-action alternatives. Actions require a nonempty list; other alternatives have an omitted or empty list. Intake and guidance are exclusive and cannot have task kind. The full internal 34-intent schema and compiler still validate the normalized result.

The final provider schema is 3832 serialized bytes versus 11014 for the full internal schema. Optional null fields normalize to omission. Required fields, per-intent argument types/enums and all existing UI confirmation/freshness checks remain enforced. Explicit MINIMAL thinking is documented for this model. Output limit stays 1024.

Sixteen local workerd groups passed, including all 34 intent contracts, the observed cross-field failure class, blocked/empty/thinking/multipart/truncated outputs, invalid values, HTTP errors and timeout. Twenty-three focused Python checks passed. Contract fingerprints are regenerated from the same authoritative source. Logs now distinguish exact invariant categories and safe shape flags without prompt content. The correction is deployed disabled, and its live success remains unverified.

## Next authorization boundary

1. Review ignored runs/live-worker-two/result.json, tail.private.json and actual-response.png.
2. Obtain new authorization for another diagnostic inference and one additional persisted allowance. Both previous authorizations are consumed. Leave forwarding disabled until then.
3. With approval, read quota and increase only the approved ceiling. Preserve counters and UTC semantics. Do not reset storage. Submit one real UI turn and disable forwarding afterward.
4. Capture complete stage metadata and actual UI behavior. Success requires accepted THPT intake and a subject question, with zero generation requests.
5. If it fails, fix the observed defect offline and stop before another inference request.
6. Multi-turn manual acceptance and future fallback need their own approved budget. Public MAS inference remains absent pending academic provider compatibility.

WORKER_RUNBOOK.md records the native Gemini schema audit and future fallback evaluation. No automatic fallback was implemented.
