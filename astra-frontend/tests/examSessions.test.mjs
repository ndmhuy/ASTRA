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

test('browser import keeps the original data and leaves failed entries available locally', async t => {
  const id = crypto.randomUUID();
  const missingId = crypto.randomUUID();
  const legacy = { id, mode: 'custom', title: 'Local draft', status: 'draft', draft: 'Draft text',
    jobId: null, messages: [], questions: [], meta: null, createdAt: new Date().toISOString() };
  const original = JSON.stringify([legacy, { ...legacy, id: missingId, jobId: crypto.randomUUID() }]);
  const storage = new Map([['astra.sessions.v1', original]]);
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true, value: { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) },
  });
  t.after(() => {
    if (descriptor) Object.defineProperty(globalThis, 'localStorage', descriptor);
    else delete globalThis.localStorage;
  });

  const workspaces = [];
  const service = fakeService();
  service.workspaceLibrary = {
    async list() { return { workspaces }; },
    async importLegacy(workspaceId, payload) {
      if (payload.jobId) throw Object.assign(new Error('Missing job'), { code: 'workspace_import_missing_job' });
      assert.equal(workspaceId, id);
      workspaces.push({ ...payload, id, revision: 1 });
      return { status: 'imported' };
    },
  };
  const store = new ExamSessions(service);
  await store.importBrowserLibrary();
  assert.equal(store.getSnapshot().find(session => !session.browserOnly).draft, legacy.draft);
  assert.equal(store.getSnapshot().filter(session => session.browserOnly).length, 1);
  assert.equal(storage.get('astra.sessions.v1'), original);
  assert.match(store.getBrowserImport().message, /Đã nhập 1 đề.*1 đề trên máy chủ/);

  const reloaded = new ExamSessions(service);
  await reloaded.loadLibrary();
  assert.equal(reloaded.getSnapshot().filter(session => session.browserOnly).length, 1);
  await reloaded.importBrowserLibrary();
  assert.equal(workspaces.length, 1);
  assert.equal(storage.get('astra.sessions.v1'), original);
});

test('a draft save with a lost response is acknowledged before sending newer edits', async () => {
  let saved;
  let loseResponse = false;
  const service = fakeService();
  service.workspaceLibrary = {
    async list() { return { workspaces: saved ? [saved] : [] }; },
    async save(id, draft, revision) {
      if (saved?.draft === draft.draft) return { revision: saved.revision };
      assert.equal(revision, saved?.revision ?? 0);
      saved = { ...draft, id, revision: revision + 1, createdAt: new Date().toISOString(), jobId: null };
      if (loseResponse) throw Object.assign(new Error('Lost response'), { code: 'network_error' });
      return { revision: saved.revision };
    },
  };
  const writer = new ExamSessions(service);
  const id = writer.create('custom');
  await flush();
  loseResponse = true;
  writer.setDraft(id, 'First edit');
  await flush();
  assert.ok(writer.getLibraryError());
  loseResponse = false;
  writer.setDraft(id, 'Latest edit');
  await flush();

  const reader = new ExamSessions(service);
  await reader.loadLibrary();
  assert.equal(reader.getSnapshot()[0].draft, 'Latest edit');
  assert.equal(writer.getLibraryError(), '');
});

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

test('deleting a generating session stops updates and leaves other sessions intact', async () => {
  const service = fakeService();
  const store = new ExamSessions(service);
  const removed = store.create('template');
  const kept = store.create('custom');
  store.setDraft(kept, 'Giữ nguyên nội dung');
  await store.generate(removed, params());
  const jobId = store.getSnapshot().find(s => s.id === removed).jobId;
  store.remove(removed);
  assert.deepEqual(service.stopped, [jobId]);
  service.callbacks.get(jobId)({ stage: 5, percent: 100, completedItems: 1 });
  await flush();
  assert.equal(store.getSnapshot().length, 1);
  assert.equal(store.getSnapshot()[0].id, kept);
  assert.equal(store.getSnapshot()[0].draft, 'Giữ nguyên nội dung');
});

test('deleting before generation starts does not register a late subscription', async () => {
  const service = fakeService();
  let resolveStart;
  service.startGeneration = () => new Promise(resolve => { resolveStart = resolve; });
  const store = new ExamSessions(service);
  const id = store.create('template');
  const pending = store.generate(id, params());
  store.remove(id);
  resolveStart({ jobId: 'late-job' });
  await pending;
  assert.equal(service.callbacks.size, 0);
  assert.deepEqual(store.getSnapshot(), []);
});
