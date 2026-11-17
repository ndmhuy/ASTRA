import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ExamSessions } from '../src/state/examSessions.ts';

const params = { subject: 'Toán Học', grade: 12, examType: 'THPT_STANDARD', durationMinutes: 90, itemCount: 22, prompt: 'Đề THPT', uploadedFiles: [] };

test('a lost start receipt reuses the workspace idempotency key on retry', async () => {
  const requests = [];
  const service = {
    async startGeneration(input) {
      requests.push(input);
      if (requests.length === 1) throw Object.assign(new Error('network'), { code: 'network_error' });
      return { jobId: 'existing-server-job' };
    },
    onProgress() { return () => {}; },
  };
  const store = new ExamSessions(service);
  const id = store.create('template');
  await store.generate(id, params);
  assert.equal(store.getSnapshot()[0].status, 'error');
  await store.generate(id, params);
  assert.equal(requests[0].clientRequestId, requests[1].clientRequestId);
  const other = store.create('template');
  await store.generate(other, params);
  assert.notEqual(requests[1].clientRequestId, requests[2].clientRequestId);
  store.dispose();
});

test('terminal provider errors stop the subscription and remain in their original workspace', async () => {
  let callback;
  let stopped = 0;
  const store = new ExamSessions({
    async startGeneration() { return { jobId: 'failed-job' }; },
    onProgress(id, listener) { callback = listener; return () => stopped++; },
  });
  const id = store.create('template');
  const other = store.create('custom');
  await store.generate(id, params);
  callback({ status: 'failed', stage: 2, percent: 20, error: { code: 'provider_unavailable', message: 'Provider overloaded' } });
  assert.equal(store.getSnapshot().find(item => item.id === id).error, 'Provider overloaded');
  assert.equal(store.getSnapshot().find(item => item.id === other).status, 'draft');
  assert.equal(stopped, 1);
  store.dispose();
});
