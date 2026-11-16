# UI ↔ Agent delivery for UI/UX review

Connection recovery follow-up: see `docs/agent/CONNECTION_RECOVERY_REPORT.md`.
`npm run dev` now starts both processes. Automated headless Chrome E2E is now available
via `npm run test:browser`; four real UI/Agent cases pass. Earlier limitations and results
below describe the initial delivery, before this follow-up.

Status: implemented on `feat/longlth2297/m2-ui-agent-orchestration`; not merged into the
teammate-owned `uiux` branch. Base commit: `afdbcd6` from
`feat/longlth2297/agent-ui-integration`.

## What this change does

The chat message is no longer answered by a canned UI string. The UI sends one versioned turn to
the standalone Agent, validates the response at runtime, executes an allowlisted semantic UI
action, reports an observed receipt, and only then stores the Agent's final acknowledgement in the
originating workspace conversation.

Implemented local-only capabilities:

| Capability | Existing UI function reused | Observed receipt |
|---|---|---|
| `ui.navigate` | updates `homeTab`, `screen`, and optional `activeId` | committed screen/workspace |
| `ui.session.create` | `ExamSessions.create(mode)` | real new workspace ID and mode |
| `ui.exam.open_setup` | selects workspace and opens `QuickPresetModal` | target workspace and visible dialog |
| `ui.sidebar.set_collapsed` | sets existing sidebar state | effective requested boolean |

These actions do not invoke generation, `/v2`, export, question editing, or any paid model. The
existing `examService` generation flow is unchanged.

## Files and ownership impact

- New adapter layer: `src/integration/agentProtocol.ts`, `uiExecutor.ts`,
  `agentController.ts`, and `src/services/agentService.ts`.
- Minimal host wiring in `src/App.tsx`: exports current semantic state, registers handlers, and
  routes chat messages through the controller. Existing layout, components, styling, and visual
  identity were not redesigned.
- `src/state/examSessions.ts`: splits user/assistant append operations and Agent pending/error from
  generation state. `sendMessage` remains as a compatibility user-message helper.
- `vite.config.ts`: local `/agent` proxy to `127.0.0.1:8010`.
- New protocol/executor tests in `tests/agentProtocol.test.mjs`; existing session tests retained.

## Safety and replay behavior

- Wire JSON stays `snake_case`; versions remain `agent-turn/0.1` and `agent-actions/0.1`.
- Runtime parsing rejects unknown versions/capabilities, wrong targets, extra action fields, wrong
  parameter types, duplicate IDs, and plans above five actions.
- Execution is serial. A failed action makes later actions `skipped` with `DEPENDENCY_FAILED`.
- The ledger keys by conversation/plan/action. Exact redelivery returns the stored receipt without
  repeating the effect; reuse of the same IDs with different action content is rejected.
- A plan whose expected UI version is stale has zero UI effect and a durable failed receipt.
- Network retry reuses the exact request or feedback ID/payload; it does not execute a plan again.
- Agent chat pending does not reuse `isGenerating`; help/navigation can still be sent while a
  generation job is running.

## Reproduction

Terminal 1 from repository root:

```powershell
.\.venv-agent\Scripts\python.exe -m uvicorn exam_baseline.agent.http:create_agent_app --factory --host 127.0.0.1 --port 8010
```

Terminal 2:

```powershell
cd astra-frontend
npm run dev -- --host 127.0.0.1
```

Create/open a custom workspace, then try:

- `Mở Tủ đề`
- `Mở mục Soạn đề`
- `Về màn hình chính`
- `Tạo một không gian làm việc mới`
- `Mở thiết lập đề`
- `Thu gọn menu` / `Mở rộng menu`

## Evidence observed on 2026-11-16

```text
npm run build                         PASS (Vite production build)
npm run lint                          PASS, 2 pre-existing no-useless-escape warnings
npm test                              PASS, 10/10
python -m ruff check ...              PASS
python -m pytest tests/agent -q       PASS, 73/73
python -m pytest -q                   PASS, 349/349; 1 dependency warning
```

A live transport smoke went through the Vite proxy, not directly to the Agent:

```text
POST http://127.0.0.1:5173/agent/turns
action_plan -> ui.navigate -> screen_id=library
POST http://127.0.0.1:5173/agent/execution-results
reply -> "Đã mở Tủ đề."
```

Automated browser/DOM smoke was attempted, but the Windows automation native pipe was unavailable.
Therefore this report does not claim browser E2E pass; UI/UX should run the manual steps above or
add its preferred browser test stack before merge.

## Decisions requested from UI/UX before merge

1. Accept the adapter folders and `snake_case` boundary, or propose a mapping change in one place
   (`agentProtocol.ts`) without changing the Agent wire version silently.
2. Confirm that opening `QuickPresetModal` is the correct meaning of `ui.exam.open_setup`.
3. Confirm whether creating a session should remain a separate effect, or whether the desired UX is
   a later two-step Agent flow: create → receive real ID → open workspace/setup.
4. Confirm how to expose Agent chat outside a workspace. Current UI has chat only inside a
   workspace; navigation works from there and the final reply is retained in that origin session,
   but it is visible again only after reopening the session.
5. Choose whether Agent errors need a designed toast/banner. This branch uses the existing workspace
   area and adds no new visual system.
6. Add/approve browser E2E and mobile capability rules. No production auth/persistence is claimed.

If these six points are accepted, the UI code can be reviewed as a narrow integration layer. If a
point is rejected, change the adapter/handler only; the presentation components should not require
a redesign.
