import assert from 'node:assert/strict';
import test from 'node:test';
import { MockExamService } from '../src/services/examService.ts';
import {
  buildQuestionReviewSummary,
  formatQuestionLabel,
  getQuestionReviewState,
} from '../src/utils/questionReview.ts';

function sampleQuestion(overrides = {}) {
  return {
    id: 1,
    stableId: 'P1-1',
    examRevision: 1,
    part: 'P1',
    questionType: 'mcq',
    stem: 'Câu mẫu',
    choices: { A: '1', B: '2', C: '3', D: '4' },
    key: 'A',
    explanation: 'Giải thích',
    level: 'NHAN_BIET',
    topic: 'Toán',
    status: 'VERIFIED',
    answerCheck: 'matched',
    writerKey: 'A',
    solverKey: 'A',
    questionApproval: null,
    ...overrides,
  };
}

test('formatQuestionLabel maps THPT stable IDs and V-ACT IDs cleanly', () => {
  assert.equal(formatQuestionLabel(sampleQuestion({ id: 22, stableId: 'P3-3' })), 'Câu III.3');
  assert.equal(formatQuestionLabel(sampleQuestion({ id: 13, stableId: 'P2-1' })), 'Câu II.1');
  assert.equal(formatQuestionLabel(sampleQuestion({ id: 5, stableId: 'q42' })), 'Câu 42');
  assert.equal(formatQuestionLabel(sampleQuestion({ id: 4, stableId: undefined }), 3), 'Câu 4');
});

test('buildQuestionReviewSummary deduplicates per question and counts RAG/visual notes separately', () => {
  const questions = [
    sampleQuestion({ id: 1, stableId: 'P1-1', answerCheck: 'matched', questionApproval: null }),
    sampleQuestion({
      id: 2,
      stableId: 'P2-1',
      questionType: 'true_false',
      answerCheck: 'mismatched',
      mismatchedStatements: ['b'],
      writerKey: 'Đ / Đ / S / Đ',
      solverKey: 'a) Đúng, b) Sai, c) Sai, d) Đúng',
    }),
    sampleQuestion({
      id: 3,
      stableId: 'P3-3',
      questionType: 'short_answer',
      answerCheck: 'needs_recheck',
      writerKey: '0,67',
      solverKey: '2/3',
      auditNotes: 'Kiểm tra lại yêu cầu làm tròn và số chữ số của đáp án.',
    }),
  ];

  const summary = buildQuestionReviewSummary(
    questions,
    [
      { questionId: 'P2-1', code: 'rag_low', message: 'Thiếu câu mẫu RAG cùng mức.' },
      { questionId: 'P1-1', code: 'rag_note', message: 'Lưu ý tham khảo.' },
    ],
    [{ questionId: 'P2-1', code: 'missing_illustration_request' }]
  );

  // One mismatched + one needs_recheck (even with extra RAG + visual notes) = 2 distinct questions.
  assert.equal(summary.answerIssueItems.length, 2);
  assert.deepEqual(
    summary.answerIssueItems.map(item => item.label),
    ['Câu II.1', 'Câu III.3']
  );
  // Matched without human approval remains unapproved until confirmed.
  assert.equal(summary.unapprovedMatchedItems.length, 1);
  assert.equal(getQuestionReviewState(questions[0]).kind, 'matched_unapproved');
  // P1-1 and P2-1 both have source/visual notes -> counted separately as 2 distinct questions.
  assert.equal(summary.sourceOrVisualQuestionCount, 2);
});

test('MockExamService.approveQuestion requires reason when unverified and clears on edit', async () => {
  const service = new MockExamService();
  const { jobId } = await service.startGeneration({
    subject: 'Toán Học',
    grade: 12,
    examType: 'THPT_STANDARD',
    durationMinutes: 90,
    itemCount: 22,
    prompt: 'Test',
    uploadedFiles: [],
  });

  const initial = await service.getExamPackage(jobId);
  const first = initial.questions[0];

  await assert.rejects(
    () => service.approveQuestion(jobId, first.id, initial.revision ?? 1, ''),
    /lý do xác nhận/i
  );

  const approvedPkg = await service.approveQuestion(
    jobId,
    first.id,
    initial.revision ?? 1,
    'Đã xác nhận đáp án thủ công.'
  );
  assert.equal(approvedPkg.questions[0].questionApproval?.reason, 'Đã xác nhận đáp án thủ công.');
  assert.equal(getQuestionReviewState(approvedPkg.questions[0]).kind, 'approved');

  await service.updateQuestion(jobId, { ...first, stem: 'Nội dung mới' });
  const afterEdit = await service.getExamPackage(jobId);
  assert.equal(afterEdit.questions[0].questionApproval, null);
  assert.equal(afterEdit.questions[0].answerCheck, 'needs_recheck');
});
