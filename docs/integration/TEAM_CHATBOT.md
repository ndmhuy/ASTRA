# Chatbot handoff

Source: inspected `origin/feat/longlth2297/m2-ui-agent-orchestration` `47b1161`.
Cached snapshot; refresh first. Use this branch rather than separately merging its earlier integration branch.

## Our UI architecture: where you connect

`App.tsx` owns screens and active workspace. `ExamSessions` owns per-workspace chat, draft,
questions and job ID. `handleSendMessage` currently calls `store.sendMessage`, which appends
a canned reply: replace this path with your controller/service, not a second chat store.
`WorkspaceLayout` displays chat beside the exam canvas. Detailed setup creates/opens a custom
workspace directly; quick setup uses `QuickPresetModal`. Generation separately uses `examService`.
The UI supports message retract/branch actions; these currently change local history only.

## Our proposed merge with you

Bring M2 protocol/controller/executor/service/tests into latest `uiux2`; manually adapt App/store
handlers. UI supplies fresh semantic screen/workspace context and commits actions; Agent chooses
intent and replies after receipts. Preserve session IDs across retries and navigation.

Use Backend's proposed format JSON catalog to explain formats/collect overrides, not a separate
list of counts or rules. Return missing fields and unavailable capabilities clearly. Agree how
message retract/branch creates or revises Agent conversation context before enabling it remotely.
We propose independent chat/job loading; direct detailed setup must stay direct.
Please propose protocol/handler changes where current M2 assumptions differ; agree mappings
before editing either team's core state.

## Deliver

- [ ] Help UI port `agentProtocol`, controller, executor, service and tests into latest `uiux2`.
- [ ] Preserve `agent-turn/0.1`, `agent-actions/0.1`, snake_case wire fields and correlated receipts.
- [ ] Replace fixture requirements/evaluation ports with Backend descriptor/evaluator.
- [ ] Ask for unresolved fields; emit generation plan only against backend-validated approval.
- [ ] Keep UI generation adapter as sole start caller; retain replay/stale-plan protection.
- [ ] Reconcile setup capability with current direct detailed-setup flow; identify any unsupported commands explicitly.

## Dependencies and acceptance

Needs Backend requirements/evaluation fixtures and UI handlers/context. Local navigation works on
the source branch; real generation remains unconnected.

Done: missing fields trigger clarification; mock readiness cannot start real generation;
retry does not duplicate effects; late responses preserve workspace identity.
Supply example turn/response/receipt and current test commands.
