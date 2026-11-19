# Input-to-action defects and fixes

Branch: `feat/agent-ui-first-merge`; starting HEAD `6b0f4b92b5f5cae00e9aab4d7a194647200665bc`. Fetched baseline remains `8f12fbb2e9c7b6adb43b20b1966b256da6f45586`.

Verified source defects:

1. Gemini received capability names/descriptions without argument contracts. The React view action requires `params.mode=review`, which was absent from its prompt. Registry-owned `parameterSchema` now reaches the Python request model and Gemini prompt for every callable action.
2. The model context dropped existing exam ID, revision, approval, preview and session identities. These now reach the provider; editor content is limited to the selected draft, and chat context contains message IDs/roles rather than all conversation content.
3. Question focus forced paper mode, undoing answer navigation in dependent plans. Focus now preserves mode; scrolling reruns after a view change.
4. Setup catalog fetching depended on selectedId, while loading cleared selectedId. Real Chrome tests reproduced a stalled task; catalog fetch now runs independently of selection. Opening setup waits up to five seconds for actual catalog readiness before dependent configure actions.
5. Partial plans could read `receipt.status` for a step never executed. Missing receipts no longer crash reporting.
6. The controller rebased returned actions even if the teacher changed UI during interpretation. React now rejects a changed context before dispatch; executor rejects workspace changes during non-navigation actions.

The call path is chat -> AgentClient HTTP -> AgentInterpreter/GeminiPlan -> React task controller -> UiActionExecutor registry validation -> App handler/store/service -> settled state verification -> receipt -> persisted task. HTTP success alone is not counted as UI success.

No live inference or Backend generation was executed for this change. The interpretation-boundary browser fixtures prove React dispatch, not live paraphrase accuracy.
