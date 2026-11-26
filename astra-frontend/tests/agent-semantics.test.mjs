import test from 'node:test';
import assert from 'node:assert/strict';
import { parseFrame, resolveSemantic, contextualSubject } from '../src/agent/semantics.ts';
import { resolveIntake } from '../src/agent/knowledge.ts';
import { execute } from '../src/agent/recipes.ts';

const math = { id: 'thpt-math', version: '1', displayName: 'Toán THPT', subjects: ['Toán Học'],
  available: true, grades: [12], examType: 'THPT_STANDARD', durationMinutes: 90, totalQuestions: 22, sections: [] };
const frame = (goals, extra = {}) => parseFrame({ schemaVersion: 'astra-semantic-v1', dialogueAct: 'REQUEST', goals, ...extra });

test('THPT semantics pause for catalog subject, then select actual UI format without generation', () => {
  const semantic = frame([{ goal: 'PREPARE_EXAM', parameters: { family: 'thpt' } }]);
  const workflow = resolveSemantic(semantic);
  const initial = resolveIntake(workflow.decision.intake, 'Chuẩn bị bài thi tốt nghiệp', undefined, [math], 'first', true);
  assert.equal(initial.draft.missing, 'subject');
  assert.equal(initial.draft.family, 'thpt');
  const local = contextualSubject('Toan.', initial.draft, [math]);
  const next = resolveIntake(local.intake, 'Toan.', initial.draft, [math], 'second');
  assert.equal(next.intent.id, 'SELECT_FORMAT');
  assert.equal(next.intent.args.format, math.id);
  const unavailable = contextualSubject('Hóa', initial.draft, [math]);
  assert.match(resolveIntake(unavailable.intake, 'Hóa', initial.draft, [math], 'third').text, /chưa hỗ trợ môn Hóa/);
  assert.equal(contextualSubject('Toán', undefined, [math]), undefined);
});

test('meaning without familiar family words uses semantic family, never an inferred subject', () => {
  const decision = resolveSemantic(frame([{ goal: 'PREPARE_EXAM', parameters: { family: 'thpt' } }])).decision;
  const result = resolveIntake(decision.intake, 'Theo dạng vừa đề cập', undefined, [math], 'id', true);
  assert.equal(result.draft.missing, 'subject');
});

test('runtime catalog additions resolve without changing semantic or routing code', () => {
  const chemistry = { ...math, id: 'thpt-chemistry', displayName: 'Hóa THPT', subjects: ['Hóa Học'] };
  const initial = resolveIntake({ mode: 'request', family: 'thpt' }, 'THPT', undefined, [math, chemistry], 'id', true);
  assert.equal(initial.draft.missing, 'subject');
  const local = contextualSubject('Hóa', initial.draft, [math, chemistry]);
  const selected = resolveIntake(local.intake, 'Hóa', initial.draft, [math, chemistry], 'next');
  assert.equal(selected.intent.args.format, 'thpt-chemistry');
});

test('whole-turn constraints prevent every composed effect and corrections revoke confirmation', () => {
  const goals = [{ goal: 'OPEN_WORKSPACE' }, { goal: 'EXPORT_EXAM', parameters: { format: 'pdf' } }];
  for (const constraint of ['NO_EXECUTION', 'CONDITIONAL', 'NEGATED', 'CONTRADICTORY']) {
    const result = resolveSemantic(frame(goals, { constraints: [constraint], dialogueAct: 'CORRECT' }));
    assert.equal(result.decision, undefined);
    assert.equal(result.invalidateConfirmation, true);
  }
  assert.equal(resolveSemantic(frame([], { dialogueAct: 'CONFIRM' })).decision, undefined);
  assert.equal(resolveSemantic(frame([], { dialogueAct: 'CANCEL' })).cancel, true);
});

test('questions and unsupported requests never become nearest executable operations', () => {
  assert.equal(resolveSemantic(frame([{ goal: 'OPEN_CONFIGURATION' }], { dialogueAct: 'QUESTION' })).decision, undefined);
  assert.equal(resolveSemantic(frame([{ goal: 'OPEN_CONFIGURATION' }], { dialogueAct: 'UNSUPPORTED' })).decision, undefined);
  assert.equal(resolveSemantic(frame([{ goal: 'INSPECT_QUESTION', reference: 'previous' }])).decision, undefined);
  assert.throws(() => frame([{ goal: 'PREPARE_EXAM', parameters: { workspaceId: 'invented' } }]));
  assert.equal(parseFrame({ schemaVersion: 'astra-semantic-v1', dialogueAct: 'CONVERSATION', title: [] }).title, undefined);
});

test('composition follows observed receipts and stops dependent work after failure', async () => {
  const workflow = resolveSemantic(frame([{ goal: 'OPEN_WORKSPACE' },
    { goal: 'INSPECT_QUESTION', parameters: { number: 5, view: 'review' } }]));
  const seen = [];
  const runtime = { binding: () => 'fresh', dispatch: intent => { seen.push(intent.id); return { status: 'failed', text: 'No matching workspace' }; } };
  const receipts = await execute(workflow.decision.intents, runtime, 'fresh', () => true);
  assert.deepEqual(seen, ['OPEN_SESSION']);
  assert.equal(receipts.length, 1);
});

test('missing parameters pause, and explicit no-generation setup never asks to start', () => {
  assert.equal(resolveSemantic(frame([{ goal: 'EXPORT_EXAM' }])).decision, undefined);
  const setup = resolveSemantic(frame([{ goal: 'PREPARE_EXAM', parameters: { family: 'vact' } }], { dialogueAct: 'CORRECT', constraints: ['NO_GENERATION'] }));
  assert.equal(setup.setupOnly, true);
  assert.equal(setup.requestGeneration, false);
  assert.equal(setup.invalidateConfirmation, true);
});

test('a pending UI operation has a bounded observation deadline and stops dependencies', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const dispatched = [];
  const pending = execute([{ id: 'OPEN_SETUP', args: {} }, { id: 'HOME', args: {} }], {
    binding: () => 'same', dispatch: intent => { dispatched.push(intent.id); return new Promise(() => {}); },
  }, 'same', () => true);
  t.mock.timers.tick(15000);
  const receipts = await pending;
  assert.equal(receipts[0].status, 'unknown');
  assert.deepEqual(dispatched, ['OPEN_SETUP']);
});
