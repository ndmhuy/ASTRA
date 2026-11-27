import domain from '../../../src/exam_baseline/resources/agent/domain.json' with { type: 'json' };
import type { ExamFormat } from '../types/exam.ts';
import type { Decision, ExamIntake, Intent } from './contracts.ts';
import type { Intake } from './intake.ts';
import { fold } from './recipes.ts';

export type AdjacentTopicConfig = {
  id: string;
  formatId: string;
  label: string;
  subject: string;
  language: string;
  defaultCount: number;
  defaultMinutes: number;
  terms: string[];
  searchQueries: string[];
  sectionGuidance: string;
};

const ADJACENT_TOPICS = (
  (domain as unknown as { adjacentTopics?: Record<string, AdjacentTopicConfig> }).adjacentTopics ?? {}
);

export function listAdjacentTopics(): AdjacentTopicConfig[] {
  return Object.values(ADJACENT_TOPICS);
}

export function matchAdjacentTopic(message: string): AdjacentTopicConfig | undefined {
  return listAdjacentTopics().find(topic => topic.terms.some(term => contains(message, term)));
}

export const familyFor = (format: ExamFormat) =>
  (Object.keys(domain.families) as Array<keyof typeof domain.families>)
    .find(key => domain.families[key].examType === format.examType);

const contains = (message: string, value: string) =>
  (" " + fold(message).replace(/[^a-z0-9-]+/g, ' ') + " ").includes(" " + fold(value) + " ");

function subjectVocabulary(formats: ExamFormat[]) {
  const subjects: Record<string, string[]> = { ...domain.subjects };
  for (const format of formats) for (const subject of format.subjects) subjects[subject] ??= [];
  return Object.entries(subjects);
}

export function shortSubjectIntake(message: string, formats: ExamFormat[] = []): ExamIntake | undefined {
  const phrase = fold(message).replace(/[.!]+$/, '').replace(/\s+(?:nhe|nha)$/, '');
  const name = phrase.replace(/^(?:de(?: thi)?(?: mon)?|mon)(?:\s*:\s*|\s+)/, '').replace(/\s+thpt$/, '');
  const matches = subjectVocabulary(formats).filter(([subject, aliases]) =>
    [subject, ...aliases].some(term => fold(term) === name));
  if (matches.length !== 1) return;
  return { mode: 'request', subject: matches[0][0] };
}

export function mentionedFamilies(message: string) {
  return (Object.entries(domain.families) as Array<[keyof typeof domain.families, { terms: string[] }]>)
    .filter(([, family]) => family.terms.some(term => contains(message, term)))
    .map(([key]) => key);
}

export function formatOverview(format: ExamFormat) {
  const sectionNames: Record<string, string> = {
    mcq: 'trắc nghiệm', true_false: 'đúng/sai', short_answer: 'trả lời ngắn',
  };
  const sections = format.sections.map(section =>
    (section.title || sectionNames[section.type] || section.id) + ' (' + section.count + ' câu)').join(', ');
  return format.displayName + ' có ' + format.totalQuestions + ' câu, ' +
    format.durationMinutes + ' phút' + (sections ? '. Các phần gồm ' + sections : '') + '.';
}

export function guidanceFor(kind: Decision['guidance'], formats: ExamFormat[]) {
  if (kind === 'remark') return 'Em ghi nhận nhận xét. Nếu thầy cô muốn sửa, hãy cho em biết câu nào và muốn đổi điều gì.';
  const options = formats.filter(format => format.available).map(format => format.displayName).join(' và ');
  if (!options) return 'Hiện chưa thấy mẫu đề khả dụng. Thầy cô có thể xem lại đề đã lưu trong tủ đề.';
  return kind === 'capabilities'
    ? 'ASTRA có thể chuẩn bị đề theo mẫu ' + options + ', cho xem cấu trúc, kiểm tra câu hỏi, xem trước PDF và xuất tệp sau khi thầy cô duyệt.'
    : 'Thầy cô có thể bắt đầu bằng một trong các mẫu ' + options + '. Hãy cho em biết muốn luyện dạng nào. Em có thể trình bày cấu trúc trước khi thầy cô quyết định tạo đề.';
}

type Resolution = { text: string; draft?: Intake; title?: string; preset?: ExamFormat } |
  { intent: Intent; draft: Intake; title: string };

export function resolveIntake(
  proposal: ExamIntake, message: string, previous: Intake | undefined,
  formats: ExamFormat[], sourceId: string,
  semantic = false,
): Resolution {
  const available = formats.filter(format => format.available);
  const previousFormat = available.find(format => format.id === previous?.formatId && format.version === previous?.version);
  const literalFamilies = mentionedFamilies(message);
  const priorFamily = previous?.family ?? (previousFormat && familyFor(previousFormat));
  const correction = /\b(?:doi|chuyen) sang\b/.test(fold(message));
  const statedFamily = literalFamilies.length === 1 ? literalFamilies[0]
    : literalFamilies.length > 1
      ? (correction && proposal.family && literalFamilies.includes(proposal.family) ? proposal.family : undefined)
      : semantic ? proposal.family ?? priorFamily : proposal.mode === 'request' ? priorFamily : proposal.family ?? priorFamily;

  // Match a catalog subject dynamically. Vocabulary also recognizes subjects absent from the catalog.
  const subjects = subjectVocabulary(formats);
  const subjectMatches = subjects.filter(([name, aliases]) =>
    [name, ...aliases].some(term => contains(message, 'môn ' + term) ||
      fold(message).replace(/[.!?]+$/, '') === fold(term))).map(([name]) => name);
  const proposed = proposal.subject;
  const canonical = proposed && subjects.find(([name, aliases]) =>
    [name, ...aliases].some(term => fold(term) === fold(proposed)));
  const extracted = proposed && (contains(message, proposed) ||
    (canonical && canonical[1].some(alias => contains(message, alias))))
    ? canonical?.[0] ?? proposed : undefined;
  const correctedSubject = correction && extracted && subjectMatches.includes(extracted) ? extracted : undefined;
  if (proposal.mode === 'request' && subjectMatches.length > 1 && !correctedSubject) {
    return { text: 'Thầy cô muốn chọn môn nào? ' + subjectMatches.join(', ') + '.' };
  }
  const statedSubject = correctedSubject ?? subjectMatches[0] ?? extracted;
  const priorSubject = previous?.subject ?? previousFormat?.subjects[0];
  const subjectFormats = statedSubject ? available.filter(format =>
    format.subjects.some(item => fold(item) === fold(statedSubject))) : [];
  const family = statedFamily ?? (proposal.mode === 'request' && !literalFamilies.length && subjectFormats.length === 1
    ? familyFor(subjectFormats[0]) : undefined);
  const familyChanged = !!priorFamily && !!family && priorFamily !== family;
  const subjectChanged = !!statedSubject && !!priorSubject && fold(statedSubject) !== fold(priorSubject);
  const subject = statedSubject ?? (familyChanged ? undefined : priorSubject);
  const topic = proposal.topic?.trim();
  if (topic && (!fold(message).includes(fold(topic)) || /\p{Cc}/u.test(topic))) {
    return { text: 'Thầy cô hãy ghi rõ chuyên đề cần tập trung.' };
  }
  const previousFacts = familyChanged || subjectChanged ? undefined : previous;
  const text = fold(message);
  const count = Number(text.match(/\b(\d+)\s*cau\b/)?.[1]) || proposal.count || (proposal.useDefaults ? undefined : previousFacts?.count);
  const minutes = Number(text.match(/\b(\d+)\s*phut\b/)?.[1]) || proposal.minutes || (proposal.useDefaults ? undefined : previousFacts?.minutes);
  const grade = Number(text.match(/\blop\s+(\d+)\b/)?.[1]) || proposal.grade || (proposal.useDefaults ? undefined : previousFacts?.grade);
  const draft: Intake = {
    sourceId, sourceIds: [...new Set([...(previousFacts?.sourceIds ?? (previousFacts ? [previousFacts.sourceId] : [])), sourceId])],
    family, subject, topic: topic ?? previousFacts?.topic, grade, count, minutes,
    phase: 'collecting',
  };
  const update = proposal.mode === 'request' ? { draft } : {};
  const familyFormats = family ? available.filter(format => familyFor(format) === family) : available;
  const matches = familyFormats.filter(format => !subject || format.subjects.some(item => fold(item) === fold(subject)));
  if (!familyFormats.length) {
    return { ...update, text: family
      ? 'ASTRA hiện chưa có mẫu khả dụng cho ' + domain.families[family].label + '.'
      : 'Hiện chưa có mẫu đề khả dụng.' };
  }
  if (!matches.length) {
    const alternatives = [...new Set(familyFormats.flatMap(format => format.subjects))].join(', ');
    return { ...(proposal.mode === 'request' ? { draft: { ...draft, missing: 'subject' as const } } : {}), text: 'ASTRA hiện chưa hỗ trợ môn ' + subject + (family ? ' cho ' + domain.families[family].label : '') +
      '. Môn đang có gồm ' + alternatives + '.' };
  }
  if (proposal.mode !== 'request') {
    return { text: matches.map(formatOverview).join(' '),
      title: family === 'vact' ? 'Cấu trúc đề V-ACT' : family === 'thpt' ? 'Cấu trúc đề THPT' : 'Xem cấu trúc mẫu đề' };
  }
  const format = matches.length === 1 ? matches[0] : undefined;
  const familyLabel = family === 'thpt' ? 'THPT' : family === 'vact' ? 'V-ACT' : undefined;
  const title = familyLabel ? 'Soạn đề ' + familyLabel : 'Chọn mẫu đề thi';
  if (family && format && (
    (count !== undefined && count !== format.totalQuestions) ||
    (minutes !== undefined && minutes !== format.durationMinutes) ||
    (grade !== undefined && !format.grades.includes(grade))
  )) return { draft, title, preset: format, text: formatOverview(format) + ' Mẫu này có cấu trúc và khối lớp cố định. Nhắn “Đồng ý” để dùng cấu trúc đó.' };
  if (!family) return { draft: { ...draft, missing: 'family' }, title,
    text: 'Thầy cô muốn chọn mẫu nào? ASTRA hiện có ' + matches.map(format => format.displayName).join(', ') + '.' };
  if (!subject && family === 'thpt') return { draft: { ...draft, missing: 'subject' }, title,
    text: 'Thầy cô muốn ôn thi tốt nghiệp môn nào? Mẫu đang hỗ trợ ' +
      [...new Set(matches.flatMap(item => item.subjects))].join(', ') + '.' };
  if (!format) return { draft, title, text: 'Thầy cô muốn sử dụng mẫu nào? ' + matches.map(formatOverview).join(' ') };
  return {
    intent: { id: draft.topic ? 'PREPARE_GENERATION' : 'SELECT_FORMAT', args: {
      format: format.id, ...(draft.topic ? { topic: draft.topic } : { details: true }),
    }},
    draft: { ...draft, formatId: format.id, version: format.version, subject: subject ?? format.subjects[0] },
    title: family === 'vact' ? 'Soạn đề V-ACT' : 'Đề thi thử ' + format.displayName,
  };
}
