import domain from '../../../src/exam_baseline/resources/agent/domain.json' with { type: 'json' };
import type { ExamIntake } from './contracts.ts';
import type { ExamFormat } from '../types/exam.ts';
import type { ExamSession } from '../state/examSessions.ts';
import { fold, polite } from './language.ts';
import { mentionedFamilies, shortSubjectIntake } from './knowledge.ts';

// Recognize the request's structure, not a list of complete user sentences.
// Unparsed requirements still go to the existing interpreter; no defaults are invented.
export function examCreation(message: string, formats: ExamFormat[] = []): { newExam: boolean; intake?: ExamIntake } | undefined {
  const text = polite(message).replace(/^(?:co|thay|toi|minh|tao|tui|em) (?:muon|can) /, '');
  if (/["“”«»`?]/.test(message) || /\b(?:dung|khong|ko|chua|neu|gia su|co the)\b/.test(text) ||
      /\b(?:roi|sau do|dong thoi|va (?:mo|xoa|xuat|duyet|tao|soan))\b/.test(text)) return;
  const match = text.match(/^(?:tao|soan|ra|gen)(?: (?:mot|1))? de(?: thi)?(?: (.*))?$/);
  if (!match) return;
  const tail = match[1] ?? '';
  const designation = tail.split(/\b(?:chuyen de|chu de|ve|tap trung)\b/)[0];
  const newExam = /\b(?:moi|khac)\b/.test(designation);
  const families = mentionedFamilies(tail);
  if (families.length > 1) return { newExam };
  let subjectName = tail.replace(/\b(?:moi|khac)\b/g, ' ');
  if (families.length) {
    const terms = [...domain.families[families[0]].terms].sort((a, b) => b.length - a.length);
    for (const term of terms) {
      const escaped = fold(term).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      subjectName = subjectName.replace(new RegExp('(^|\\s)' + escaped + '(?=\\s|$)', 'g'), ' ');
    }
  }
  subjectName = subjectName.replace(/\s+/g, ' ').trim();
  const subject = shortSubjectIntake(subjectName, formats)?.subject;
  if (subjectName && !subject) return { newExam };
  return { newExam, intake: { mode: 'request', ...(families[0] ? { family: families[0] } : {}), ...(subject ? { subject } : {}) } };
}

export function needsNewExamWorkspace(session: ExamSession | undefined, message: string) {
  const request = examCreation(message);
  if (!session || !request) return false;
  const hasWork = session.jobId || session.generationId || session.generationStopped || session.intake || session.messages.length;
  return session.status === 'complete' || !!(request.newExam && hasWork);
}
