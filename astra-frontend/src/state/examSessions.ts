import type { ChatMessage, ExamPackage, ExamRequestParams, QuestionItem } from '../types/exam';
import type { IExamService } from '../services/examService';

export interface ExamSession {
  id: string;
  title: string;
  mode: 'template' | 'custom';
  status: 'draft' | 'generating' | 'complete' | 'error';
  createdAt: string;
  messages: ChatMessage[];
  questions: QuestionItem[];
  draft: string;
  jobId: string | null;
  meta: { title: string; subject: string; duration: number; completedCount: number; totalCount: number } | null;
  previousCount: number;
  error?: string;
}

// Every asynchronous result is addressed to its originating session, never the selected tab.
export class ExamSessions {
  private sessions: ExamSession[] = [];
  private listeners = new Set<() => void>();
  private subscriptions = new Map<string, () => void>();
  private disposed = false;
  private service: IExamService;

  constructor(service: IExamService) { this.service = service; }
  getSnapshot = () => this.sessions;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private emit() { this.listeners.forEach(listener => listener()); }
  private update(id: string, change: (session: ExamSession) => ExamSession) {
    if (this.disposed) return;
    this.sessions = this.sessions.map(session => session.id === id ? change(session) : session);
    this.emit();
  }
  create(mode: ExamSession['mode']) {
    this.disposed = false;
    const id = crypto.randomUUID();
    const number = this.sessions.length + 1;
    this.sessions = [{ id, mode, title: `Đề ${number} · ${mode === 'custom' ? 'Theo yêu cầu' : 'Từ mẫu'}`, status: 'draft', createdAt: new Date().toISOString(), messages: [], questions: [], draft: '', jobId: null, meta: null, previousCount: 0 }, ...this.sessions];
    this.emit();
    return id;
  }
  setDraft(id: string, draft: string) { this.update(id, session => ({ ...session, draft })); }
  sendMessage(id: string, content: string) {
    const message = (role: ChatMessage['role'], text: string): ChatMessage => ({ id: crypto.randomUUID(), role, content: text, timestamp: new Date().toISOString() });
    this.update(id, session => ({ ...session, title: session.mode === 'custom' && !session.meta && session.messages.length === 0 ? content.slice(0, 72) : session.title, draft: '', messages: [...session.messages, message('user', content), message('assistant', session.status === 'complete' ? 'Đã ghi nhận yêu cầu chỉnh sửa cho đề này. Chỉnh sửa bằng hội thoại sẽ khả dụng khi kết nối dịch vụ AI.' : 'Đã ghi nhận yêu cầu cho đề này. Chọn “Tạo đề từ yêu cầu” để chọn môn học, cấu trúc và bắt đầu tạo đề.')] }));
  }
  async generate(id: string, params: ExamRequestParams) {
    const existing = this.sessions.find(session => session.id === id);
    if (!existing || existing.status === 'generating') return;
    this.subscriptions.get(id)?.();
    this.update(id, session => ({ ...session, status: 'generating', error: undefined, questions: [], previousCount: 0, title: session.mode === 'template' ? `Đề thi ${params.subject}` : session.title, meta: { title: `Đề thi ${params.subject}`, subject: params.subject, duration: params.durationMinutes, completedCount: 0, totalCount: params.itemCount } }));
    let finishing = false;
    try {
      const { jobId } = await this.service.startGeneration(params);
      if (this.disposed) return;
      this.update(id, session => ({ ...session, jobId }));
      const unsubscribe = this.service.onProgress(jobId, progress => {
        if (this.disposed || finishing) return;
        this.update(id, session => {
          const item = progress.latestItemPreview;
          const append = item && !session.questions.some(question => question.id === item.id);
          return { ...session, meta: session.meta ? { ...session.meta, completedCount: progress.completedItems, totalCount: progress.totalItems || session.meta.totalCount } : null, previousCount: append ? session.questions.length : session.previousCount, questions: append ? [...session.questions, item] : session.questions };
        });
        if (progress.stage >= 5 && progress.percent >= 100) {
          finishing = true;
          void this.service.getExamPackage(jobId).then(pkg => this.complete(id, pkg)).catch(() => this.fail(id)).finally(() => { this.subscriptions.get(id)?.(); this.subscriptions.delete(id); });
        }
      });
      this.subscriptions.set(id, unsubscribe);
    } catch { this.fail(id); }
  }
  private complete(id: string, pkg: ExamPackage) {
    this.update(id, session => ({ ...session, status: 'complete', title: session.mode === 'custom' ? session.title : pkg.title, questions: pkg.questions, meta: { title: pkg.title, subject: pkg.subject, duration: pkg.durationMinutes, completedCount: pkg.questions.length, totalCount: pkg.questions.length }, messages: [...session.messages, { id: crypto.randomUUID(), role: 'assistant', content: `Đã soạn xong ${pkg.questions.length} câu. Bạn có thể kiểm tra đề, xem đáp án và xuất file.`, timestamp: new Date().toISOString() }] }));
  }
  private fail(id: string) { this.update(id, session => ({ ...session, status: 'error', error: 'Chưa tạo được đề. Hãy kiểm tra kết nối và thử lại.' })); }
  dispose() { this.disposed = true; this.subscriptions.forEach(stop => stop()); this.subscriptions.clear(); }
}
