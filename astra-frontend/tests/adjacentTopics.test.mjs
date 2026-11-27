import assert from 'node:assert/strict';
import test from 'node:test';
import { listAdjacentTopics, matchAdjacentTopic } from '../src/agent/knowledge.ts';

test('listAdjacentTopics exposes hardcoded allowlisted topics', () => {
  const ids = listAdjacentTopics().map(item => item.id).sort();
  assert.deepEqual(ids, ['act', 'ielts', 'sat', 'toefl', 'toeic']);
});

test('matchAdjacentTopic recognizes SAT, IELTS, TOEIC, TOEFL, ACT and rejects unknown topics', () => {
  assert.equal(matchAdjacentTopic('Soạn đề SAT Math 10 câu giúp tôi')?.id, 'sat');
  assert.equal(matchAdjacentTopic('Tìm mạng cho IELTS Academic Reading')?.id, 'ielts');
  assert.equal(matchAdjacentTopic('Làm bài TOEIC Part 5 10 câu')?.id, 'toeic');
  assert.equal(matchAdjacentTopic('Đề TOEFL iBT Reading')?.id, 'toefl');
  assert.equal(matchAdjacentTopic('Luyện tập ACT Math 10 câu')?.id, 'act');
  assert.equal(matchAdjacentTopic('Soạn đề Toán tốt nghiệp THPT'), undefined);
  assert.equal(matchAdjacentTopic('Tìm đề thi Olympic Sinh học quốc tế'), undefined);
});
