import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ExamSessions } from '../src/state/examSessions.ts';
import { ApiError, ApiExamService, resolveApiUrl } from '../src/services/examService.ts';

const params = { subject: 'Toán Học', grade: 12, examType: 'THPT_STANDARD', durationMinutes: 90, itemCount: 22, prompt: 'Đề THPT', uploadedFiles: [] };
const HASH_1 = 'a'.repeat(64);
const HASH_2 = 'b'.repeat(64);

function makePackage(revision = 1, contentHash = HASH_1, previewStatus = 'not_requested', extra = {}) {
  const query = `revision=${revision}&contentHash=${contentHash}`;
  return {
    examId: 'job-1',
    title: 'Đề Toán THPT',
    subject: 'Toán Học',
    grade: 12,
    durationMinutes: 90,
    totalScore: 10,
    createdAt: '2026-11-17T00:00:00Z',
    revision,
    contentHash,
    approved: false,
    approval: null,
    hasDrawings: false,
    visualWarnings: [],
    blueprint: {
      subject: 'Toán Học',
      grade: 12,
      examType: 'THPT_STANDARD',
      title: 'Toán THPT',
      totalQuestions: 1,
      durationMinutes: 90,
      levelDistribution: { nhanBiet: 1, thongHieu: 0, vanDung: 0, vanDungCao: 0 },
      topics: ['Hàm số'],
    },
    questions: [
      {
        id: 1,
        stableId: 'P1-1',
        examRevision: revision,
        part: 'P1',
        questionType: 'mcq',
        stem: 'Tính $1+1$.',
        choices: { A: '1', B: '2', C: '3', D: '4' },
        key: 'B',
        explanation: '$1+1=2$.',
        level: 'NHAN_BIET',
        topic: 'Số học',
        status: 'PENDING',
      },
    ],
    preview: {
      status: previewStatus,
      revision,
      contentHash,
      sourceHash: 'c'.repeat(64),
      compilerAvailable: true,
      draft: true,
      statusUrl: `/api/exams/job-1/preview?${query}`,
      pdfUrl: `/api/exams/job-1/preview.pdf?${query}`,
      logUrl: `/api/exams/job-1/preview.log?${query}`,
      ...(previewStatus === 'ready' ? { pageCount: 4, pdfHash: 'd'.repeat(64) } : {}),
    },
    ...extra,
  };
}

const flush = () => new Promise(resolve => setImmediate(resolve));

test('checking a saved question sends only the exam revision', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => new Response('{}'));
  const service = new ApiExamService('http://localhost:8000/api');
  await service.verifyQuestion('job-1', 3, 2);
  assert.equal(fetch.mock.callCount(), 1);
  const [url, request] = fetch.mock.calls[0].arguments;
  assert.equal(url, 'http://localhost:8000/api/exams/job-1/questions/3/verify');
  assert.equal(request.method, 'POST');
  assert.deepEqual(JSON.parse(request.body), { revision: 2 });
});

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

test('resolveApiUrl preserves query strings and avoids duplicate /api prefix', () => {
  const path = '/api/exams/job-1/preview.pdf?revision=2&contentHash=abc123';
  assert.equal(resolveApiUrl(path, '/api'), path);
  assert.equal(
    resolveApiUrl(path, 'http://127.0.0.1:8000/api'),
    'http://127.0.0.1:8000/api/exams/job-1/preview.pdf?revision=2&contentHash=abc123'
  );
  assert.equal(
    resolveApiUrl(path, 'http://127.0.0.1:8000/api/'),
    'http://127.0.0.1:8000/api/exams/job-1/preview.pdf?revision=2&contentHash=abc123'
  );
  assert.equal(
    resolveApiUrl(path, 'http://127.0.0.1:8000'),
    'http://127.0.0.1:8000/api/exams/job-1/preview.pdf?revision=2&contentHash=abc123'
  );
  assert.equal(resolveApiUrl('https://api.example.com/api/x?y=1', 'http://127.0.0.1:8000/api'), 'https://api.example.com/api/x?y=1');
  assert.equal(resolveApiUrl('data:application/pdf;base64,AAAA', 'http://127.0.0.1:8000/api'), 'data:application/pdf;base64,AAAA');
});

test('preview polls until ready, gates approval on opening, and invalidates on edit', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let progressCb;
  let currentPkg = makePackage(1, HASH_1, 'not_requested');
  let statusCalls = 0;
  const previewRequests = [];
  const service = {
    async startGeneration() { return { jobId: 'job-1' }; },
    onProgress(_id, cb) { progressCb = cb; return () => {}; },
    async getExamPackage() { return structuredClone(currentPkg); },
    async requestPreview(_jobId, binding) {
      previewRequests.push(binding);
      return {
        ...currentPkg.preview,
        status: binding.revision === 1 ? 'queued' : 'ready',
        revision: binding.revision,
        contentHash: binding.contentHash,
        ...(binding.revision > 1 ? { pageCount: 4, pdfHash: 'e'.repeat(64) } : {}),
      };
    },
    async getPreviewStatus(_jobId, binding) {
      statusCalls++;
      return {
        ...currentPkg.preview,
        status: statusCalls === 1 ? 'compiling' : 'ready',
        revision: binding.revision,
        contentHash: binding.contentHash,
        ...(statusCalls > 1 ? { pageCount: 4, pdfHash: 'd'.repeat(64) } : {}),
      };
    },
    async getPreviewLog() { return ''; },
    async regenerateQuestion() { return currentPkg.questions[0]; },
    async updateQuestion() {},
    async downloadExport() {},
  };

  const store = new ExamSessions(service);
  const id = store.create('template');
  store.setActiveSession(id);
  await store.generate(id, params);
  progressCb({ status: 'completed', stage: 6, percent: 100, completedItems: 1, totalItems: 1 });
  await flush();
  await flush();

  assert.equal(previewRequests.length, 1);
  assert.equal(store.getSnapshot()[0].preview?.status, 'queued');
  assert.equal(store.canApprove(id), false);

  t.mock.timers.tick(1250);
  await flush();
  await flush();
  assert.equal(store.getSnapshot()[0].preview?.status, 'compiling');
  assert.equal(store.canApprove(id), false);

  t.mock.timers.tick(1250);
  await flush();
  await flush();
  assert.equal(store.getSnapshot()[0].preview?.status, 'ready');
  assert.equal(store.canApprove(id), false);

  store.markPreviewOpened(id);
  assert.equal(store.canApprove(id), true);

  // Edit invalidates approval and preview, then refresh requests preview for revision 2
  store.invalidatePreview(id);
  assert.equal(store.getSnapshot()[0].preview, undefined);
  assert.equal(store.canApprove(id), false);

  currentPkg = makePackage(2, HASH_2, 'not_requested');
  await store.refresh(id);
  await flush();

  assert.equal(previewRequests.length, 2);
  assert.deepEqual(previewRequests[1], { revision: 2, contentHash: HASH_2 });
  assert.equal(store.getSnapshot()[0].preview?.status, 'ready');
  assert.equal(store.canApprove(id), false);

  store.markPreviewOpened(id);
  assert.equal(store.canApprove(id), true);
  store.dispose();
});

test('preview polling stops on workspace switch, remove, and dispose', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let progressCb;
  let statusCalls = 0;
  const service = {
    async startGeneration() { return { jobId: 'job-1' }; },
    onProgress(_id, cb) { progressCb = cb; return () => {}; },
    async getExamPackage() { return makePackage(1, HASH_1, 'not_requested'); },
    async requestPreview() { return { ...makePackage(1, HASH_1, 'queued').preview }; },
    async getPreviewStatus() {
      statusCalls++;
      return { ...makePackage(1, HASH_1, 'compiling').preview };
    },
    async regenerateQuestion() { throw new Error('unused'); },
    async updateQuestion() {},
    async downloadExport() {},
  };

  const store = new ExamSessions(service);
  const first = store.create('template');
  const second = store.create('custom');
  store.setActiveSession(first);
  await store.generate(first, params);
  progressCb({ status: 'completed', stage: 6, percent: 100, completedItems: 1, totalItems: 1 });
  await flush();
  await flush();

  // Switch workspace -> cancels timer for first
  store.setActiveSession(second);
  t.mock.timers.tick(5000);
  await flush();
  assert.equal(statusCalls, 0);

  // Switch back -> resumes preview and polls; then remove stops polling
  store.setActiveSession(first);
  await flush();
  store.remove(first);
  t.mock.timers.tick(5000);
  await flush();
  assert.equal(statusCalls, 0);

  store.dispose();
});

test('handles stale_revision, artifact_changed, latex_compiler_unavailable, and failed compile logs', async () => {
  let progressCb;
  let pkg = makePackage(1, HASH_1, 'ready');
  let generationCalls = 0;
  const previewRevisions = [];
  const service = {
    async startGeneration() { generationCalls++; return { jobId: 'job-1' }; },
    onProgress(_id, cb) { progressCb = cb; return () => {}; },
    async getExamPackage() { return structuredClone(pkg); },
    async requestPreview(_jobId, binding) {
      previewRevisions.push(binding.revision);
      return { ...pkg.preview, status: 'ready', revision: binding.revision, contentHash: binding.contentHash };
    },
    async getPreviewLog() { return '! Undefined control sequence \\badcmd.'; },
    async regenerateQuestion() { throw new Error('unused'); },
    async updateQuestion() {},
    async downloadExport() {},
  };

  const store = new ExamSessions(service);
  const id = store.create('template');
  await store.generate(id, params);
  progressCb({ status: 'completed', stage: 6, percent: 100, completedItems: 1, totalItems: 1 });
  await flush();
  await flush();

  // stale_revision reloads package and restarts preview
  pkg = makePackage(2, HASH_2, 'not_requested');
  await store.handleActionError(id, new ApiError('Exam changed', 'stale_revision', 409));
  await flush();
  assert.equal(store.getSnapshot()[0].package.revision, 2);
  assert.deepEqual(previewRevisions, [2]);

  // latex_compiler_unavailable does not regenerate the exam
  await store.handleActionError(id, new ApiError('No compiler', 'latex_compiler_unavailable', 503));
  assert.equal(store.getSnapshot()[0].previewErrorCode, 'latex_compiler_unavailable');
  assert.equal(generationCalls, 1);

  // failed preview fetches diagnostics from logUrl
  pkg = makePackage(3, 'f'.repeat(64), 'failed');
  pkg.preview.error = 'latex_compile_failed';
  await store.refresh(id);
  await flush();
  await flush();
  assert.equal(store.getSnapshot()[0].previewErrorCode, 'latex_compile_failed');
  assert.equal(store.getSnapshot()[0].previewLog, '! Undefined control sequence \\badcmd.');

  // artifact_changed blocks approval
  store.markPreviewOpened(id);
  await store.handleActionError(id, new ApiError('Source tampered', 'artifact_changed', 409));
  assert.equal(store.getSnapshot()[0].artifactChanged, true);
  assert.equal(store.canApprove(id), false);

  store.dispose();
});
