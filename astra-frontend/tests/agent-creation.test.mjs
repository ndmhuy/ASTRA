import { test } from 'node:test';
import assert from 'node:assert/strict';
import formats from '../../eval/agent-semantic/local-catalog.fixture.json' with { type: 'json' };
import { catalogMeaning } from '../src/agent/local.ts';
import { examCreation, needsNewExamWorkspace } from '../src/agent/creation.ts';
import { parseFrame, resolveSemantic } from '../src/agent/semantics.ts';
import { resolveIntake } from '../src/agent/knowledge.ts';

const semantic = (goals, rest = {}) => parseFrame({ schemaVersion: 'astra-semantic-v1', dialogueAct: 'REQUEST', goals, ...rest });

test('ordinary creation requests resolve subject and family from compositional grammar', () => {
  for (const [message, subject, format] of [
    ['soạn đề tiếng anh THPT cho tao', 'Tiếng Anh', 'thpt-english'],
    ['tạo đề toán thpt mới', 'Toán Học', 'thpt-math'],
    ['Em ơi, soạn một đề THPT môn Hóa giúp cô nhé', 'Hóa Học', 'thpt-chemistry'],
    ['Vui lòng ra đề thi vật lý tốt nghiệp cho tôi', 'Vật Lý', 'thpt-physics'],
    ['tao de moi mon sinh thpt di', 'Sinh Học', 'thpt-biology'],
    ['Cô muốn soạn đề sử THPT', 'Lịch Sử', 'thpt-history'],
  ]) {
    const local = catalogMeaning(message, formats);
    assert.equal(local?.intake?.subject, subject, message);
    assert.equal(local.intake.family, 'thpt');
    const resolved = resolveIntake(local.intake, message, undefined, formats, 'source');
    assert.equal(resolved.intent?.args.format, format, message);
  }
  // Unparsed constraints must not disappear into a default-sized exam.
  assert.equal(catalogMeaning('Tạo đề tiếng Anh THPT 15 câu, 45 phút', formats), undefined);
  assert.equal(catalogMeaning('Soạn đề Sinh THPT chuyên đề di truyền', formats), undefined);
});

test('fresh creation targets preserve completed/paused/running work and never inherit old intake', () => {
  const current = { status: 'complete', jobId: 'old-job', messages: [], intake: { subject: 'Tiếng Anh' } };
  assert.equal(needsNewExamWorkspace(current, 'tạo đề toán thpt mới'), true);
  assert.equal(needsNewExamWorkspace(current, 'soạn đề tiếng Anh THPT cho tao'), true);
  assert.equal(needsNewExamWorkspace({ ...current, status: 'draft', generationStopped: true }, 'Tạo đề Toán THPT mới'), true);
  assert.equal(needsNewExamWorkspace({ ...current, status: 'generating' }, 'Tạo đề Toán THPT mới'), true);
  assert.equal(needsNewExamWorkspace({ ...current, status: 'draft', generationStopped: true }, 'Tiếp tục đề'), false);
  assert.equal(needsNewExamWorkspace({ status: 'draft', jobId: null, messages: [] }, 'Tạo đề mới'), false);
  assert.equal(needsNewExamWorkspace(current, 'Xem đáp án câu 2'), false);
  assert.equal(needsNewExamWorkspace({ ...current, status: 'draft' }, 'Tạo đề Sử THPT chuyên đề Đổi mới'), false);
  for (const message of ['Đừng tạo đề mới', 'Nếu tạo đề Toán THPT mới thì sao?', '“Tạo đề mới”', 'Tạo đề mới được không?', 'Tạo đề mới rồi xóa đề cũ']) {
    assert.equal(examCreation(message), undefined, message);
    assert.equal(needsNewExamWorkspace(current, message), false, message);
  }
});

test('compatible preparation/configuration/generation goals become one intake with every slot', () => {
  const result = resolveSemantic(semantic([
    { goal: 'OPEN_CONFIGURATION' },
    { goal: 'PREPARE_EXAM', parameters: { family: 'thpt', subject: 'Tiếng Anh' } },
    { goal: 'REQUEST_GENERATION', parameters: { family: 'thpt', topic: 'ngữ pháp', count: 40 } },
  ]));
  assert.equal(result.text, undefined);
  assert.equal(result.requestGeneration, true);
  assert.deepEqual(result.decision.intake, { mode: 'request', family: 'thpt', subject: 'Tiếng Anh', topic: 'ngữ pháp', count: 40 });
  const synonyms = resolveSemantic(semantic([
    { goal: 'PREPARE_EXAM', parameters: { subject: 'Toán' } },
    { goal: 'REQUEST_GENERATION', parameters: { subject: 'Toán Học' } },
  ]));
  assert.ok(synonyms.decision.intake);
});

test('conflicting exam goals, unrelated business operations and whole-turn guards stay blocked', () => {
  for (const field of ['subject', 'count', 'family']) {
    const pairs = { subject: ['Toán Học', 'Tiếng Anh'], count: [22, 40], family: ['thpt', 'vact'] };
    assert.equal(resolveSemantic(semantic([
      { goal: 'PREPARE_EXAM', parameters: { [field]: pairs[field][0] } },
      { goal: 'REQUEST_GENERATION', parameters: { [field]: pairs[field][1] } },
    ])).decision, undefined);
  }
  const goals = [{ goal: 'PREPARE_EXAM', parameters: { family: 'thpt' } }, { goal: 'REQUEST_GENERATION', parameters: { subject: 'Tiếng Anh' } }];
  for (const guard of ['NO_EXECUTION', 'NEGATED', 'CONDITIONAL', 'CONTRADICTORY']) {
    assert.equal(resolveSemantic(semantic(goals, { constraints: [guard] })).decision, undefined);
  }
  const setup = resolveSemantic(semantic(goals, { constraints: ['NO_GENERATION'] }));
  assert.equal(setup.setupOnly, true);
  assert.equal(setup.requestGeneration, false);
  const question = resolveSemantic(semantic(goals, { dialogueAct: 'QUESTION' }));
  assert.equal(question.decision.intake.mode, 'structure');
  assert.equal(question.requestGeneration, false);
  assert.equal(resolveSemantic(semantic([...goals, { goal: 'EXPORT_EXAM', parameters: { format: 'pdf' } }])).decision, undefined);
});
