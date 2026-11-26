import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { getChoiceGridClass } from '../src/utils/choiceLayout.ts';

test('getChoiceGridClass returns cols-4 only when all 4 choices are compact', () => {
  assert.equal(getChoiceGridClass({ A: '1', B: '2', C: '3', D: '4' }), 'cols-4');
  assert.equal(
    getChoiceGridClass({ A: '$x = 1$', B: '$x = 2$', C: '$x = -1$', D: '$x = 0$' }),
    'cols-4',
  );
  assert.equal(
    getChoiceGridClass({ A: 'Đáp án A', B: 'Đáp án B', C: 'Đáp án C', D: 'Đáp án D' }),
    'cols-4',
  );
  assert.equal(getChoiceGridClass(['12', '24', '36', '48']), 'cols-4');
});

test('getChoiceGridClass returns cols-2 for longer choices, newlines, or complex math (never 3+1)', () => {
  assert.equal(
    getChoiceGridClass({
      A: 'Hàm số đồng biến trên khoảng $(0; +\\infty)$',
      B: 'Hàm số nghịch biến trên $\\mathbb{R}$',
      C: 'Hàm số đạt cực đại tại $x = 1$',
      D: 'Hàm số có hai điểm cực trị',
    }),
    'cols-2',
  );
  assert.equal(
    getChoiceGridClass({
      A: '$\\frac{1}{2}$',
      B: '$\\frac{1}{3}$',
      C: '$\\frac{1}{4}$',
      D: '$\\frac{1}{5}$',
    }),
    'cols-2',
  );
  assert.equal(
    getChoiceGridClass({
      A: 'Dòng 1\nDòng 2',
      B: '2',
      C: '3',
      D: '4',
    }),
    'cols-2',
  );
  assert.equal(getChoiceGridClass({ A: '', B: '2', C: '3', D: '4' }), 'cols-2');
});

test('QuestionCard renders empty short-answer-cell spans instead of missing-glyph square character', () => {
  const questionCardPath = path.resolve(
    import.meta.dirname,
    '../src/components/Workspace/LiveCanvas/QuestionCard.tsx',
  );
  const source = fs.readFileSync(questionCardPath, 'utf8');
  assert.ok(!source.includes('\u25a1'), 'QuestionCard must not contain U+25A1 glyph');
  const cellMatches = source.match(/className="short-answer-cell"/g) || [];
  assert.equal(cellMatches.length, 4, 'short_answer should render 4 empty .short-answer-cell boxes');
});

test('atelier.css uses unified sans-serif fonts and symmetric 2/4-column choice grids', () => {
  const atelierPath = path.resolve(import.meta.dirname, '../src/styles/atelier.css');
  const css = fs.readFileSync(atelierPath, 'utf8');
  assert.ok(!css.includes('Newsreader'), 'atelier.css must not reference serif Newsreader');
  assert.ok(!css.includes('Times New Roman'), 'atelier.css must not reference Times New Roman');
  assert.ok(!/auto-fit,\s*minmax/.test(css), 'question-choices must not use auto-fit (prevents 3+1 rows)');
});
