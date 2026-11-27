import type { QuestionItem } from '../types/exam.ts';
import { fold } from './recipes.ts';

export function patchEditorDraft(draft: QuestionItem, field: string, value: string): QuestionItem | undefined {
  if (field === 'stem' || field === 'explanation') return { ...draft, [field]: value };
  const choices = !draft.questionType || draft.questionType === 'mcq';
  if (field === 'key') {
    if ((choices && /^[A-D]$/i.test(value)) || (draft.questionType === 'short_answer' && value.trim())) {
      return { ...draft, key: choices ? value.toUpperCase() : value };
    }
    return;
  }
  if (choices && /^[A-D]$/.test(field)) {
    return { ...draft, choices: { ...draft.choices, [field]: value } };
  }
  const statement = /^(statement|truth)_([a-d])$/.exec(field);
  if (!statement || draft.questionType !== 'true_false' || !draft.statements) return;
  const index = 'abcd'.indexOf(statement[2]);
  if (!draft.statements[index]) return;
  const answer = fold(value);
  const truth = ['dung', 'true'].includes(answer);
  if (statement[1] === 'truth' && !truth && !['sai', 'false'].includes(answer)) return;
  return {
    ...draft,
    statements: draft.statements.map((item, i) => i !== index ? item
      : statement[1] === 'truth' ? { ...item, answer: truth } : { ...item, text: value }),
  };
}
