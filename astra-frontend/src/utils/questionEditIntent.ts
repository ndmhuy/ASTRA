import type { QuestionItem } from '../types/exam';

type Intent = { kind: 'chat' | 'clarify' } | { kind: 'edit'; question: QuestionItem };

const sections: Record<string, string> = {
  i: 'P1', '1': 'P1', p1: 'P1', ii: 'P2', '2': 'P2', p2: 'P2', iii: 'P3', '3': 'P3', p3: 'P3',
};
const normalize = (content: string) =>
  content.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/đ/g, 'd');

export function questionEditIntent(content: string, questions: QuestionItem[]): Intent {
  const text = normalize(content);
  if (/^(?:vi sao|tai sao|giai thich)\b/.test(text.trim()) ||
      /^(?:(?:cau\s+\d+|p[123]-\d+|q\d+)\s*[:,]?\s*|vui long\s+)?(?:khong|dung)\s+(?:sua|chinh(?: sua)?|viet lai|tao lai|doi|thay)\b/.test(text.trim()) ||
      !/\b(?:sua|chinh sua|viet lai|tao lai|doi lai|doi cau|thay doi|thay the)\b/.test(text)) {
    return { kind: 'chat' };
  }

  // Compound requests must be disambiguated before mutating the exam.
  if (/\bcau\s+\d+\s*(?:-|–|den|va|hoac|,)\s*(?:cau\s+)?\d+/.test(text)) {
    return { kind: 'clarify' };
  }
  const refs = [...text.matchAll(/\b(p[123]-\d+|q\d+)\b/g)].map(match =>
    questions.filter(question => question.stableId?.toLowerCase() === match[1]));
  const numbered = /\b(?:(?:phan\s+(iii|ii|i|[123])|(p[123]))\s*[,.:]?\s+cau\s+(\d+)|cau\s+(\d+)(?:\s+(?:(?:o|thuoc|cua)\s+)?(?:phan\s+(iii|ii|i|[123])|(p[123])))?)\b/g;
  for (const match of text.matchAll(numbered)) {
    const [, prefix, prefixCode, firstNumber, lastNumber, suffix, suffixCode] = match;
    const part = sections[prefix || prefixCode || suffix || suffixCode];
    const number = Number(firstNumber || lastNumber);
    refs.push(questions.filter(question => {
      const id = question.stableId?.toUpperCase();
      if (part) return id === `${part}-${number}`;
      return id ? id === `Q${number}` || /^P[123]-/.test(id) && id.endsWith(`-${number}`)
        : question.id === number;
    }));
  }
  if (refs.length === 0 || refs.some(items => items.length !== 1)) return { kind: 'clarify' };
  const targets = new Set(refs.map(([question]) => question));
  if (targets.size !== 1) return { kind: 'clarify' };
  return { kind: 'edit', question: refs[0][0] };
}

export function clarifyQuestionEdit(content: string, original: string, questions: QuestionItem[]): Intent {
  const text = normalize(content).trim().replace(/\.$/, '');
  const part = /^(?:phan\s+)?(iii|ii|i|[123]|p[123])$/.exec(text);
  if (part) {
    return questionEditIntent(original, questions.filter(question => question.part === sections[part[1]]));
  }
  if (/^(?:cau\s+\d+(?:\s+(?:o\s+)?phan\s+(?:iii|ii|i|[123]))?|phan\s+(?:iii|ii|i|[123])\s*[,.:]?\s+cau\s+\d+|p[123]-\d+|q\d+)$/.test(text)) {
    return questionEditIntent(`sua ${text}`, questions);
  }
  return { kind: 'chat' };
}
