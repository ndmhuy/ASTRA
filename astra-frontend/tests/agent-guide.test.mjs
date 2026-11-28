import assert from 'node:assert/strict';
import test from 'node:test';
import routes from '../../src/exam_baseline/resources/agent/local-utterances.json' with { type: 'json' };
import handbook from '../../src/exam_baseline/resources/agent/app-guide.json' with { type: 'json' };
import formats from '../../eval/agent-semantic/local-catalog.fixture.json' with { type: 'json' };
import { requestText } from '../src/agent/local.ts';
import { continueGuide, startGuide } from '../src/agent/guide.ts';
import { meaning, planMeaning, understandLocal } from '../src/agent/intelligence.ts';

test('local phrase data is unique and resolves every entry to its registered meaning', () => {
  const seen = new Set();
  for (const route of routes.routes) {
    for (const example of route.examples) {
      const phrase = requestText(example);
      assert.ok(!seen.has(phrase), example);
      seen.add(phrase);
      const reading = understandLocal(example, { formats });
      assert.notEqual(reading.kind, 'defer', example);
      assert.deepEqual(reading.frame, meaning(route.goal, route.parameters, route.act), example);
    }
  }
  assert.ok(seen.size >= 120);
});

test('guide questions return instructions and never submit a request', () => {
  for (const [topic, card] of Object.entries(handbook.topics)) {
    for (const example of card.examples) {
      const result = understandLocal(example, { formats });
      assert.notEqual(result.kind, 'defer', example);
      assert.equal(planMeaning(result.frame).kind, 'guide', example);
      assert.equal(planMeaning(result.frame).topic, topic, example);
    }
  }
  assert.equal(understandLocal('Xem đề này và duyệt luôn', { formats }).kind, 'defer');
  assert.equal(understandLocal('Đừng mở đề thi', { formats }).kind, 'defer');
  assert.equal(understandLocal('Cách tạo đề hôm trước mà tôi làm dở', { formats }).kind, 'defer');
  assert.equal(planMeaning(meaning('REQUEST_GENERATION', {}, 'GUIDANCE')).kind, 'text');
});

test('step-by-step guide offers available templates and waits for explicit progress', () => {
  const live = formats.filter(format => format.available);
  const guide = startGuide('create', live);
  assert.equal(guide.progress.stage, 'choose');
  assert.ok(live.every(format => guide.text.includes(format.displayName)));
  const english = live.find(format => format.id === 'thpt-english');
  const selected = continueGuide(guide.progress, 'Môn Tiếng Anh', live);
  assert.equal(selected.progress.formatId, english.id);
  assert.equal(continueGuide(guide.progress, 'Tao muốn chọn mẫu Tiếng Anh', live).progress.formatId, english.id);
  assert.match(selected.text, new RegExp(`${english.totalQuestions} câu, ${english.durationMinutes} phút`));
  assert.equal(continueGuide(selected.progress, 'ok', live), undefined);
  const details = continueGuide(selected.progress, 'Mình đã chọn mẫu rồi', live);
  assert.match(details.text, /Điền chủ đề/);
  const start = continueGuide(details.progress, 'Dùng mẫu mặc định', live);
  assert.match(start.text, /bấm Tạo đề thi/);
  assert.equal(start.progress.stage, 'start');
  assert.match(startGuide('create', live, 'vật lý').text, /Vật Lý THPT/);
  assert.match(startGuide('create', live.filter(format => format !== english), 'Tiếng Anh').text, /chưa tìm thấy mẫu/);
});
