# ASTRA — UI/UX ↔ Conversational Interaction Orchestrator Handoff

**Purpose:** Working document to align the UI/UX team with the developer of ASTRA's Context-Aware Conversational Agent & Interaction Orchestrator.  
**Status:** `REQUEST FOR REVIEW` — proposals and examples are **not** approved interfaces.  
**Prepared:** 2026-11-13  
**Please reply by editing this document or by creating `UIUX_HANDOFF_RESPONSE.md` with the same headings.**

> **Short version to send:** I am building the conversational layer that understands user requests, asks follow-up questions using the **backend module's required input schema**, and generates **validated actions** for the UI/backend. I am **not** asking UI/UX to determine what information is required to generate an exam or to parse the user's request. I need your real UI component/state/action contracts so we can integrate without coupling the agent to React components or DOM selectors. Please mark what is already implemented versus proposed, and give me real paths and examples.

---

## 1. Shared understanding: what my module does / does not do

### My module owns

1. Interpret the teacher's natural-language intent (`create_exam`, `open_feature`, `explain_feature`, `focus_question`, etc.).
2. Merge the current message with **conversation memory** for the current session.
3. Compare collected parameters with **backend-provided requirements**; ask clarifying questions for missing, ambiguous, or invalid inputs.
4. Read a **structured UI context** and a registry of actions the application can perform.
5. Produce a **structured, allowlisted action plan**; validate action type, target, parameters, permissions and relevant UI state **before dispatch**.
6. Receive an execution acknowledgement/updated state, and then respond accurately to the teacher.
7. Route well-formed requests to the backend module adapter; track job state at a high level.

### UI/UX owns

- React UI, navigation and actual component behavior, chat message rendering, form rendering if a form is used, focus/highlight/animation, LiveCanvas display, handling UI events and local session/UI state.
- **Implementing the UI action executor**; my module never directly manipulates DOM/CSS or calls `setState` from outside React.
- Subscribing to backend progress/stream events and rendering draft/verified question states. There is **no need to send every generated token/event through an LLM**.

### Backend owns

- Mandatory exam input fields, field constraints/defaults and semantic validation; uploaded file processing; exam generation, RAG, solving, review, export; job status and content/progress events.

**Crucial distinction:** UI state describes **what is visible/selected/available right now**. Backend schema describes **what information is required**. The agent asks the missing questions; this is conversational slot filling, **not form-field completion detection**.

---

## 2. Expected initial end-to-end user story

**Scenario A — teacher makes an incomplete request**

1. Teacher writes: “Tạo đề Toán 12.”
2. Chat UI sends `{ message, sessionId, screenContext }` to the conversational service.
3. Agent recognizes `exam.generate`, extracts subject/grade, consults the backend's registered schema, and finds required information missing.
4. Agent returns a **clarification message** (e.g. “Bạn muốn bao nhiêu câu?”); UI simply displays it and sends the teacher's next reply with the same session ID.
5. After collecting the remaining required data, the agent presents a summary and asks for user confirmation where appropriate.
6. Agent produces `NAVIGATE`/`OPEN_PANEL` actions if needed, then triggers **one** backend generation job through the agreed owner. UI shows the updated view.
7. Backend emits progress/questions; UI streams updates to LiveCanvas, clearly distinguishing `DRAFT`, `VERIFIED`, and `FLAGGED` when supported.
8. Agent can answer “Đã xong đến đâu?” using job state, and never claims success before an execution result confirms it.

**Scenario B — context-dependent UI action**

Teacher asks: “Giải thích cái này” or “Tô sáng câu này”. Agent checks `selectedQuestionId`/`focusedComponentId`. If missing or stale, it **asks which item** rather than guessing.

**Scenario C — unsupported action**

Teacher asks the chatbot to perform an action not registered or currently unavailable. The agent explains the limitation, returns no unsafe action, and optionally suggests a supported alternative.

---

## 3. Please fill this inventory with **current code**, not only planned UI

**Response rule:** For each item, specify `IMPLEMENTED`, `PARTIAL`, `PROPOSED`, or `NOT AVAILABLE`, plus path to the actual branch/file and a small example. Avoid assuming earlier design docs reflect the current branch.

| Item | Questions for UI/UX | UI/UX response / source path / status |
|---|---|---|
| Repository & version | Branch, commit SHA, instructions to run, entry point? | `TODO` |
| Pages/screens | Stable screen IDs and navigation route/state transitions? | `TODO` |
| Chat component | Where is the message submit handler? Can we insert an agent service adapter? | `TODO` |
| Chat session | Who creates/stores `sessionId`; can chat continue across turns/navigation? | `TODO` |
| Screen context | Where can we read current screen, selected question, active exam/session, panels and available actions? | `TODO` |
| UI capabilities | List supported actions, target IDs, input parameters and preconditions. | `TODO` |
| UI action executor | Where can an adapter implement `execute(action)` and return result? | `TODO` |
| UI feedback | Can each action report success/error plus updated context and version? | `TODO` |
| Confirmation UI | How can teacher approve/cancel a generation request? | `TODO` |
| Progress/canvas | How does UI subscribe to job progress and append/update question items? | `TODO` |
| Error/loading/disabled states | What happens while an action/job runs or a screen changes? | `TODO` |
| File uploads | What upload component exists? Does it return a backend-owned `fileId` or reference? | `TODO` |
| Existing tests | Which tests cover chat, navigation, sessions and progress? | `TODO` |

**Files to check if the `uiux` snapshot still resembles the version previously reviewed:**
- `astra-frontend/src/App.tsx`
- `astra-frontend/src/state/examSessions.ts`
- `astra-frontend/src/services/examService.ts`
- `astra-frontend/src/types/exam.ts`
- `astra-frontend/src/components/Workspace/ChatPane/ModernChatBar.tsx`
- `astra-frontend/src/components/Workspace/LiveCanvas/ExamPaperView.tsx`

These are **historical paths from an earlier branch snapshot**, not guaranteed current code. Please correct them.

---

## 4. Proposed UI → Agent contract (for discussion)

Every chat turn should carry **text + stable session identity + structured UI context**. UI does **not** have to send all displayed exam text or raw DOM.

```json
{
  "schemaVersion": "0.1",
  "requestId": "req-001",
  "sessionId": "chat-session-01",
  "message": "Tạo đề Toán lớp 12",
  "screenContext": {
    "screenId": "workspace",
    "activeExamId": null,
    "selectedQuestionId": null,
    "focusedComponentId": null,
    "availableActions": ["navigate.workspace", "exam.open_setup", "question.highlight"],
    "stateVersion": 12
  }
}
```

### Please confirm or change

- Which fields are available from React state today?
- Can you give stable screen IDs, target/component IDs **instead of CSS selectors**?
- Can we send only an **allowlisted, small snapshot** of UI state to the model?
- How is an active session/current selected item identified?
- Where should UI context be refreshed after an action/navigation?

**Important:** The agent's **collected exam requirements** are stored in its own conversation state and validated using the **backend schema**. They should not be inferred from form values. A form is optional as a confirmation/editing view.

---

## 5. Proposed Agent → UI action contract (for discussion)

**Example action plan** (this is an illustrative interface, not a directive to implement these exact names):

```json
{
  "schemaVersion": "0.1",
  "planId": "plan-001",
  "sessionId": "chat-session-01",
  "reply": "Tôi đã hiểu yêu cầu. Mình sẽ mở khu vực soạn đề để xác nhận trước khi tạo.",
  "actions": [
    {"id": "a1", "capabilityId": "navigate.workspace", "target": "workspace", "params": {}},
    {"id": "a2", "capabilityId": "exam.open_setup", "target": "exam-setup", "params": {}}
  ],
  "requiresUserConfirmation": false
}
```

**Example execution result:**

```json
{
  "planId": "plan-001",
  "actionId": "a1",
  "status": "success",
  "updatedScreenContext": {
    "screenId": "workspace",
    "stateVersion": 13
  },
  "error": null
}
```

If action fails, return `status: "failed"` with a **stable error code** and **do not falsely acknowledge completion**.

### Minimum UI capabilities to discuss for MVP

| Capability ID (suggested) | Semantics | Parameters | Preconditions / failure |
|---|---|---|---|
| `navigate.workspace` | Open main exam workspace | none or `sessionId` | User/session availability |
| `exam.open_setup` | Open setup/confirmation view | optional `draftRequestId` | Setup supported |
| `question.highlight` | Highlight specific exam question | `questionId` | Question exists in current exam |
| `question.open_editor` | Open editor for a selected question | `questionId` | Exam and question exist |
| `panel.open` | Open a known panel | `panelId` | Panel registered and enabled |

**No generic arbitrary script execution or DOM selector instructions.** New UI features register a semantic capability with typed parameters and an executor implementation. This avoids recoding the intent parser whenever a new button appears.

---

## 6. Capability registration format — UI/UX contribution

Please describe each available UI action with **what it means** rather than only its component implementation.

```json
{
  "capabilityId": "question.highlight",
  "owner": "ui",
  "description": "Emphasize a specified question in the active exam canvas",
  "parameterSchema": {
    "type": "object",
    "properties": {"questionId": {"type": "integer", "minimum": 1}},
    "required": ["questionId"],
    "additionalProperties": false
  },
  "preconditions": ["workspace_active", "question_exists"],
  "confirmation": "none"
}
```

**MVP recommendation:** A **static, versioned registry loaded at startup** is fine. We do not need a complex distributed plugin marketplace or automatic runtime registration at this stage. Make it easy to add new capabilities later.

### UI/UX should provide one of the following

- A JSON/TypeScript list of available capabilities, with their parameter schemas.
- An adapter that exposes UI actions as `execute(action): Promise<ExecutionResult>`.
- Or a proposal for an alternative interface together with a working example.

---

## 7. Progress events and division of responsibility

Backend job events should normally go **directly to the UI's progress consumer** (e.g. an SSE listener). UI renders:

- Job stage/progress; question content once available; draft vs verified vs flagged; failure and cancellation.
- Any movement/highlight the agent requests **only after valid action execution**.

Agent receives a compact job status (when necessary to answer a follow-up), **not** every generated token. UI/UX and backend must jointly agree on event names, payload, ordering and reconnect/retry semantics.

**Please tell me** whether `examService.onProgress` and the session state already support real streamed jobs or only a mock. Provide the current event payload and a screenshot/small test if available.

---

## 8. Questions we need to settle together (reply inline)

| Decision | Options / expected answer | Decision owner | Current answer |
|---|---|---|---|
| Source of truth for screen state | React store / session store / router | UI/UX | `TBD` |
| Where the UI executor lives | React hook / provider / service adapter | UI/UX | `TBD` |
| How chat calls the agent | REST / server streaming / existing service | UI + agent | `TBD` |
| Required exam inputs | **Backend schema, not UI form** | Backend | `TBD` |
| Who starts a generation job | One designated caller (avoid duplicate jobs) | Backend + UI + agent | `TBD` |
| Who renders job progress | UI from backend events | UI + backend | `TBD` |
| How errors are presented | Agent reply + UI error state | UI + agent | `TBD` |
| Confirmation and cancel | Who owns prompts/button actions and result | UI + agent + backend | `TBD` |

---

## 9. Concrete handoff requested from UI/UX

Please return these **four things** (minimal viable response is fine):

1. **`UIUX_IMPLEMENTATION_STATUS.md`**: what currently works / mocked / planned; branch+commit; precise file paths; how to run and test.
2. **`ui_capabilities.json`** (or TS equivalent): screen/action IDs, descriptions, typed params, availability and preconditions. Start with 3–5 essential actions.
3. **One current `screenContext` example** and one **actual UI action execution example** or proposed adapter signature.
4. **Progress information**: existing chat handoff and canvas progress mechanism, actual/mocked status, and relevant code paths.

If team bandwidth is limited, fill Sections **3, 4, 5 and 8** of this document instead of creating additional files. Mark every item `IMPLEMENTED / PARTIAL / PROPOSED / NOT AVAILABLE`, so we can proceed with mocks for anything not yet ready.

---

## 10. My commitments back to UI/UX

I will provide:

- A versioned `AgentTurnRequest`/`AgentTurnResponse` contract and examples.
- A validated semantic `ActionPlan`, a capability registry interface and a dispatch adapter.
- Conversational clarification responses and state continuity across turns.
- Tests for intent parsing, backend-schema-driven missing-field questions, context-dependent actions, invalid capabilities and execution feedback.
- A mock UI executor and integration instructions; I will **not** overwrite the UI team's components without an agreed integration task/PR.

**Success for the first integration:** teacher can write an incomplete exam request, answer follow-up questions, confirm the completed request, see the UI navigate/open setup, and (with a real or clearly labeled mock backend adapter) initiate **one** generation job. UI progress remains UI/backend-owned.

**Please reply with the filled handoff and any objections to the proposed contracts; after that we can freeze a small `v0.1` interface and integrate through a PR.**
