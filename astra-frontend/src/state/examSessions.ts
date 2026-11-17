import type { ChatMessage, ExamPackage, ExamRequestParams, QuestionItem, GenerationProgress } from '../types/exam';
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
  errorCode?: string;
  package?: ExamPackage;
  requestId?: string;
  requestSignature?: string;
  progress?: GenerationProgress;
}

// Every asynchronous result is addressed to its originating session, never the selected tab.
export class ExamSessions {
  private sessions: ExamSession[] = [];
  private listeners = new Set<() => void>();
  private subscriptions = new Map<string, () => void>();
  private disposed = false;
  private service: IExamService;

  constructor(service: IExamService) {
    this.service = service;
    if (typeof localStorage !== 'undefined') {
      try {
        const saved = JSON.parse(localStorage.getItem('astra.sessions.v1') || '[]');
        if (Array.isArray(saved)) this.sessions = saved.filter(item => typeof item.id === 'string' && Array.isArray(item.messages));
      } catch { console.warn('Could not restore local exam workspaces'); }
    }
  }
  getSnapshot = () => this.sessions;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private emit() {
    if (typeof localStorage !== 'undefined') {
      try { localStorage.setItem('astra.sessions.v1', JSON.stringify(this.sessions)); }
      catch { console.warn('Could not save local exam workspaces'); }
    }
    this.listeners.forEach(listener => listener());
  }
  resume() {
    this.disposed = false;
    this.sessions.filter(session => session.status === 'generating' && session.jobId).forEach(session => {
      this.subscriptions.get(session.id)?.();
      this.watch(session.id, session.jobId!);
    });
  }
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
  remove(id: string) {
    this.subscriptions.get(id)?.();
    this.subscriptions.delete(id);
    this.sessions = this.sessions.filter(session => session.id !== id);
    this.emit();
  }
  setDraft(id: string, draft: string) { this.update(id, session => ({ ...session, draft })); }
  retractMessage(id: string, messageId: string) {
    this.update(id, session => {
      const index = session.messages.findIndex(message => message.id === messageId);
      return index < 0 ? session : { ...session, messages: session.messages.slice(0, index) };
    });
  }
  branchAtMessage(id: string, messageId: string) {
    const source = this.sessions.find(session => session.id === id);
    const index = source?.messages.findIndex(message => message.id === messageId) ?? -1;
    if (!source || index < 0) return null;
    const branch: ExamSession = {
      ...source,
      id: crypto.randomUUID(),
      title: `Nhánh · ${source.title}`,
      createdAt: new Date().toISOString(),
      messages: source.messages.slice(0, index + 1),
      draft: '',
      jobId: null, package: undefined, questions: [], meta: null, status: 'draft',
    };
    this.sessions = [branch, ...this.sessions];
    this.emit();
    return branch.id;
  }
  sendMessage(id: string, content: string) {
    const message = (role: ChatMessage['role'], text: string): ChatMessage => ({ id: crypto.randomUUID(), role, content: text, timestamp: new Date().toISOString() });
    this.update(id, session => ({ ...session, title: session.mode === 'custom' && !session.meta && session.messages.length === 0 ? content.slice(0, 72) : session.title, draft: '', messages: [...session.messages, message('user', content), message('assistant', session.status === 'complete' ? 'Đã ghi nhận yêu cầu chỉnh sửa cho đề này. Chỉnh sửa bằng hội thoại sẽ khả dụng khi kết nối dịch vụ AI.' : 'Đã ghi nhận yêu cầu cho đề này. Chọn “Tạo đề từ yêu cầu” để chọn môn học, cấu trúc và bắt đầu tạo đề.')] }));
  }
  async generate(id: string, params: ExamRequestParams) {
    const existing = this.sessions.find(session => session.id === id);
    if (!existing || existing.status === 'generating') return;
    this.subscriptions.get(id)?.();
    const requestSignature = JSON.stringify(params);
    const requestId = existing.errorCode === 'network_error' && existing.requestSignature === requestSignature
      ? existing.requestId || crypto.randomUUID() : crypto.randomUUID();
    this.update(id, session => ({ ...session, requestId, requestSignature, status: 'generating', error: undefined, errorCode: undefined, package: undefined, questions: [], previousCount: 0, title: session.mode === 'template' ? `Đề thi ${params.subject}` : session.title, meta: { title: `Đề thi ${params.subject}`, subject: params.subject, duration: params.durationMinutes, completedCount: 0, totalCount: params.itemCount } }));
    try {
      const { jobId } = await this.service.startGeneration({ ...params, clientRequestId: requestId });
      if (this.disposed || !this.sessions.some(session => session.id === id)) return;
      this.update(id, session => ({ ...session, jobId }));
      this.watch(id, jobId);
    } catch (error) { this.fail(id, error); }
  }
  private watch(id: string, jobId: string) {
    let finishing = false;
    const unsubscribe = this.service.onProgress(jobId, progress => {
        if (this.disposed || finishing || !this.sessions.some(session => session.id === id && session.jobId === jobId)) return;
        if (progress.status === 'failed') {
          finishing = true;
          const error = Object.assign(new Error(progress.error?.message || progress.statusMessage), { code: progress.error?.code });
          this.fail(id, error);
          this.subscriptions.get(id)?.(); this.subscriptions.delete(id);
          return;
        }
        this.update(id, session => {
          const item = progress.latestItemPreview;
          const append = item && !session.questions.some(question => question.id === item.id);
          return { ...session, progress, meta: session.meta ? { ...session.meta, completedCount: progress.completedItems, totalCount: progress.totalItems || session.meta.totalCount } : null, previousCount: append ? session.questions.length : session.previousCount, questions: append ? [...session.questions, item] : session.questions };
        });
        if (progress.status === 'completed' || progress.stage >= 5 && progress.percent >= 100) {
          finishing = true;
          void this.service.getExamPackage(jobId).then(pkg => {
            if (this.sessions.some(session => session.id === id && session.jobId === jobId)) this.complete(id, pkg);
          }).catch(error => this.fail(id, error)).finally(() => { this.subscriptions.get(id)?.(); this.subscriptions.delete(id); });
        }
      });
      this.subscriptions.set(id, unsubscribe);
  }
  async refresh(id: string) {
    const session = this.sessions.find(item => item.id === id);
    if (!session?.jobId) return;
    const pkg = await this.service.getExamPackage(session.jobId);
    const current = this.sessions.find(item => item.id === id);
    if (current?.jobId === session.jobId && (current.package?.revision || 0) <= (pkg.revision || 0)) this.complete(id, pkg);
  }
  setError(id: string, error: unknown) { this.update(id, session => ({ ...session, error: error instanceof Error ? error.message : 'Có lỗi xảy ra' })); }
  private complete(id: string, pkg: ExamPackage) {
    this.update(id, session => ({ ...session, package: pkg, error: undefined, status: 'complete', title: session.mode === 'custom' ? session.title : pkg.title, questions: pkg.questions, meta: { title: pkg.title, subject: pkg.subject, duration: pkg.durationMinutes, completedCount: pkg.questions.length, totalCount: pkg.questions.length }, messages: session.status === 'complete' ? session.messages : [...session.messages, { id: crypto.randomUUID(), role: 'assistant', content: `Đã soạn xong ${pkg.questions.length} câu. Hãy kiểm tra và phê duyệt bản hiện tại trước khi xuất file.`, timestamp: new Date().toISOString() }] }));
  }
  private fail(id: string, error?: unknown) {
    this.update(id, session => ({ ...session, status: 'error', error: error instanceof Error ? error.message : 'Chưa tạo được đề. Hãy kiểm tra kết nối và thử lại.', errorCode: error && typeof error === 'object' && 'code' in error ? String(error.code) : undefined }));
  }
  dispose() { this.disposed = true; this.subscriptions.forEach(stop => stop()); this.subscriptions.clear(); }
}
