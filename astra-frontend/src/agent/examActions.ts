import type { ExamSession } from '../state/examSessions.ts';
import type { Intent } from './contracts.ts';
import { fold, type Effect } from './recipes.ts';

export const success = (text: string): Effect => ({ status: 'succeeded', text });
export const failure = (text: string): Effect => ({ status: 'failed', text });

const sections: Record<string, string> = {
  '1': 'P1', 'i': 'P1', 'trac nghiem': 'P1', '2': 'P2', 'ii': 'P2', 'dung sai': 'P2',
  '3': 'P3', 'iii': 'P3', 'tra loi ngan': 'P3', 'tieng viet': 'TV', 'tieng anh': 'TA',
  'toan hoc': 'TO', 'logic': 'LOGIC', 'khoa hoc': 'SCIENCE',
};

export function sectionId(text: string) {
  const part = fold(text).replace(/^phan\s+/, '');
  return sections[part] || part.toUpperCase();
}

export function displayNumber(question: ExamSession['questions'][number]) {
  const suffix = question.stableId?.split('-')[1];
  return suffix && /^\d+$/.test(suffix) ? Number(suffix) : question.id;
}

export function resolveQuestion(session: ExamSession, args: Intent['args'], selected?: string) {
  const part = typeof args.part === 'string' ? sectionId(args.part) : undefined;
  const matches = session.questions.filter(question => !!question.stableId &&
    question.examRevision === session.package?.revision &&
    (typeof args.number === 'number' ? displayNumber(question) === args.number : question.stableId === selected) &&
    (!part || question.part === part));
  return matches.length === 1 ? matches[0] : undefined;
}

export function inspectQuestion(session: ExamSession | undefined, args: Intent['args']): Effect {
  if (!session?.package || session.status !== 'complete') return failure('Đề chưa có dữ liệu hoàn chỉnh để đọc câu hỏi.');
  const question = resolveQuestion(session, args);
  if (!question) return failure('Chưa xác định được câu hỏi hiện tại. Thầy cô hãy ghi số câu và phần thi.');
  const label = `Câu ${displayNumber(question)}${question.part ? ` (${question.part})` : ''}`;
  if(args.subItem!==undefined){
    const index=['a','b','c','d'].indexOf(String(args.subItem));
    const statement=index>=0?question.statements?.[index]:undefined;
    if(!statement)return failure(`${label} không có ý ${args.subItem} trong dữ liệu đã lưu.`);
    return success(`${label}, ý ${args.subItem}: ${statement.text}\nĐáp án đang lưu: ${statement.answer?'Đúng':'Sai'}.${statement.solution?`\nGiải thích đã lưu: ${statement.solution}`:''}`);
  }
  if(args.aspect==='verification')return success(`${label}: trạng thái kiểm tra đã lưu ${question.answerCheck??question.status}; đáp án tác giả ${question.writerKey??question.key??'chưa có'}, bộ giải ${question.solverKey??'chưa có'}.${question.auditNotes?` ${question.auditNotes}`:''} Chưa gọi bộ giải mới.`);
  if(args.aspect==='approval')return success(`${label}: ${question.questionApproval?.revision===session.package.revision?'đã được giáo viên duyệt ở phiên bản hiện tại':'chưa có phê duyệt riêng còn hiệu lực'}.`);
  if(args.aspect==='metadata')return success(`${label}: ${question.questionType??'chưa rõ loại'} · ${question.topic} · ${question.level}. Nguồn đã lưu: ${question.sourceReference??'chưa có'}. Phiên bản ${session.package.revision}.`);
  if(args.aspect==='explanation')return success(`${label}: ${question.explanation||'Chưa có lời giải đã lưu.'}`);
  return success([`${label}: ${question.stem}`,
    ...(args.view === 'paper' ? [] : [`Đáp án đang lưu: ${question.key || 'chưa có'}.`,
      ...(question.answerCheck === 'mismatched' ? ['Đáp án đang khác kết quả bộ giải đã lưu.'] : []),
      ...(question.explanation ? [`Giải thích đang lưu: ${question.explanation}`] : [])]),
  ].join('\n'));
}

export function statusText(session?: ExamSession) {
  if (!session) return 'Thầy cô hãy mở một không gian soạn đề để xem trạng thái.';
    if (session.progress && (session.generationId || session.stoppedJobId || session.status === 'generating')) {
      const progress = session.progress;
      const done = progress.completedItems ?? 0;
      const total = progress.totalItems ?? session.meta?.totalCount ?? 0;
      return `${progress.statusMessage} · Đã lưu ${done}/${total} câu, còn ${Math.max(0, total - done)} câu. ${progress.error?.message ?? ''}`.trim();
    }
  if (session.status === 'generating') {
    if (!session.jobId) return 'ASTRA đang gửi yêu cầu tạo đề và chờ mã công việc.';
    const progress = session.progress;
    if (!progress) return 'Máy chủ đã nhận công việc. Em đang chờ cập nhật tiến độ.';
    return `Cập nhật gần nhất: ${progress.statusMessage} · ${progress.percent}%.`;
  }
  if (session.status === 'error') return session.error || 'Yêu cầu trước gặp lỗi.';
  if (session.status === 'complete') return `Đề hiện có ${session.questions.length} câu. ${session.package?.approved ? 'Bản hiện tại đã được duyệt.' : 'Bản hiện tại đang chờ duyệt.'}`;
  return 'Đề vẫn ở bản nháp và chưa gửi yêu cầu tạo.';
}

export function previewText(session?: ExamSession) {
  const state = session?.preview?.status;
  if (!session?.package) return 'Chưa có đề hoàn chỉnh để xem trước PDF.';
  if (session.artifactChanged) return 'Tệp đề thi đã thay đổi. Thầy cô cần tải lại dữ liệu hiện tại.';
  if (state === 'ready' && session.preview?.revision === session.package.revision &&
      session.preview?.contentHash === session.package.contentHash) return 'Đã mở chế độ xem PDF của phiên bản hiện tại.';
  if (state === 'failed' || state === 'unavailable') return session.previewError || 'Bản xem trước PDF đang gặp lỗi.';
  return 'Đã mở chế độ xem PDF. Bản xem trước đang được chuẩn bị.';
}
