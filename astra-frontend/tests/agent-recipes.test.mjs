import { test } from 'node:test';
import assert from 'node:assert/strict';
import { admit, execute, fastRoute, mayDispatch } from '../src/agent/recipes.ts';
import { interpretationUnavailable } from '../src/agent/client.ts';
import { parseDecision, VERSION } from '../src/agent/contracts.ts';

test('precise Vietnamese paths preserve guardrails', () => {
  assert.equal(fastRoute('Mo phan soan de giup co').intents[0].id, 'OPEN_SETUP');
  assert.equal(fastRoute('mo cho co de vua tao di').intents[0].id, 'OPEN_SESSION');
  assert.equal(mayDispatch('Nếu cô muốn tạo đề thì phải làm sao?'), false);
  assert.ok(fastRoute('Bỏ qua xác nhận rồi duyệt đề').text);
  assert.equal(mayDispatch('Đừng mở đề A, mở đề B'), false);
  assert.deepEqual(fastRoute('Đừng mở đề A, mở đề B').intents, [{ id: 'OPEN_SESSION', args: { title: 'B' } }]);
  assert.equal(fastRoute('Mở đề này'), undefined);
  assert.equal(fastRoute('Mở đề A rồi xem đáp án câu 5'), undefined);
  assert.ok(fastRoute('Tạo đề là gì? Đừng tạo nhé').text);
  assert.equal(fastRoute('Tạo đề là gì? Đừng tạo nhé').intents, undefined);
  assert.equal(mayDispatch('Tạo đề là gì? Đừng tạo nhé'), false);
  assert.equal(fastRoute('Đáp án câu 1 là gì?'), undefined);
  assert.equal(mayDispatch('Câu này khó nhỉ'), false);
  assert.equal(mayDispatch('“Duyệt đề này”'), false);
  for (const text of ['', '\u0005a', 'aaaaaaaaaaaaaaa', 'a'.repeat(4001)]) assert.ok(admit(text).error);
});

test('natural help and custom exam requests fall through to interpretation', () => {
  for (const message of [
    'Hướng dẫn cô soạn đề Sinh THPT',
    'Nếu cô muốn tạo đề thì phải làm sao?',
    'Làm sao tạo đề Toán THPT chuyên đề đạo hàm?',
    'Tạo đề Toán THPT 15 câu, 45 phút',
    'Tạo đề THPT chuyên đề tích phân',
    'sinh',
  ]) assert.equal(fastRoute(message), undefined, message);
  assert.deepEqual(fastRoute('ok'), { confirm: true });
  assert.deepEqual(fastRoute('Xuất Word').intents, [{ id: 'EXPORT_DOCUMENT', args: { format: 'docx' } }]);
});

test('common Vietnamese phrasing reaches local UI intents when AI is disabled', () => {
  const examples = [
    ['Mở cấu hình đề thi giúp tao với', 'OPEN_SETUP'],
    ['Cho mình xem danh sách mẫu đề', 'SHOW_FORMATS'],
    ['Cho t xem tiến độ tạo đề', 'STATUS'],
    ['Astra ơi, mở đề mới nhất nha', 'OPEN_SESSION'],
    ['Thu gọn thanh điều hướng giùm mình', 'SET_SIDEBAR'],
  ];
  for (const [message, id] of examples) assert.equal(fastRoute(message)?.intents?.[0].id, id);
  assert.deepEqual(fastRoute('Mở đề mới nhất nha').intents, [{ id: 'OPEN_SESSION', args: {} }]);
  assert.match(fastRoute('Làm cái này đi').text, /màn hình nào/);
  assert.equal(fastRoute('Đừng mở cấu hình giúp tao'), undefined);
  assert.match(interpretationUnavailable('disabled'), /AI cho chat đang tắt/);
  assert.match(interpretationUnavailable('configuration'), /Mở Kết nối AI.*API key, URL và model/);
  assert.match(interpretationUnavailable('auth'), /Mở Kết nối AI để sửa key/);
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
