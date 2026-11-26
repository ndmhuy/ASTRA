import type { QuestionChoices } from '../types/exam.ts';

const COMPLEX_LATEX_PATTERN =
  /\\(?:frac|dfrac|tfrac|begin|sum|int|lim|prod|matrix|pmatrix|bmatrix|cases)\b|\$\$/i;

function normalizeChoiceText(raw: string): string {
  return raw.replace(/\$/g, '').replace(/\s+/g, ' ').trim();
}

/**
 * Picks a symmetric grid class for 4 MCQ options so choices render either
 * 1 row x 4 columns (compact options) or 2 rows x 2 columns (never 3 + 1).
 */
export function getChoiceGridClass(
  choices: QuestionChoices | readonly string[] | null | undefined,
): 'cols-4' | 'cols-2' {
  if (!choices) return 'cols-2';
  const values = Array.isArray(choices)
    ? choices
    : (['A', 'B', 'C', 'D'] as const).map(key => (choices as QuestionChoices)[key] ?? '');

  if (values.length !== 4) return 'cols-2';

  const allCompact = values.every(value => {
    if (typeof value !== 'string') return false;
    const raw = value.trim();
    if (!raw || raw.includes('\n') || COMPLEX_LATEX_PATTERN.test(raw)) return false;
    return normalizeChoiceText(raw).length <= 16;
  });

  return allCompact ? 'cols-4' : 'cols-2';
}
