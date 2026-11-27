import type { ExamSession } from '../state/examSessions.ts';
import { displayNumber, sectionId } from './examActions.ts';

export type Note = {
  id: string;
  sourceId: string;
  jobId: string;
  number: number;
  part?: string;
  instruction: string;
  stableId?: string;
  status: 'recorded' | 'awaiting_review' | 'unresolved' | 'applied' | 'failed' | 'cancelled';
  appliedRevision?: number;
};

export const noteLabel = (note: Note) => `Câu ${note.number}${note.part ? ` (${note.part})` : ''}`;

export function reconcileNotes(notes: Note[] | undefined, jobId: string, questions: ExamSession['questions']) {
  return notes?.map(note => {
    if (note.jobId !== jobId || note.status !== 'recorded') return note;
    const matches = questions.filter(question => question.stableId && displayNumber(question) === note.number &&
      (!note.part || question.part === sectionId(note.part)));
    return matches.length === 1
      ? { ...note, stableId: matches[0].stableId, status: 'awaiting_review' as const }
      : { ...note, status: 'unresolved' as const };
  });
}
