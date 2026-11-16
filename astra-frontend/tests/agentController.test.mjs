import { test } from 'node:test';
import assert from 'node:assert/strict';
import { runAgentTurn } from '../src/integration/agentController.ts';
import { AgentHttpError, agentService } from '../src/services/agentService.ts';
import { ExamSessions } from '../src/state/examSessions.ts';
import { UiExecutor } from '../src/integration/uiExecutor.ts';

function fixture() {
  const store = new ExamSessions({});
  const id = store.create('custom');
  let context = { screen_id: 'workspace', workspace_session_id: id, state_version: 1, selected_question_id: null, question_index_map: {}, available_actions: ['ui.navigate'] };
  let effects = 0;
  const executor = new UiExecutor({ 'ui.navigate': async () => {
    effects++;
    context = { ...context, screen_id: 'library', workspace_session_id: null, state_version: 2 };
    return { data: { screen_id: 'library' }, stateVersion: 2 };
  } }, () => context);
  const getContext = () => context;
  const reply = request => ({ schema_version: 'agent-turn/0.1', request_id: request.request_id, conversation_id: request.conversation_id, kind: 'reply', reply: 'Đã mở Tủ đề.', data: {}, mock: false });
  return { store, id, executor, getContext, reply, effects: () => effects };
}

test('502 recovery reuses the original turn and does not duplicate the user message', async () => {
  const f = fixture();
  const requests = [];
  const service = { turn: async request => { requests.push(structuredClone(request)); if (requests.length === 1) throw new AgentHttpError(502, 'HTTP_502'); return f.reply(request); } };
  const deps = { ...f, service };
  await runAgentTurn(f.id, 'Mở Tủ đề', deps);
  assert.match(f.store.getSnapshot()[0].agentError, /npm run dev/);
  await runAgentTurn(f.id, null, deps);
  assert.deepEqual(requests[0], requests[1]);
  assert.deepEqual(f.store.getSnapshot()[0].messages.map(m => m.role), ['user', 'assistant']);
});

test('feedback outage retries only the exact receipt; action runs once', async () => {
  const f = fixture();
  let request;
  let turns = 0;
  const feedbacks = [];
  const service = {
    turn: async input => {
      request = input; turns++;
      return { ...f.reply(input), kind: 'action_plan', data: { plan: { schema_version: 'agent-actions/0.1', conversation_id: input.conversation_id, plan_id: 'p1', expected_state_version: 1, actions: [{ action_id: 'a1', capability_id: 'ui.navigate', target: 'application', params: { screen_id: 'library' } }] } } };
    },
    feedback: async feedback => { feedbacks.push(structuredClone(feedback)); if (feedbacks.length === 1) throw new TypeError('network'); return f.reply(request); },
  };
  await runAgentTurn(f.id, 'Mở Tủ đề', { ...f, service });
  await runAgentTurn(f.id, null, { ...f, service });
  assert.equal(f.effects(), 1);
  assert.equal(turns, 1);
  assert.deepEqual(feedbacks[0], feedbacks[1]);
  assert.equal(f.store.getSnapshot()[0].messages.length, 2);
});

test('double submit is suppressed before React commits pending state', async () => {
  const f = fixture();
  let resolve;
  const service = { turn: request => new Promise(done => { resolve = () => done(f.reply(request)); }) };
  const first = runAgentTurn(f.id, 'hello', { ...f, service });
  await runAgentTurn(f.id, 'hello', { ...f, service });
  assert.equal(f.store.getSnapshot()[0].messages.length, 1);
  resolve(); await first;
  assert.equal(f.store.getSnapshot()[0].messages.length, 2);
});

test('HTTP adapter retries transient 502 with byte-identical JSON', async () => {
  const originalFetch = globalThis.fetch;
  const bodies = [];
  globalThis.fetch = async (_url, options) => {
    bodies.push(options.body);
    if (bodies.length === 1) return new Response('', { status: 502 });
    return Response.json({ schema_version: 'agent-turn/0.1', request_id: 'r', conversation_id: 'c', kind: 'reply', reply: 'ok', data: {}, mock: true });
  };
  try { await agentService.turn({ request_id: 'r' }); assert.equal(bodies.length, 2); assert.equal(bodies[0], bodies[1]); }
  finally { globalThis.fetch = originalFetch; }
});
