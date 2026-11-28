import test from 'node:test';
import assert from 'node:assert/strict';
import thptMath from '../../src/exam_baseline/resources/exam_formats/thpt_math_v1.json' with { type: 'json' };
import vact from '../../src/exam_baseline/resources/exam_formats/vact_v1.json' with { type: 'json' };
import { buildParamsFromDraft, extractExamDraft, recomputeDraftStatus } from '../src/agent/chatConfig.ts';

const thptGeo = {
  ...thptMath,
  id: 'thpt-geography',
  displayName: 'Địa Lý THPT',
  subjects: ['Địa Lý'],
  durationMinutes: 50,
  totalQuestions: 28,
};

const formats = [thptMath, thptGeo, vact];

test('extractExamDraft extracts subject, topic focus, and difficulty preferences for editable chat config', () => {
  const draft = extractExamDraft(
    'Toán THPT, 22 câu, ưu tiên Hàm số, tăng câu vận dụng',
    formats,
    'msg-1'
  );
  assert.ok(draft);
  assert.equal(draft.formatId, 'thpt-math');
  assert.equal(draft.subject, 'Toán Học');
  assert.equal(draft.topic, 'Hàm số');
  assert.equal(draft.difficulty, 'Tăng câu vận dụng');
  assert.equal(draft.hasMismatch, false);
  assert.deepEqual(draft.limitations, []);
  assert.deepEqual(draft.needsClarification, []);

  const params = buildParamsFromDraft({ ...draft, extraNotes: 'Giữ phần I cơ bản' }, formats, ['doc-1']);
  assert.ok(params);
  assert.equal(params.formatId, 'thpt-math');
  assert.match(params.prompt, /Hàm số/);
  assert.match(params.prompt, /Tăng câu vận dụng/);
  assert.match(params.prompt, /Giữ phần I cơ bản/);
  assert.deepEqual(params.uploadedFiles, ['doc-1']);
});

test('extractExamDraft surfaces fixed preset limitations clearly when requested count/time differs', () => {
  const geoDraft = extractExamDraft('đề Địa lý 67 câu, 90 phút', formats, 'msg-2');
  assert.ok(geoDraft);
  assert.equal(geoDraft.formatId, 'thpt-geography');
  assert.equal(geoDraft.hasMismatch, true);
  assert.equal(geoDraft.limitations.length, 1);
  assert.match(geoDraft.limitations[0], /67 câu/);
  assert.match(geoDraft.limitations[0], /28 câu/);
  assert.match(geoDraft.limitations[0], /90 phút/);
  assert.match(geoDraft.limitations[0], /50 phút/);
});

test('extractExamDraft flags missing subject while still noting fixed preset limits', () => {
  const bareDraft = extractExamDraft('đề 67 câu, 90 phút', formats, 'msg-3');
  assert.ok(bareDraft);
  assert.equal(bareDraft.formatId, undefined);
  assert.equal(bareDraft.needsClarification.length, 1);
  assert.equal(bareDraft.limitations.length, 1);
  assert.match(bareDraft.limitations[0], /67 câu, 90 phút/);

  const updated = recomputeDraftStatus({ ...bareDraft, formatId: 'thpt-math', topic: 'Tích phân' }, formats);
  assert.equal(updated.needsClarification.length, 0);
  assert.equal(updated.hasMismatch, true);
  assert.match(updated.applied.join(' '), /Tích phân/);
});
