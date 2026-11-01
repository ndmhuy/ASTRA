import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ExamSessions } from '../src/state/examSessions.ts';
import { MockExamService } from '../src/services/examService.ts';

const params = (subject = 'Vật Lý') => ({ subject, grade: 12, examType: 'THPT_STANDARD', durationMinutes: 50, itemCount: 40, prompt: 'Đề ôn tập', uploadedFiles: [] });
const flush = () => new Promise(resolve => setImmediate(resolve));
function fakeService() {
  const callbacks = new Map();
  const jobs = new Map();
  const stopped = [];
  return { callbacks, jobs, stopped,
    async startGeneration(input) { const id = crypto.randomUUID(); jobs.set(id, { ...input, title: input.subject, durationMinutes: input.durationMinutes, questions: [] }); return { jobId: id }; },
    onProgress(id, callback) { callbacks.set(id, callback); return () => stopped.push(id); },
    async getExamPackage(id) { return jobs.get(id); },
  };
}

test('two generation jobs finish out of order without mixing drafts, chat, questions or metadata', async () => {
  const service = fakeService();
  const store = new ExamSessions(service);
  const first = store.create('template');
  const second = store.create('custom');
  store.sendMessage(second, 'Đề về dao động');
  store.setDraft(second, 'Nội dung chưa gửi');
  await Promise.all([store.generate(first, params()), store.generate(second, params('Toán Học'))]);
  const find = id => store.getSnapshot().find(session => session.id === id);
  const jobA = find(first).jobId;
  const jobB = find(second).jobId;
  const question = { id: 1, stem: 'Câu riêng của đề A' };
  service.callbacks.get(jobA)({ stage: 3, percent: 50, completedItems: 1, latestItemPreview: question });
  service.callbacks.get(jobA)({ stage: 3, percent: 50, completedItems: 1, latestItemPreview: question });
  assert.equal(find(first).questions.length, 1);
  assert.equal(find(second).questions.length, 0);
  service.jobs.get(jobB).questions = [{ id: 2, stem: 'Câu riêng của đề B' }];
  service.callbacks.get(jobB)({ stage: 5, percent: 100, completedItems: 1 });
  await flush();
  assert.equal(find(second).status, 'complete');
  assert.equal(find(first).status, 'generating');
  assert.equal(find(second).meta.subject, 'Toán Học');
  assert.equal(find(second).draft, 'Nội dung chưa gửi');
  assert.equal(find(first).messages.length, 0);
  service.jobs.get(jobA).questions = [question];
  service.callbacks.get(jobA)({ stage: 5, percent: 100, completedItems: 1 });
  await flush();
  assert.equal(find(first).questions[0].stem, 'Câu riêng của đề A');
  assert.equal(find(second).questions[0].stem, 'Câu riêng của đề B');
  assert.equal(service.stopped.length, 2);
});

test('failed final fetch stays in drafts and can be retried without affecting another session', async () => {
  const service = fakeService();
  service.getExamPackage = async () => { throw new Error('network'); };
  const store = new ExamSessions(service);
  const first = store.create('template');
  const other = store.create('custom');
  await store.generate(first, params());
  let session = store.getSnapshot().find(item => item.id === first);
  service.callbacks.get(session.jobId)({ stage: 5, percent: 100, completedItems: 1 });
  await flush();
  session = store.getSnapshot().find(item => item.id === first);
  assert.equal(session.status, 'error');
  assert.equal(store.getSnapshot().find(item => item.id === other).status, 'draft');
  await store.generate(first, params());
  assert.equal(store.getSnapshot().find(item => item.id === first).status, 'generating');
  store.dispose();
});

test('duplicate start does not launch a second job and dispose stops all subscriptions', async () => {
  const service = fakeService();
  const store = new ExamSessions(service);
  const id = store.create('template');
  await Promise.all([store.generate(id, params()), store.generate(id, params())]);
  assert.equal(service.jobs.size, 1);
  store.dispose();
  assert.equal(service.stopped.length, 1);
});

test('mock service keeps per-job metadata and edits isolated', async () => {
  const service = new MockExamService();
  const [a, b] = await Promise.all([service.startGeneration(params()), service.startGeneration(params('Toán Học'))]);
  assert.notEqual(a.jobId, b.jobId);
  const original = await service.getExamPackage(a.jobId);
  await service.updateQuestion(a.jobId, { ...original.questions[0], stem: 'Updated only in A' });
  assert.equal((await service.getExamPackage(a.jobId)).questions[0].stem, 'Updated only in A');
  assert.notEqual((await service.getExamPackage(b.jobId)).questions[0].stem, 'Updated only in A');
  assert.equal((await service.getExamPackage(a.jobId)).subject, 'Vật Lý');
  assert.equal((await service.getExamPackage(b.jobId)).subject, 'Toán Học');
  await assert.rejects(() => service.getExamPackage('missing'));
});
