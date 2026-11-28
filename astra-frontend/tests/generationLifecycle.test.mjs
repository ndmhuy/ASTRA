import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ExamSessions } from '../src/state/examSessions.ts';
import { ApiExamService } from '../src/services/examService.ts';
import { generationTarget, generationReceipt } from '../src/agent/lifecycle.ts';
import { fastRoute } from '../src/agent/recipes.ts';

const progress = (status, version = 1) => ({ jobId: 'saved-job', executionVersion: version, checkpointVersion: 1,
  stage: 2, stageName: 'composer', percent: 40, completedItems: 16, totalItems: 22,
  estimatedSecondsLeft: 0, statusMessage: status, status, resumeAvailable: status === 'paused' });
function fixture() {
  let state = progress('paused');
  const posts = [], callbacks = [];
  let pending;
  const entry = () => ({ id: 'workspace', revision: 1, mode: 'custom', title: 'Đề Sinh',
    draft: '', messages: [], createdAt: '2026-11-28T00:00:00Z', jobId: 'saved-job', jobStatus: state.status,
    generationId: 'saved-job', generationStatus: state.status, generationState: { ...state } });
  const service = {
    workspaceLibrary: { async list() { return { workspaces: [entry()] }; } },
    async generationState() { return { ...state }; },
    async resumeGeneration(jobId, executionVersion) {
      posts.push({ jobId, executionVersion });
      if (pending) await pending;
      state = progress('resuming', 2);
      return { ...state };
    },
    async pauseGeneration(jobId, executionVersion) {
      posts.push({ jobId, executionVersion });
      state = progress('pausing', 2);
      return { ...state };
    },
    onProgress(_id, callback) { callbacks.push(callback); return () => {}; },
  };
  return { service, posts, callbacks, setState: value => { state = value; }, hold: value => { pending = value; } };
}

test('reload restores saved academic progress and watches only after explicit same-job resume', async () => {
  const f = fixture();
  const store = new ExamSessions(f.service);
  await store.loadLibrary();
  const saved = store.getSnapshot()[0];
  assert.equal(saved.stoppedJobId, 'saved-job');
  assert.equal(saved.progress.completedItems, 16);
  assert.equal(f.posts.length, 0);
  assert.equal(f.callbacks.length, 0);
  await store.controlGeneration(saved.id, 'resume');
  assert.deepEqual(f.posts, [{ jobId: 'saved-job', executionVersion: 1 }]);
  assert.equal(store.getSnapshot()[0].jobId, 'saved-job');
  assert.equal(store.getSnapshot()[0].progress.executionVersion, 2);
  assert.equal(store.getSnapshot()[0].progress.status, 'resuming');
  assert.equal(f.callbacks.length, 1);
  f.callbacks[0](progress('paused', 1));
  assert.equal(store.getSnapshot()[0].progress.status, 'resuming');
  // A delayed library response from the previous execution cannot roll back state.
  f.setState(progress('paused', 1));
  await store.loadLibrary();
  assert.equal(store.getSnapshot()[0].progress.executionVersion, 2);
  f.callbacks[0]({ ...progress('running', 2), connectionLost: true, statusMessage: 'Mất kết nối' });
  assert.equal(store.getSnapshot()[0].progress.status, 'resuming');
  assert.equal(store.getSnapshot()[0].generationError, 'Mất kết nối');
  f.callbacks[0](progress('running', 2));
  assert.equal(store.getSnapshot()[0].generationError, undefined);
  store.sendMessage(saved.id, 'Tôi vẫn chat khi đang tạo');
  assert.equal(store.getSnapshot()[0].messages.at(-1).content, 'Tôi vẫn chat khi đang tạo');
  store.dispose();
});

test('duplicate controls and stale execution versions cannot send another POST', async () => {
  const f = fixture(), store = new ExamSessions(f.service);
  await store.loadLibrary();
  let release;
  f.hold(new Promise(resolve => { release = resolve; }));
  const first = store.controlGeneration('workspace', 'resume');
  await assert.rejects(store.controlGeneration('workspace', 'resume'), /Đang xử lý/);
  release();
  await first;
  await assert.rejects(store.controlGeneration('workspace', 'pause', { jobId: 'saved-job', executionVersion: 1 }), /thay đổi/);
  assert.equal(f.posts.length, 1);
  assert.equal((await store.controlGeneration('workspace', 'pause')).status, 'pausing');
  assert.equal(generationReceipt('pause', store.getSnapshot()[0].progress).status, 'accepted');
  store.dispose();
});

test('job targeting clarifies multiple matches and respects current job or explicit title', () => {
  const a = { id: 'a', title: 'Sinh A', stoppedJobId: 'ja', progress: progress('paused') };
  const b = { id: 'b', title: 'Sinh B', stoppedJobId: 'jb', progress: progress('paused') };
  assert.equal(generationTarget([a, b], null, 'resume').target, undefined);
  assert.match(generationTarget([a, b], null, 'resume').text, /2 phiên/);
  assert.equal(generationTarget([a, b], 'b', 'resume').target.id, 'b');
  assert.equal(generationTarget([a, b], null, 'resume', 'Sinh A').target.id, 'a');
  assert.equal(generationTarget([a, b], null, 'resume', 'Sinh').target, undefined);
  assert.equal(generationTarget([a, b], 'a', 'pause').target, undefined);
});

test('backend receipts distinguish acceptance, actual running, saved pause and failure', () => {
  assert.equal(generationReceipt('resume', progress('resuming')).status, 'accepted');
  assert.equal(generationReceipt('resume', progress('running')).status, 'succeeded');
  assert.equal(generationReceipt('pause', progress('pausing')).status, 'accepted');
  assert.equal(generationReceipt('pause', progress('paused')).status, 'succeeded');
  assert.equal(generationReceipt('retry', progress('interrupted')).status, 'failed');
});

test('controls include execution version and polling reconnects without fabricating failure', async t => {
  const posted = [];
  t.mock.method(globalThis, 'fetch', async (url, request) => {
    posted.push([url, request]);
    return new Response(JSON.stringify(progress('paused')), { headers: { 'Content-Type': 'application/json' } });
  });
  const api = new ApiExamService('/api');
  await api.pauseGeneration('saved-job', 3);
  assert.deepEqual(JSON.parse(posted[0][1].body), { schemaVersion: 'astra-generation-control-v1', executionVersion: 3 });
  t.mock.timers.enable({ apis: ['setInterval'] });
  const original = globalThis.EventSource;
  globalThis.EventSource = class { close() {} };
  t.after(() => { globalThis.EventSource = original; });
  let offline = true;
  globalThis.fetch = async () => {
    if (offline) throw new Error('offline');
    return new Response(JSON.stringify(progress('running', 3)));
  };
  const seen = [];
  const detach = api.onProgress('saved-job', data => seen.push(data));
  for (let i = 0; i < 4; i++) { await new Promise(resolve => setImmediate(resolve)); t.mock.timers.tick(1500); }
  assert.ok(seen.some(data => data.connectionLost));
  assert.ok(seen.every(data => data.status !== 'failed'));
  offline = false;
  await new Promise(resolve => setImmediate(resolve));
  t.mock.timers.tick(1500);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(seen.at(-1).status, 'running');
  detach();
});

test('preview retry stays distinct from academic retry and lifecycle questions never execute', () => {
  assert.equal(fastRoute('Thử lại bản xem trước PDF').intents[0].id, 'RETRY_PREVIEW');
  for (const message of ['Đừng tạm dừng', 'Chưa cần dừng, cô chỉ hỏi cách dừng thôi.', 'Nếu tiếp tục đề thì sao?', '“Thử lại phần bị lỗi”', 'Tạm dừng được không?', 'Dừng tạo đề rồi xuất Word']) {
    assert.equal(fastRoute(message)?.intents, undefined, message);
  }
});
