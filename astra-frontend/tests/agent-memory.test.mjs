import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ExamSessions } from '../src/state/examSessions.ts';
import { retrievedContext } from '../src/agent/memory.ts';

test('legacy migration, meaningful title, bounded facts, branch and retract', () => {
  let raw = JSON.stringify([{
    id: 'old', mode: 'custom', status: 'draft', title: 'Đề 1 · Theo yêu cầu',
    createdAt: '2026-10-01T08:00:00Z', questions: [], messages: [], draft: '', jobId: null,
  }]);
  globalThis.localStorage = { getItem: () => raw, setItem: (_, value) => { raw = value; } };
  try {
    const store = new ExamSessions({});
    store.appendMessage('old', 'user', 'Chào em', 'hello');
    assert.equal(store.getSnapshot()[0].conversation.titleOrigin, 'default');
    store.appendMessage('old', 'user', 'Ôn THPT Toán đạo hàm', 'goal', true);
    assert.equal(store.getSnapshot()[0].conversation.titleOrigin, 'default');
    store.suggestTitle('old', 'Đề ôn tập đạo hàm', 'goal', 3);
    assert.equal(store.getSnapshot()[0].title, 'Đề ôn tập đạo hàm');
    store.rename('old', 'Ôn Toán tháng 12');
    store.setIntake('old', { sourceId: 'goal', formatId: 'thpt-math', version: '1', phase: 'confirmed' });
    for (let i = 0; i < 12; i++) store.appendMessage('old', 'user', `Nội dung ${i}`, `msg-${i}`);
    const restored = new ExamSessions({});
    const session = restored.getSnapshot()[0];
    assert.equal(session.title, 'Ôn Toán tháng 12');
    assert.equal(session.conversation.titleOrigin, 'manual');
    assert.equal(session.messages.length, 14);
    const context = retrievedContext(session, 'unrelated', 'đạo hàm');
    assert.ok(context.history.length <= 8);
    assert.ok(context.history.includes('Ôn THPT Toán đạo hàm'));
    assert.match(context.facts[0], /confirmed/);
    const branch = restored.branchAtMessage('old', 'goal');
    assert.equal(restored.getSnapshot()[0].id, branch);
    assert.equal(restored.getSnapshot()[0].jobId, null);
    assert.equal(restored.getSnapshot()[0].intake.phase, 'selected');
    restored.retractMessage('old', 'goal');
    assert.equal(restored.getSnapshot().find(item => item.id === 'old').intake, undefined);
    assert.equal(restored.getSnapshot()[0].messages.length, 2);
  } finally {
    delete globalThis.localStorage;
  }
});

test('malformed storage is preserved for recovery', () => {
  let writes = 0;
  globalThis.localStorage = { getItem: () => 'broken-json', setItem: () => { writes++; } };
  try {
    const store = new ExamSessions({});
    assert.match(store.storageWarning, /Dữ liệu cũ vẫn được giữ/);
    store.create('custom');
    assert.equal(writes, 0);
  } finally {
    delete globalThis.localStorage;
  }
});
