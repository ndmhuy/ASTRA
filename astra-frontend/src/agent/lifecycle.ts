import type { ExamSession } from '../state/examSessions.ts';
import type { GenerationProgress } from '../types/exam.ts';
import { fold } from './language.ts';

export const activeGeneration = (status: GenerationProgress['status'] | null | undefined) =>
  !!status && ['queued', 'running', 'pausing', 'resuming', 'retrying'].includes(status);
export const restingGeneration = (status: GenerationProgress['status'] | null | undefined) =>
  !!status && ['paused', 'interrupted', 'cancelled', 'failed'].includes(status);
export const generationJob = (session: ExamSession) => session.generationId ?? session.stoppedJobId ??
  (session.status === 'generating' ? session.jobId : undefined);

export function generationTarget(sessions: ExamSession[], currentId: string | null, operation: 'pause' | 'cancel' | 'resume' | 'retry' | 'status', title?: string) {
  const matches = (session: ExamSession) => {
    if (!generationJob(session)) return false;
    const status = session.progress?.status;
    return operation === 'status' || (operation === 'pause' || operation === 'cancel'
      ? activeGeneration(status) || (!status && !!session.generationId)
      : restingGeneration(status) || session.generationStopped);
  };
  const current = sessions.find(session => session.id === currentId);
  if (title) {
    const name = fold(title);
    const exact = sessions.filter(session => fold(session.title) === name);
    const candidates = (exact.length ? exact : sessions.filter(session => fold(session.title).includes(name))).filter(matches);
    return candidates.length === 1 ? { target: candidates[0] }
      : { text: candidates.length ? 'Có nhiều phiên khớp tên này. Thầy cô hãy chọn đúng một đề.' : 'Không tìm thấy phiên phù hợp với tên đề và thao tác này.' };
  }
  if (current && matches(current)) return { target: current };
  const candidates = sessions.filter(matches);
  return candidates.length === 1 ? { target: candidates[0] }
    : { text: candidates.length ? `Có ${candidates.length} phiên phù hợp. Thầy cô muốn thao tác với đề nào?`
      : 'Chưa có phiên phù hợp. Hãy mở đề đang chạy hoặc đã tạm dừng để xem trạng thái.' };
}

export function generationReceipt(operation: 'pause' | 'resume' | 'retry', state: GenerationProgress) {
  if (operation === 'pause') {
    if (state.status === 'paused') return { status: 'succeeded' as const, text: 'Backend đã tạm dừng và lưu kết quả hợp lệ.' };
    if (state.status === 'pausing') return { status: 'accepted' as const, text: 'Backend đã nhận yêu cầu tạm dừng; đang đợi lưu phản hồi đang gọi. Chưa phải trạng thái đã dừng.' };
  } else {
    if (state.status === 'running' || state.status === 'retrying') return { status: 'succeeded' as const, text: 'Backend xác nhận đang tiếp tục phần công việc còn thiếu.' };
    if (state.status === 'resuming' || state.status === 'queued') return { status: 'accepted' as const, text: 'Backend đã nhận yêu cầu tiếp tục từ checkpoint; đang chờ executor bắt đầu.' };
    if (state.status === 'completed') return { status: 'succeeded' as const, text: 'Backend xác nhận phiên này đã hoàn tất.' };
  }
  return { status: 'failed' as const, text: state.error?.message || state.statusMessage || 'Backend chưa xác nhận trạng thái yêu cầu.' };
}
