import assert from 'node:assert/strict';
import test from 'node:test';
import { adaptStudentPaper } from '../src/services/contractPaper.ts';

test('publishes canonical questions and keeps teacher keys bound to the revision', () => {
  const text = value => [{ type: 'text', text: value }];
  const choices = { A: text('first'), B: text('second'), C: text('third'), D: text('fourth') };
  const paper = {
    schemaVersion: 'astra-thpt-paper-v1', examId: 'exam-job', revision: 2, contentHash: 'hash',
    sections: [{ id: 'P1', items: [{
      id: 'p1-1', type: 'mcq', number: 1, choices, passageIds: ['e2'],
      stem: [{ type: 'paragraph', runs: [{ type: 'math', latex: 'x^2' }] },
        { type: 'figure', assetId: 'figure-p1-1', alt: 'Graph' }],
    }] }],
    passages: [{ id: 'e2', sectionId: 'P1', kind: 'cloze', questionRange: [1, 1],
      instructions: text('Read the passage.'),
      blocks: [{ type: 'paragraph', runs: [{ type: 'blank', label: '1' }] }],
    }],
    assets: [{ id: 'figure-p1-1', mimeType: 'application/pdf' }],
  };
  const pkg = { examId: 'job', revision: 2, contentHash: 'hash', studentPaper: paper,
    questions: [{ id: 42, stableId: 'P1-1', questionType: 'mcq', stem: 'legacy', key: 'B' }],
  };
  const adapted = adaptStudentPaper(pkg, '/api');
  assert.equal(adapted.questions[0].id, 42);
  assert.equal(adapted.questions[0].key, 'B');
  assert.equal(adapted.questions[0].stem, '$x^2$');
  assert.equal(adapted.questions[0].choices.B, 'second');
  assert.equal(adapted.questions[0].figures[0].url, '/api/exams/job/assets/figure-p1-1');
  assert.equal(adapted.passages[0].text, '(1) ____');
  assert.throws(() => adaptStudentPaper({ ...pkg, revision: 3 }, '/api'), /phiên bản/);
});
