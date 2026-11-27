import type { ExamPackage, QuestionItem, VisualWarning } from '../types/exam';
import { formatVisualWarning } from './userMessages.ts';

export type QuestionReviewKind =
  | 'approved'
  | 'mismatched'
  | 'needs_recheck'
  | 'matched_unapproved';

export interface QuestionReviewState {
  kind: QuestionReviewKind;
  label: string;
  primaryAction: string;
}

export interface ReviewQueueItem {
  question: QuestionItem;
  index: number;
  label: string;
  state: QuestionReviewState;
  notes: string[];
}

export interface QuestionReviewSummary {
  answerIssueItems: ReviewQueueItem[];
  unapprovedMatchedItems: ReviewQueueItem[];
  approvedItems: ReviewQueueItem[];
  sourceOrVisualItems: ReviewQueueItem[];
  sourceOrVisualQuestionCount: number;
  notesByStableId: Record<string, string[]>;
}

const PART_ROMAN: Record<string, string> = {
  P1: 'I',
  P2: 'II',
  P3: 'III',
};

/** Format a stable question identifier (e.g. `P3-3` -> `Câu III.3`) for quick lookup. */
export function formatQuestionLabel(
  question: Pick<QuestionItem, 'stableId' | 'id'>,
  index?: number
): string {
  const stableId = question.stableId?.trim();
  if (stableId) {
    const partMatch = stableId.match(/^(P[123])-(\d+)$/i);
    if (partMatch) {
      const roman = PART_ROMAN[partMatch[1].toUpperCase()];
      if (roman) return `Câu ${roman}.${partMatch[2]}`;
    }
    const vactMatch = stableId.match(/^q(\d+)$/i);
    if (vactMatch) return `Câu ${vactMatch[1]}`;
  }
  const fallbackNumber = index !== undefined ? index + 1 : question.id;
  return `Câu ${fallbackNumber}`;
}

/** Map current verification and approval metadata onto the handoff status table. */
export function getQuestionReviewState(question: QuestionItem): QuestionReviewState {
  if (question.questionApproval) {
    return {
      kind: 'approved',
      label: 'Đã duyệt',
      primaryAction: 'Xem chi tiết quyết định khi cần.',
    };
  }
  if (question.answerCheck === 'mismatched') {
    return {
      kind: 'mismatched',
      label: 'Lệch đáp án',
      primaryAction: 'Xem hai kết quả, sửa hoặc ghi lý do xác nhận.',
    };
  }
  if (!question.answerCheck || question.answerCheck === 'needs_recheck') {
    return {
      kind: 'needs_recheck',
      label: 'Cần đối chiếu',
      primaryAction: 'Xem lý do, sửa nếu cần rồi giải kiểm tra lại.',
    };
  }
  return {
    kind: 'matched_unapproved',
    label: 'Khớp đáp án · Chưa duyệt',
    primaryAction: 'Kiểm tra nội dung rồi duyệt câu.',
  };
}

/** Return the most helpful primary explanation for a flagged/unapproved question. */
export function getPrimaryReviewReason(question: QuestionItem): string {
  if (question.auditNotes?.trim()) return question.auditNotes.trim();
  if (question.answerCheck === 'mismatched') {
    if (question.mismatchedStatements?.length) {
      return `Đáp án khác kết quả giải độc lập ở ý ${question.mismatchedStatements.join(', ')}.`;
    }
    return 'Đáp án dự kiến khác kết quả giải độc lập.';
  }
  if (!question.answerCheck || question.answerCheck === 'needs_recheck') {
    return 'Chưa có kết quả giải độc lập có thể đối chiếu cho câu này.';
  }
  return 'Đáp án khớp với kết quả giải độc lập, chờ người duyệt xác nhận.';
}

/** Build deduplicated question review lists with RAG/visual notes counted separately. */
export function buildQuestionReviewSummary(
  questions: QuestionItem[],
  warnings?: ExamPackage['warnings'],
  visualWarnings?: VisualWarning[]
): QuestionReviewSummary {
  const notesByStableId: Record<string, string[]> = {};

  const appendNote = (rawQuestionId: string | undefined, text: string) => {
    const key = rawQuestionId?.trim().toUpperCase();
    const cleanText = text.trim();
    if (!key || !cleanText) return;
    const list = notesByStableId[key] ?? (notesByStableId[key] = []);
    if (!list.includes(cleanText)) list.push(cleanText);
  };

  for (const warning of warnings || []) {
    if (warning.questionId) appendNote(warning.questionId, warning.message);
  }
  for (const visual of visualWarnings || []) {
    if (visual.questionId) appendNote(visual.questionId, formatVisualWarning(visual.code));
  }

  const answerIssueItems: ReviewQueueItem[] = [];
  const unapprovedMatchedItems: ReviewQueueItem[] = [];
  const approvedItems: ReviewQueueItem[] = [];
  const sourceOrVisualItems: ReviewQueueItem[] = [];
  const seenKeys = new Set<string>();

  for (let index = 0; index < questions.length; index += 1) {
    const question = questions[index];
    const dedupeKey = question.stableId?.trim().toUpperCase() || `id:${question.id}`;
    if (seenKeys.has(dedupeKey)) continue;
    seenKeys.add(dedupeKey);

    const label = formatQuestionLabel(question, index);
    const state = getQuestionReviewState(question);
    const notes = question.stableId
      ? (notesByStableId[question.stableId.trim().toUpperCase()] ?? [])
      : [];
    const entry: ReviewQueueItem = { question, index, label, state, notes };

    if (state.kind === 'approved') {
      approvedItems.push(entry);
    } else if (state.kind === 'matched_unapproved') {
      unapprovedMatchedItems.push(entry);
    } else {
      answerIssueItems.push(entry);
    }

    if (notes.length > 0) {
      sourceOrVisualItems.push(entry);
    }
  }

  return {
    answerIssueItems,
    unapprovedMatchedItems,
    approvedItems,
    sourceOrVisualItems,
    sourceOrVisualQuestionCount: sourceOrVisualItems.length,
    notesByStableId,
  };
}
