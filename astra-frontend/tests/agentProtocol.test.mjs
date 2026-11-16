import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseActionPlan, parseTurnResponse } from '../src/integration/agentProtocol.ts';
import { UiExecutor } from '../src/integration/uiExecutor.ts';

const plan = () => ({
  schema_version: 'agent-actions/0.1',
  plan_id: 'p1',
  conversation_id: 'workspace:w1',
  expected_state_version: 3,
  actions: [{ action_id: 'a1', capability_id: 'ui.navigate', target: 'application', params: { screen_id: 'library' } }],
});

test('strict parser accepts the frozen action envelope and rejects extra fields', () => {
  assert.equal(parseActionPlan(plan()).actions[0].capability_id, 'ui.navigate');
  assert.throws(() => parseActionPlan({ ...plan(), accidental: true }), /INVALID_PLAN_SHAPE/);
  assert.throws(() => parseActionPlan({ ...plan(), actions: [...plan().actions, { ...plan().actions[0] }] }), /DUPLICATE_ACTION_ID/);
  assert.throws(() => parseActionPlan({ ...plan(), actions: [{ ...plan().actions[0], target: 'wrong' }] }), /INVALID_TARGET/);
});

test('turn response must correlate a valid plan with action_plan kind', () => {
  const response = parseTurnResponse({ schema_version: 'agent-turn/0.1', request_id: 'r1', conversation_id: 'workspace:w1', kind: 'action_plan', reply: 'Đang mở.', data: { plan: plan() }, mock: true });
  assert.equal(response.data.plan.plan_id, 'p1');
  assert.throws(() => parseTurnResponse({ ...response, kind: 'reply' }), /UNEXPECTED_PLAN/);
});

test('executor is stale-safe and replays a committed action without repeating its effect', async () => {
  let context = { screen_id: 'workspace', state_version: 3, workspace_session_id: 'w1', selected_question_id: null, question_index_map: {}, available_actions: ['ui.navigate'] };
  let effects = 0;
  const executor = new UiExecutor({ 'ui.navigate': async () => {
    effects += 1;
    context = { ...context, screen_id: 'library', workspace_session_id: null, state_version: 4 };
    return { data: { screen_id: 'library' }, stateVersion: 4 };
  } }, () => context);
  const parsed = parseActionPlan(plan());
  assert.equal((await executor.execute(parsed))[0].status, 'success');
  assert.equal((await executor.execute(parsed))[0].status, 'success');
  assert.equal(effects, 1);
  await assert.rejects(() => executor.execute({ ...parsed, actions: [{ ...parsed.actions[0], params: { screen_id: 'welcome' } }] }), /PLAN_ACTION_ID_REUSED/);
  const stale = { ...parsed, plan_id: 'p2', expected_state_version: 2, actions: [{ ...parsed.actions[0], action_id: 'a2' }] };
  assert.equal((await executor.execute(stale))[0].error_code, 'STALE_CONTEXT');
});
