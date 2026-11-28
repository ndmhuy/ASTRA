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
    if (state.status === 'paused') return { status: 'succeeded' as const, text: 'Đã tạm dừng và lưu phần đã soạn.' };
    if (state.status === 'pausing') return { status: 'accepted' as const, text: 'Đang lưu phần vừa soạn để tạm dừng. Bạn có thể xem tiến độ ngay trong đề.' };
  } else {
    if (state.status === 'running' || state.status === 'retrying') return { status: 'succeeded' as const, text: 'Đang soạn tiếp phần còn lại.' };
    if (state.status === 'resuming' || state.status === 'queued') return { status: 'accepted' as const, text: 'Yêu cầu tiếp tục đã được nhận. Lượt soạn sẽ nối từ phần đã lưu.' };
    if (state.status === 'completed') return { status: 'succeeded' as const, text: 'Đề đã soạn xong. Bạn có thể mở đề để kiểm tra.' };
  }
  return { status: 'failed' as const, text: state.error?.message || state.statusMessage || 'Mình chưa kiểm tra được kết quả. Bạn có thể mở đề để xem tiến độ.' };
}
