import type { ExamSession } from '../state/examSessions.ts';

/** Actual submitted form parameters also exist when no chat intake was created. */
export function workspaceDescription(session: ExamSession): string {
  const params = session.lastParams;
  const subject = params?.subject ?? session.package?.subject ?? session.meta?.subject ?? session.intake?.subject;
  const family = params?.formatId?.startsWith('thpt-') || params?.examType?.startsWith('THPT') || session.intake?.family === 'thpt' ? 'THPT'
    : params?.formatId?.startsWith('vact') || session.intake?.family === 'vact' ? 'V-ACT' : '';
  const count = params?.itemCount ?? session.meta?.totalCount ?? session.intake?.count ?? (session.questions.length || undefined);
  const minutes = params?.durationMinutes ?? session.package?.durationMinutes ?? session.meta?.duration ?? session.intake?.minutes;
  return [subject ? `Đề ${subject}${family ? ` ${family}` : ''}` : session.title,
    count ? `${count} câu` : '', minutes ? `${minutes} phút` : ''].filter(Boolean).join(' · ');
}

export function workspaceContextFacts(session: ExamSession): string[] {
  return [workspaceDescription(session),
    ...(session.lastParams?.prompt ? [`Yêu cầu trong cấu hình: ${session.lastParams.prompt.slice(0, 500)}`] : []),
    ...(session.lastParams?.grade ? [`Lớp ${session.lastParams.grade}`] : [])];
}
