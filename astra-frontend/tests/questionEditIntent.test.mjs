import assert from 'node:assert/strict';
import test from 'node:test';
import { clarifyQuestionEdit, questionEditIntent } from '../src/utils/questionEditIntent.ts';

test('targets the specified THPT section and clarifies duplicate question numbers', () => {
  const questions = [{ id: 1, stableId: 'P1-1', part: 'P1' }, { id: 17, stableId: 'P3-1', part: 'P3' }];
  assert.equal(questionEditIntent('Sửa câu 1, nêu rõ đơn vị.', questions).kind, 'clarify');
  assert.equal(questionEditIntent('Sửa Phần III, câu 1: làm tròn đến hàng phần trăm.', questions).question.id, 17);
  assert.equal(questionEditIntent('Sửa câu 1 ở phần 3 cho rõ.', questions).question.id, 17);
  assert.equal(questionEditIntent('Tạo lại P1-1.', questions).question.id, 1);
  assert.equal(questionEditIntent('Đừng sửa câu 1 Phần III.', questions).kind, 'chat');
  assert.equal(clarifyQuestionEdit('Phần III', 'Sửa câu 1, nêu rõ đơn vị.', questions).question.id, 17);
  assert.equal(clarifyQuestionEdit('Vì sao vậy?', 'Sửa câu 1.', questions).kind, 'chat');
});

test('uses V-ACT numbering and never applies a multi-question request', () => {
  const questions = [{ id: 97, stableId: 'q97' }, { id: 98, stableId: 'q98' }];
  assert.equal(questionEditIntent('Viết lại câu 97 cho rõ dữ kiện.', questions).question.id, 97);
  assert.equal(questionEditIntent('Sửa câu 97, không đổi dữ liệu.', questions).question.id, 97);
  assert.equal(questionEditIntent('Sửa câu 97, 98.', questions).kind, 'clarify');
  assert.equal(questionEditIntent('Sửa câu này.', questions).kind, 'clarify');
  assert.equal(questionEditIntent('Sửa câu 121.', questions).kind, 'clarify');
  assert.equal(questionEditIntent('Đối với câu 97, vì sao đáp án là B?', questions).kind, 'chat');
});
