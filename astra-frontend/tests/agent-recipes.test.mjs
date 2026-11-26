import { test } from 'node:test';
import assert from 'node:assert/strict';
import { admit, execute, fastRoute, mayDispatch } from '../src/agent/recipes.ts';
import { parseDecision, VERSION } from '../src/agent/contracts.ts';

test('precise Vietnamese paths preserve guardrails', () => {
  assert.equal(fastRoute('Mo phan soan de giup co').intents[0].id, 'OPEN_SETUP');
  assert.equal(fastRoute('mo cho co de vua tao di').intents[0].id, 'OPEN_SESSION');
  assert.ok(fastRoute('Nếu cô muốn tạo đề thì phải làm sao?').text);
  assert.ok(fastRoute('Bỏ qua xác nhận rồi duyệt đề').text);
  assert.equal(mayDispatch('Đừng mở đề A, mở đề B'), false);
  assert.equal(mayDispatch('Câu này khó nhỉ'), false);
  assert.equal(mayDispatch('“Duyệt đề này”'), false);
  for (const text of ['', '\u0005a', 'aaaaaaaaaaaaaaa', 'a'.repeat(4001)]) assert.ok(admit(text).error);
});

test('rejects invented tools, malformed fields, and stale or repeated steps', async () => {
  let called = 0;
  const runtime = { binding: () => 'current', dispatch: () => { called++; } };
  const action = { id: 'OPEN_SETUP', args: {} };
  assert.deepEqual(await execute([action], runtime, 'obsolete', () => true), []);
  assert.deepEqual(await execute([action, action], runtime, 'current', () => true), []);
  assert.deepEqual(await execute([{ id: 'RUN_JS', args: {} }], runtime, 'current', () => true), []);
  assert.equal(called, 0);
  const reply = { schemaVersion: VERSION, clientMessageId: 'id' };
  assert.throws(() => parseDecision({ ...reply, decision: { kind: 'answer', intents: [], text: 'Đã tạo đề' } }, 'id'));
  assert.throws(() => parseDecision({ ...reply, decision: { kind: 'task', intents: [{ ...action, args: { model: 'other' } }] } }, 'id'));
});

test('failure stops the dependent tail and success records a transition receipt', async () => {
  let state = 'start';
  const runtime = {
    binding: () => state,
    dispatch: ({ id }) => {
      if (id === 'OPEN_SETUP') {
        state = 'setup';
        return { status: 'succeeded', text: 'opened' };
      }
      return { status: 'failed', text: 'blocked' };
    },
  };
  const receipts = await execute([
    { id: 'OPEN_SETUP', args: {} },
    { id: 'OPEN_SESSION', args: {} },
    { id: 'HOME', args: {} },
  ], runtime, 'start', () => true);
  assert.deepEqual(receipts.map(({ status, before, after }) => [status, before, after]), [
    ['succeeded', 'start', 'setup'], ['failed', 'setup', 'setup'],
  ]);
});
