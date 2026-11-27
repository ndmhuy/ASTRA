import assert from 'node:assert/strict';
import { test } from 'node:test';
import thpt from '../../src/exam_baseline/resources/exam_formats/thpt_math_v1.json' with { type: 'json' };
import vact from '../../src/exam_baseline/resources/exam_formats/vact_v1.json' with { type: 'json' };
import { guidanceFor, resolveIntake } from '../src/agent/knowledge.ts';
import { fastRoute } from '../src/agent/recipes.ts';
import { parseDecision, VERSION } from '../src/agent/contracts.ts';

const catalog = [thpt, vact];
const resolve = (message, proposal = {}, previous, formats = catalog) =>
  resolveIntake({ mode: 'request', ...proposal }, message, previous, formats, message);

test('partial intake retains family and catalog subject, then prepares a grounded topic', () => {
  const initial = resolve('Tạo đề thi thử tốt nghiệp');
  assert.equal(initial.draft.family, 'thpt');
  assert.equal(initial.draft.missing, 'subject');
  const subject = resolve('Toán', {}, initial.draft);
  assert.deepEqual(subject.intent, { id: 'SELECT_FORMAT', args: { format: 'thpt-math', details: true } });
  assert.equal(subject.draft.subject, 'Toán Học');
  const focus = resolve('Cô muốn tập trung vào đạo hàm và tích phân', { topic: 'đạo hàm và tích phân' }, subject.draft);
  assert.equal(focus.intent.id, 'PREPARE_GENERATION');
  assert.equal(focus.draft.sourceIds.length, 3);
  const correction = resolve('Thôi đổi sang V-ACT', { family: 'vact' }, focus.draft);
  assert.equal(correction.draft.topic, undefined);
  assert.deepEqual(correction.draft.sourceIds, ['Thôi đổi sang V-ACT']);
  assert.equal(correction.intent.id, 'SELECT_FORMAT');
});

test('catalog drives capability, subject rejection, locks and read-only structure', () => {
  assert.match(resolve('Tạo đề THPT môn Hóa', { subject: 'Toán Học' }).text, /Hóa.*Toán/);
  assert.equal(fastRoute('Tạo đề THPT').intake.family, 'thpt');
  assert.match(resolve('Tạo đề thi thử', { family: 'thpt' }).text, /Toán THPT.*V-ACT/);
  assert.equal(resolve('Tạo đề thi thử tốt nghiệp', { family: 'vact' }).draft.missing, 'subject');
  const conflict = resolve('Tạo đề Toán THPT 15 câu', { subject: 'Toán Học' });
  assert.match(conflict.text, /22 câu.*cố định.*Đồng ý/);
  assert.equal(conflict.preset.id, thpt.id);
  assert.equal(conflict.draft.count, 15);
  assert.equal(conflict.intent, undefined);
  assert.equal(resolve('Tạo đề đánh giá năng lực ĐHQG-HCM').intent.args.format, 'vact');
  assert.match(resolve('Đề V-ACT có bao nhiêu câu?', { mode: 'structure' }).text, /120 câu/);
  assert.equal(resolve('Đừng tạo đề, chỉ xem cấu trúc', { mode: 'structure' }).intent, undefined);
  assert.match(resolve('Tôi cần random exam').text, /chưa có mẫu khả dụng/);
  assert.doesNotMatch(guidanceFor('start', [thpt, { ...vact, available: false }]), /V-ACT/);
  assert.match(resolve('Đề V-ACT có bao nhiêu câu?', { mode: 'structure' }, undefined, [thpt, { ...vact, available: false }]).text, /chưa có mẫu khả dụng/);
});

test('structured knowledge proposals cannot coexist with executable model intents', () => {
  const envelope = decision => ({ schemaVersion: VERSION, clientMessageId: 'id', decision });
  const guide = { kind: 'answer', intents: [], guidance: 'start', title: 'Hướng dẫn soạn đề' };
  assert.deepEqual(parseDecision(envelope(guide), 'id'), guide);
  assert.throws(() => parseDecision(envelope({ ...guide, kind: 'task', intents: [{ id: 'OPEN_SETUP', args: {} }] }), 'id'));
  assert.throws(() => parseDecision(envelope({ kind: 'answer', intents: [], intake: { mode: 'request', family: 'thpt', command: 'start' } }), 'id'));
});
