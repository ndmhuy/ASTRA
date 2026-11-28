import type { ExamFormat, ExamRequestParams } from '../types/exam.ts';
import type { Intake } from './intake.ts';
import { presetParams } from './intake.ts';
import { fold } from './recipes.ts';
import { detectSubjectInMessage, familyFor, shortSubjectIntake } from './knowledge.ts';

export interface ChatConfigDraft {
  id: string;
  sourceMessageId: string;
  formatId?: string;
  family?: Intake['family'];
  subject?: string;
  requestedCount?: number;
  requestedMinutes?: number;
  requestedGrade?: number;
  topic: string;
  difficulty: string;
  extraNotes: string;
  limitations: string[];
  needsClarification: string[];
  applied: string[];
  hasMismatch: boolean;
}

const DIFFICULTY_PATTERNS: Array<{ pattern: RegExp; label: string }> = [
  { pattern: /\b(?:tang|nhieu|uu tien)\s+cau\s+van\s+dung\s+cao\b/, label: 'Tăng câu vận dụng cao' },
  { pattern: /\b(?:tang|nhieu|uu tien)\s+(?:cau|muc)?\s*van\s+dung\b/, label: 'Tăng câu vận dụng' },
  { pattern: /\b(?:tang|nhieu|uu tien)\s+(?:cau|muc)?\s*thong\s+hieu\b/, label: 'Tăng câu thông hiểu' },
  { pattern: /\b(?:tang|nhieu|uu tien)\s+(?:cau|muc)?\s*nhan\s+biet\b/, label: 'Ưu tiên mức nhận biết' },
  { pattern: /\bvan\s+dung\s+cao\b/, label: 'Mức độ: Vận dụng cao' },
  { pattern: /\bnang\s+cao\b/, label: 'Mức độ nâng cao / phân hóa' },
  { pattern: /\bco\s+ban\b/, label: 'Mức độ cơ bản' },
  { pattern: /\bkho\s+hon\b/, label: 'Tăng độ khó' },
  { pattern: /\bde\s+hon\b/, label: 'Giảm độ khó' },
];

const TOPIC_PATTERNS = [
  /(?:ưu tiên|uu tien|tập trung(?:\s+vào)?|tap trung(?:\s+vao)?|chương|chuong|chuyên đề|chuyen de|phần|phan|về|ve)\s+(?:về\s+|ve\s+|chủ đề\s+|chu de\s+|chương\s+|chuong\s+)?([^,.;\n]+)/i,
];

function extractClause(raw: string, pattern: RegExp): string {
  const match = raw.match(pattern);
  if (!match) return '';
  let candidate = match[1].trim();
  const cutoff = candidate.search(/\b(?:tăng|tang|nhiều|nhieu|giảm|giam|mức độ|muc do|vận dụng|van dung|nâng cao|nang cao|cơ bản|co ban|\d+\s*(?:câu|cau|phút|phut)|lớp\s+\d+|lop\s+\d+)\b/i);
  if (cutoff > 0) candidate = candidate.slice(0, cutoff).trim();
  return candidate.replace(/[,.;:]+$/, '').trim();
}

function matchDifficulty(raw: string): string {
  const folded = fold(raw);
  const found: string[] = [];
  for (const item of DIFFICULTY_PATTERNS) {
    if (item.pattern.test(folded) && !found.includes(item.label)) {
      found.push(item.label);
    }
  }
  return found.slice(0, 2).join(' · ');
}

function matchTopic(raw: string, matchedSubject?: string): string {
  const compact = raw.replace(/\s+/g, ' ').trim();
  for (const pattern of TOPIC_PATTERNS) {
    const candidate = extractClause(compact, pattern);
    if (!candidate || candidate.length < 2) continue;
    if (matchedSubject && fold(candidate) === fold(matchedSubject)) continue;
    if (/^(?:mau nay|cau truc|thpt|v-?act)$/i.test(fold(candidate))) continue;
    return candidate.slice(0, 120);
  }
  return '';
}

function resolveMatchedFormat(
  message: string,
  formats: ExamFormat[],
  previous?: Intake,
  proposal?: Partial<Intake>,
): { format?: ExamFormat; family?: Intake['family']; subject?: string } {
  const available = formats.filter(f => f.available);
  const folded = fold(message);
  const subjectGuess = shortSubjectIntake(message, available);
  const detectedSubject = detectSubjectInMessage(message, available);
  const subject = proposal?.subject ?? subjectGuess?.subject ?? detectedSubject ?? previous?.subject;
  const family: Intake['family'] =
    proposal?.family === 'vact' || /\bv-?act\b|\bdanh gia nang luc\b|\bdhqg\b/.test(folded)
      ? 'vact'
      : proposal?.family === 'thpt' || /\bthpt\b|\btot nghiep\b/.test(folded)
        ? 'thpt'
        : subjectGuess?.family ?? previous?.family;

  if (proposal?.formatId) {
    const exact = available.find(f => f.id === proposal.formatId);
    if (exact) return { format: exact, family: familyFor(exact), subject: exact.subjects[0] };
  }
  if (family === 'vact') {
    const vact = available.find(f => familyFor(f) === 'vact');
    if (vact) return { format: vact, family: 'vact', subject: vact.subjects[0] };
  }
  if (subject) {
    const match = available.find(f => f.subjects.some(s => fold(s) === fold(subject)));
    if (match) return { format: match, family: familyFor(match), subject: match.subjects[0] };
  }
  return { format: undefined, family, subject };
}

export function extractExamDraft(
  message: string,
  formats: ExamFormat[],
  sourceMessageId: string,
  previous?: Intake,
  proposal?: Partial<Intake>,
  existingId?: string,
): ChatConfigDraft | null {
  const folded = fold(message);
  const hasExamCue =
    Boolean(proposal?.formatId || proposal?.subject || proposal?.family || proposal?.topic) ||
    /\b(?:soan|tao|lam|ra|on tap)\b/.test(folded) ||
    /\b\d+\s*(?:cau|phut)\b/.test(folded) ||
    Boolean(shortSubjectIntake(message, formats));
  if (!hasExamCue) return null;

  const { format, family, subject } = resolveMatchedFormat(message, formats, previous, proposal);
  const countMatch = folded.match(/\b(\d+)\s*cau\b/);
  const minutesMatch = folded.match(/\b(\d+)\s*phut\b/);
  const gradeMatch = folded.match(/\blop\s+(\d+)\b/);

  const requestedCount = countMatch ? Number(countMatch[1]) : proposal?.count;
  const requestedMinutes = minutesMatch ? Number(minutesMatch[1]) : proposal?.minutes;
  const requestedGrade = gradeMatch ? Number(gradeMatch[1]) : proposal?.grade;

  const topic = (proposal?.topic?.trim() || matchTopic(message, subject) || previous?.topic || '').slice(0, 120);
  const difficulty = matchDifficulty(message);

  const draft: ChatConfigDraft = {
    id: existingId || `${sourceMessageId}`,
    sourceMessageId,
    formatId: format?.id,
    family,
    subject,
    requestedCount,
    requestedMinutes,
    requestedGrade,
    topic,
    difficulty,
    extraNotes: '',
    limitations: [],
    needsClarification: [],
    applied: [],
    hasMismatch: false,
  };

  return recomputeDraftStatus(draft, formats);
}

export function recomputeDraftStatus(draft: ChatConfigDraft, formats: ExamFormat[]): ChatConfigDraft {
  const format = formats.find(f => f.id === draft.formatId && f.available);
  const applied: string[] = [];
  const limitations: string[] = [];
  const needsClarification: string[] = [];
  let hasMismatch = false;

  if (format) {
    applied.push(`${format.displayName} (${format.totalQuestions} câu · ${format.durationMinutes} phút)`);
    if (draft.topic.trim()) applied.push(`Chủ đề trọng tâm: ${draft.topic.trim()}`);
    if (draft.difficulty.trim()) applied.push(draft.difficulty.trim());

    const mismatches: string[] = [];
    if (draft.requestedCount !== undefined && draft.requestedCount !== format.totalQuestions) {
      mismatches.push(`${draft.requestedCount} câu (mẫu cố định ${format.totalQuestions} câu)`);
    }
    if (draft.requestedMinutes !== undefined && draft.requestedMinutes !== format.durationMinutes) {
      mismatches.push(`${draft.requestedMinutes} phút (mẫu cố định ${format.durationMinutes} phút)`);
    }
    if (draft.requestedGrade !== undefined && !format.grades.includes(draft.requestedGrade)) {
      mismatches.push(`lớp ${draft.requestedGrade} (mẫu cố định lớp ${format.grades.join(', ')})`);
    }
    if (mismatches.length > 0) {
      hasMismatch = true;
      limitations.push(
        `Chưa đổi được ${mismatches.join(' và ')}. Thầy cô có thể dùng cấu trúc ${format.displayName} bên dưới và tùy chỉnh chủ đề / mức độ.`
      );
    }
  } else {
    needsClarification.push('Chưa chọn môn hoặc mẫu đề cụ thể.');
    if (draft.requestedCount !== undefined || draft.requestedMinutes !== undefined) {
      const reqParts = [
        draft.requestedCount !== undefined ? `${draft.requestedCount} câu` : '',
        draft.requestedMinutes !== undefined ? `${draft.requestedMinutes} phút` : '',
      ].filter(Boolean).join(', ');
      limitations.push(
        `Các mẫu THPT & V-ACT có số câu và thời gian cố định theo cấu trúc chuẩn (không tùy biến sang ${reqParts}). Chọn một mẫu bên dưới để dùng cấu trúc chuẩn hoặc tùy chỉnh chủ đề / độ khó.`
      );
    }
    if (draft.topic.trim()) applied.push(`Chủ đề tạm lưu: ${draft.topic.trim()}`);
    if (draft.difficulty.trim()) applied.push(draft.difficulty.trim());
  }

  return { ...draft, applied, limitations, needsClarification, hasMismatch };
}

export function buildCustomPrompt(
  format: ExamFormat,
  topic: string,
  difficulty: string,
  extraNotes: string,
): string {
  const lines = [`Tạo đề ${format.displayName}`];
  if (topic.trim()) lines.push(`Chuyên đề trọng tâm: ${topic.trim()}`);
  if (difficulty.trim()) lines.push(`Phân bố độ khó: ${difficulty.trim()}`);
  if (extraNotes.trim()) lines.push(`Yêu cầu bổ sung: ${extraNotes.trim()}`);
  return lines.join('\n');
}

export function buildParamsFromDraft(
  draft: ChatConfigDraft,
  formats: ExamFormat[],
  uploadedFileIds: string[],
): ExamRequestParams | null {
  const format = formats.find(f => f.id === draft.formatId && f.available);
  if (!format) return null;
  const base = presetParams(format);
  return {
    ...base,
    prompt: buildCustomPrompt(format, draft.topic, draft.difficulty, draft.extraNotes),
    uploadedFiles: uploadedFileIds,
  };
}
