import { test } from 'node:test';
import assert from 'node:assert/strict';
import { UiContextTracker } from '../src/agent/context.ts';
import { UiActionExecutor, executeActionPlan } from '../src/agent/executor.ts';
import { UI_CAPABILITY_MANIFEST } from '../src/agent/capabilities.ts';
import { ExamSessions } from '../src/state/examSessions.ts';

function baseRaw(overrides = {}) {
  return {
    workspaceId: null,
    screen: 'start',
    activeModal: null,
    sidebarCollapsed: false,
    activeJob: null,
    examRevision: null,
    sessions: [],
    notes: [],
    capabilities: UI_CAPABILITY_MANIFEST,
    ...overrides,
  };
}

test('context version changes only when sanitized UI state changes', () => {
  const tracker = new UiContextTracker();
  const first = tracker.capture(baseRaw());
  const same = tracker.capture(baseRaw());
  const changed = tracker.capture(baseRaw({ sidebarCollapsed: true }));
  assert.equal(first.stateVersion, 1);
  assert.equal(same.stateVersion, 1);
  assert.equal(changed.stateVersion, 2);
  assert.equal(JSON.stringify(changed).includes('GEMINI_API_KEY'), false);
});

test('executor observes real effect, reuses duplicate receipt and rejects stale input', async () => {
  const tracker = new UiContextTracker();
  let raw = baseRaw();
  const context = () => tracker.capture(raw);
  const executor = new UiActionExecutor(context, {
    'ui.session.create': params => {
      assert.equal(params.mode, 'custom');
      raw = baseRaw({
        workspaceId: 'workspace-new',
        screen: 'workspace',
        sessions: [{ id: 'workspace-new', title: 'Đề mới', status: 'draft', createdAt: 'now' }],
      });
      return { workspaceId: 'workspace-new' };
    },
  });
  const proposal = {
    kind: 'propose_ui_action', text: 'open', actionId: 'action-1',
    capabilityId: 'ui.session.create', expectedStateVersion: context().stateVersion,
    params: { mode: 'custom' }, target: {},
  };
  const receipt = await executor.execute(proposal);
  assert.equal(receipt.status, 'success');
  assert.equal(receipt.result.workspaceId, 'workspace-new');
  const duplicate = await executor.execute(proposal);
  assert.equal(duplicate.status, 'success');
  assert.equal(duplicate.duplicate, true);

  const stale = await executor.execute({ ...proposal, actionId: 'action-stale', expectedStateVersion: 1 });
  assert.equal(stale.status, 'failed');
  assert.equal(stale.errorCode, 'STALE_CONTEXT');
});

test('executor rejects invalid and invented capabilities without invoking handlers', async () => {
  const tracker = new UiContextTracker();
  const context = () => tracker.capture(baseRaw());
  let calls = 0;
  const executor = new UiActionExecutor(context, {
    'ui.sidebar.set_collapsed': () => { calls++; },
  });
  const invalid = await executor.execute({
    kind: 'propose_ui_action', text: 'collapse', actionId: 'invalid',
    capabilityId: 'ui.sidebar.set_collapsed', expectedStateVersion: 1,
    params: { collapsed: 'yes' }, target: {},
  });
  const invented = await executor.execute({
    kind: 'propose_ui_action', text: 'delete', actionId: 'invented',
    capabilityId: 'backend.deleteExam', expectedStateVersion: 1,
    params: {}, target: {},
  });
  assert.equal(invalid.errorCode, 'INVALID_COLLAPSED_VALUE');
  assert.equal(invented.errorCode, 'CAPABILITY_UNAVAILABLE');
  assert.equal(calls, 0);
});

test('dependent steps are skipped after opener failure', async () => {
  const tracker = new UiContextTracker();
  const context = () => tracker.capture(baseRaw());
  const executor = new UiActionExecutor(context, {
    'ui.exam.open_setup': () => { throw new Error('modal failed'); },
    'ui.sidebar.set_collapsed': () => { throw new Error('must not execute'); },
  });
  const receipts = await executeActionPlan([
    { kind: 'propose_ui_action', text: 'setup', actionId: 'step-1', capabilityId: 'ui.exam.open_setup', expectedStateVersion: 1, params: {}, target: {} },
    { kind: 'propose_ui_action', text: 'collapse', actionId: 'step-2', capabilityId: 'ui.sidebar.set_collapsed', expectedStateVersion: 1, params: { collapsed: true }, target: {} },
  ], executor);
  assert.equal(receipts[0].errorCode, 'HANDLER_FAILED');
  assert.equal(receipts[1].status, 'skipped');
  assert.equal(receipts[1].errorCode, 'DEPENDENCY_FAILED');
});

test('generation-time notes stay in UI state and can be edited or cancelled', async () => {
  const service = {
    async startGeneration() { return { jobId: 'job-1' }; },
    onProgress() { return () => {}; },
  };
  const store = new ExamSessions(service);
  const id = store.create('custom');
  await store.generate(id, { subject: 'Toán Học', grade: 12, examType: 'THPT_STANDARD', durationMinutes: 90, itemCount: 22, prompt: 'test', uploadedFiles: [] });
  const note = store.addNote(id, { targetQuestion: 3, requestedChange: 'Dễ hơn', teacherText: 'Câu 3 sửa dễ hơn' });
  assert.ok(note);
  assert.equal(store.getSnapshot()[0].agentNotes[0].jobId, 'job-1');
  assert.equal(store.updateNote(id, note.id, 'Ngắn hơn'), true);
  assert.equal(store.getSnapshot()[0].agentNotes[0].requestedChange, 'Ngắn hơn');
  assert.equal(store.cancelNote(id, note.id), true);
  assert.equal(store.getSnapshot()[0].agentNotes[0].status, 'cancelled');
  store.dispose();
});

test('completion with pending notes asks for review and never claims they were applied', async () => {
  let progress;
  const service = {
    async startGeneration() { return { jobId: 'job-2' }; },
    onProgress(_id, callback) { progress = callback; return () => {}; },
    async getExamPackage() {
      return { examId: 'job-2', title: 'Đề kiểm tra', subject: 'Toán Học', durationMinutes: 90, questions: [{ id: 1 }], revision: 1, contentHash: 'a'.repeat(64) };
    },
  };
  const store = new ExamSessions(service);
  const id = store.create('custom');
  await store.generate(id, { subject: 'Toán Học', grade: 12, examType: 'THPT_STANDARD', durationMinutes: 90, itemCount: 22, prompt: 'test', uploadedFiles: [] });
  store.addNote(id, { targetQuestion: 1, requestedChange: 'Ngắn hơn', teacherText: 'Sửa câu 1 ngắn hơn' });
  progress({ status: 'completed', stage: 5, percent: 100, completedItems: 1, totalItems: 1 });
  await new Promise(resolve => setImmediate(resolve));
  const assistant = store.getSnapshot()[0].messages.at(-1).content;
  assert.match(assistant, /ghi chú đang chờ/);
  assert.match(assistant, /chưa được tự động áp dụng/);
  store.dispose();
});
