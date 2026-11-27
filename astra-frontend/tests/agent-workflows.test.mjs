import { test } from 'node:test';
import assert from 'node:assert/strict';
import { prepareParams } from '../src/agent/intake.ts';
import { reconcileNotes } from '../src/agent/notes.ts';
import { resolveQuestion } from '../src/agent/examActions.ts';

const math = {
  id: 'thpt-math', version: '1', displayName: 'Toán THPT', subjects: ['Toán Học'],
  grades: [12], examType: 'THPT_STANDARD', durationMinutes: 90, totalQuestions: 22,
};

test('intake preserves locked constraints and only confirmed academic slots', () => {
  assert.ok(prepareParams(math, {}, 'THPT 15 câu, 45 phút').error);
  assert.ok(prepareParams(math, { topic: 'tích phân' }, 'Tạo đề chuyên đề đạo hàm').error);
  const result = prepareParams(math, { topic: 'đạo hàm' }, 'Tạo đề chuyên đề đạo hàm');
  assert.equal(result.params.prompt, 'Tạo đề Toán THPT\nChuyên đề: đạo hàm');
  assert.deepEqual(result.params.uploadedFiles, []);
});

test('ambiguous repeated section numbers stay unresolved', () => {
  const questions = [
    { id: 3, stableId: 'P1-03', part: 'P1', examRevision: 2 },
    { id: 15, stableId: 'P2-03', part: 'P2', examRevision: 2 },
  ];
  const session = { questions, package: { revision: 2 } };
  assert.equal(resolveQuestion(session, { number: 3 }), undefined);
  assert.equal(resolveQuestion(session, { number: 3, part: 'II' }).id, 15);
  assert.equal(resolveQuestion({ ...session, package: { revision: 3 } }, { number: 3, part: 'II' }), undefined);
  const note = { jobId: 'job', number: 3, status: 'recorded' };
  const result = reconcileNotes([note, { ...note, part: 'P2' }], 'job', questions);
  assert.equal(result[0].status, 'unresolved');
  assert.equal(result[1].stableId, 'P2-03');
});
