import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ExamSessions } from '../src/state/examSessions.ts';
import { recentQuestion, retrievedContext } from '../src/agent/memory.ts';

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

test('observed question memory is scoped to source, job and revision and is cleared in branches', () => {
  const question = { id: 15, stableId: 'P2-03', part: 'P2', examRevision: 2 };
  const source = { id: 'source', role: 'user', content: 'Xem câu 3 phần II', timestamp: '2026-11-27' };
  const initial = { id: 'session', title: 'Fixture', createdAt: '2026-11-27', messages: [source],
    questions: [question], package: { revision: 2 }, jobId: 'job', status: 'complete', draft: '' };
  let raw = JSON.stringify([initial]);
  globalThis.localStorage = { getItem: () => raw, setItem: (_, value) => { raw = value; } };
  try {
    const store = new ExamSessions({});
    store.rememberQuestion('session', 'P2-03', 'job', 2, 'source');
    const session = store.getSnapshot()[0];
    assert.deepEqual(recentQuestion(session), { number: 3, part: 'P2' });
    assert.equal(recentQuestion({ ...session, package: { revision: 3 } }), undefined);
    assert.equal(recentQuestion({ ...session, jobId: 'other' }), undefined);
    assert.equal(recentQuestion({ ...session, messages: [] }), undefined);
    const branch = store.branchAtMessage('session', 'source');
    assert.equal(store.getSnapshot().find(item => item.id === branch).conversation.questionReference, undefined);
    store.retractMessage('session', 'source');
    assert.equal(recentQuestion(store.getSnapshot().find(item => item.id === 'session')), undefined);
  } finally { delete globalThis.localStorage; }
});
