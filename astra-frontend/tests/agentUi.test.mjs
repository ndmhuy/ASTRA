import { test } from 'node:test';
import assert from 'node:assert/strict';
import { UiContextTracker } from '../src/agent/context.ts';
import { UiActionExecutor, executeActionPlan } from '../src/agent/executor.ts';
import { UI_CAPABILITY_MANIFEST } from '../src/agent/capabilities.ts';
import { CALLABLE_CAPABILITIES, capabilityCatalog } from '../src/agent/capabilities.ts';
import { ExamSessions } from '../src/state/examSessions.ts';
import { AgentTaskController } from '../src/agent/orchestrator.ts';
import { isExplicitConfirmation } from '../src/agent/orchestrator.ts';
import { confirmationBinding, confirmationValid, actionScope } from '../src/agent/confirmation.ts';

function baseRaw(overrides = {}) {
  return {
    workspaceId: null,
    screen: 'start',
    activeModal: null,
    sidebarCollapsed: false,
    activeJob: null,
    examRevision: null,
    examId: null,
    contentHash: null,
    selectedQuestion: null,
    questions: [],
    viewMode: 'paper',
    preview: null,
    approved: false,
    setup: { status: 'closed', selectedFormatId: null, prompt: '', formats: [] },
    pendingConfirmation: null,
    activeTask: null,
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

test('explicit wrong target and reused action ID with changed payload never dispatch', async () => {
  const tracker=new UiContextTracker(); let calls=0;
  const capture=()=>tracker.capture(baseRaw({workspaceId:'w',screen:'workspace'}));
  const executor=new UiActionExecutor(capture,{'ui.sidebar.set_collapsed':()=>{calls++;}});
  const action={kind:'propose_ui_action',text:'test',actionId:'scope',capabilityId:'ui.sidebar.set_collapsed',params:{collapsed:true},target:{workspaceId:'other'},expectedStateVersion:1};
  assert.equal((await executor.execute(action)).errorCode,'TARGET_CHANGED');
  assert.equal((await executor.execute({...action,params:{collapsed:false}})).errorCode,'ACTION_ID_CONFLICT');
  assert.equal(calls,0);
});

test('cancellation while awaiting a handler prevents the next dispatch', async () => {
  let release;
  const controller = new AgentTaskController();
  const tracker = new UiContextTracker();
  let raw = baseRaw();
  const capture = () => tracker.capture(raw);
  let calls=0;
  const executor = new UiActionExecutor(capture, {'ui.sidebar.set_collapsed': async p => { calls++; await new Promise(r => {release=r;}); raw={...raw,sidebarCollapsed:p.collapsed}; }});
  const proposal={kind:'propose_ui_action',text:'toggle',actionId:'cancel-1',capabilityId:'ui.sidebar.set_collapsed',expectedStateVersion:1,params:{collapsed:true},target:{}};
  const run=controller.execute('test',null,[proposal,{...proposal,actionId:'cancel-2',params:{collapsed:false}}],executor,capture);
  const duplicate=executor.execute(proposal);
  controller.cancel(); release();
  const result=await run;
  assert.equal(result.task.taskStatus,'cancelled');
  assert.equal((await duplicate).duplicate,true);
  assert.equal(calls,1);
});

test('answer-view contract is published and executor observes the review transition', async () => {
  let raw = baseRaw({ workspaceId: 'w', screen: 'workspace', examId: 'e', examRevision: 1 });
  const tracker = new UiContextTracker();
  const capture = () => tracker.capture(raw);
  assert.deepEqual(CALLABLE_CAPABILITIES['ui.exam.view_mode'].parameterSchema.mode, ['paper','review','pdf']);
  const executor = new UiActionExecutor(capture, { 'ui.exam.view_mode': p => { raw = { ...raw, viewMode: p.mode }; } });
  const result = await executor.execute({ kind: 'propose_ui_action', text: 'answers', actionId: 'review', capabilityId: 'ui.exam.view_mode', expectedStateVersion: capture().stateVersion, params: { mode: 'review' }, target: {} });
  assert.equal(result.status, 'success');
  assert.equal(raw.viewMode, 'review');
  assert.equal(capabilityCatalog(baseRaw()).find(c => c.id === 'ui.exam.view_mode').availability, 'SUPPORTED_BUT_UNAVAILABLE_NOW');
});

test('approval cannot execute without a matching revision-bound confirmation', () => {
  const raw = baseRaw({ workspaceId: 'w', examId: 'e', examRevision: 2, contentHash: 'h', preview: { status: 'ready', revision: 2, opened: true } });
  const action = CALLABLE_CAPABILITIES['exam.approve'];
  assert.equal(action.validate({}, raw), 'CONFIRMATION_REQUIRED');
  raw.pendingConfirmation = { id: 'c', kind: 'ui_action', createdAt: new Date().toISOString(), binding: confirmationBinding(raw,'ui_action'), capabilityId: 'exam.approve', workspaceId: 'w', revision: 2, contentHash: 'h', params: {} };
  assert.equal(action.validate({ confirmationId: 'c' }, raw), null);
  assert.equal(action.validate({ confirmationId: 'c' }, { ...raw, examRevision: 3 }), 'CONFIRMATION_REQUIRED');
});

test('confirmation binds the actual draft, expires, and accepts Vietnamese consent', () => {
  const ctx = baseRaw({ workspaceId:'w', setup:{status:'ready',selectedFormatId:'thpt-math',prompt:'A',formats:[]} });
  ctx.pendingConfirmation = {id:'c',kind:'generation',workspaceId:'w',createdAt:new Date().toISOString(),binding:confirmationBinding(ctx,'generation')};
  assert.equal(confirmationValid(ctx),true);
  assert.equal(confirmationValid({...ctx,setup:{...ctx.setup,prompt:'B'}}),false);
  assert.equal(confirmationValid({...ctx,pendingConfirmation:{...ctx.pendingConfirmation,createdAt:'2000-01-01T00:00:00Z'}}),false);
  assert.equal(isExplicitConfirmation('đồng ý'),true);
  assert.equal(isExplicitConfirmation('không đồng ý'),false);
  assert.equal(actionScope({...ctx,activeJob:{id:'j',percent:10}}),actionScope({...ctx,activeJob:{id:'j',percent:80}}));
});

test('task controller rebases every dependent step on fresh UI state and records receipts', async () => {
  const tracker = new UiContextTracker();
  let raw = baseRaw();
  const context = () => tracker.capture(raw);
  const executor = new UiActionExecutor(context, {
    'ui.session.create': () => {
      raw = baseRaw({ workspaceId: 'workspace-1', screen: 'workspace', sessions: [{ id: 'workspace-1', title: 'New', status: 'draft', createdAt: 'now' }] });
      return { workspaceId: 'workspace-1' };
    },
    'ui.exam.open_setup': () => { raw = { ...raw, activeModal: 'exam_setup' }; },
  });
  const proposals = [
    { kind: 'propose_ui_action', text: 'create', actionId: 'task-1', capabilityId: 'ui.session.create', expectedStateVersion: 1, params: { mode: 'custom' }, target: {} },
    { kind: 'propose_ui_action', text: 'setup', actionId: 'task-2', capabilityId: 'ui.exam.open_setup', expectedStateVersion: 1, params: {}, target: {} },
  ];
  const result = await new AgentTaskController().execute('create and configure', null, proposals, executor, context);
  assert.deepEqual(result.receipts.map(item => item.status), ['success', 'success']);
  assert.equal(result.task.taskStatus, 'completed');
  assert.equal(result.task.completedSteps.length, 2);
  assert.ok(result.receipts[1].observedStateVersion > result.receipts[0].observedStateVersion);
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

test('approved deferred note uses existing single-question regeneration and observes revision', async () => {
  let progress;
  let revision = 1;
  let regenerateCalls = 0;
  const service = {
    async startGeneration() { return { jobId: 'job-revision' }; },
    onProgress(_id, callback) { progress = callback; return () => {}; },
    async getExamPackage() {
      return { examId: 'exam-1', title: 'Exam', subject: 'Math', durationMinutes: 90,
        questions: [{ id: 1, stableId: 'q-stable', examRevision: revision }], revision, contentHash: String(revision).repeat(64), approved: false };
    },
    async regenerateQuestion(_jobId, questionId, instruction, expectedRevision) {
      assert.equal(questionId, 1); assert.equal(instruction, 'Easier'); assert.equal(expectedRevision, 1);
      regenerateCalls++; revision++; return { id: 1, stableId: 'q-stable', examRevision: revision };
    },
  };
  const store = new ExamSessions(service);
  const id = store.create('custom');
  await store.generate(id, { subject: 'Math', grade: 12, examType: 'THPT_STANDARD', durationMinutes: 90, itemCount: 1, prompt: 'test', uploadedFiles: [] });
  const note = store.addNote(id, { targetQuestion: 1, requestedChange: 'Easier', teacherText: 'Make it easier' });
  progress({ status: 'completed', stage: 5, percent: 100, completedItems: 1, totalItems: 1 });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(store.approveNote(id, note.id).status, 'approved');
  const result = await store.applyNote(id, note.id);
  assert.equal(result.revision, 2);
  assert.equal(regenerateCalls, 1);
  assert.equal(store.getSnapshot()[0].agentNotes[0].status, 'applied');
  store.dispose();
});
