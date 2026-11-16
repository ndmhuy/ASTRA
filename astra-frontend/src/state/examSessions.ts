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
  agentPending: boolean;
  agentError?: string;
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
    this.sessions = [{ id, mode, title: `Đề ${number} · ${mode === 'custom' ? 'Theo yêu cầu' : 'Từ mẫu'}`, status: 'draft', createdAt: new Date().toISOString(), messages: [], questions: [], draft: '', jobId: null, meta: null, previousCount: 0, agentPending: false }, ...this.sessions];
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
      status: source.status === 'generating' ? 'draft' : source.status,
      messages: source.messages.slice(0, index + 1),
      draft: '',
      agentPending: false,
      agentError: undefined,
    };
    this.sessions = [branch, ...this.sessions];
    this.emit();
    return branch.id;
  }
  private message(role: ChatMessage['role'], content: string): ChatMessage {
    return { id: crypto.randomUUID(), role, content, timestamp: new Date().toISOString() };
  }
  appendUserMessage(id: string, content: string) {
    this.update(id, session => ({
      ...session,
      title: session.mode === 'custom' && !session.meta && session.messages.length === 0 ? content.slice(0, 72) : session.title,
      draft: '',
      agentError: undefined,
      messages: [...session.messages, this.message('user', content)],
    }));
  }
  appendAssistantMessage(id: string, content: string) {
    this.update(id, session => ({ ...session, messages: [...session.messages, this.message('assistant', content)] }));
  }
  setAgentPending(id: string, pending: boolean) {
    this.update(id, session => ({ ...session, agentPending: pending, agentError: pending ? undefined : session.agentError }));
  }
  setAgentError(id: string, error: string) {
    this.update(id, session => ({ ...session, agentPending: false, agentError: error }));
  }
  // Compatibility helper for callers that only need to record a user message.
  sendMessage(id: string, content: string) { this.appendUserMessage(id, content); }
  async generate(id: string, params: ExamRequestParams) {
    const existing = this.sessions.find(session => session.id === id);
    if (!existing || existing.status === 'generating') return;
    this.subscriptions.get(id)?.();
    this.update(id, session => ({ ...session, status: 'generating', error: undefined, questions: [], previousCount: 0, title: session.mode === 'template' ? `Đề thi ${params.subject}` : session.title, meta: { title: `Đề thi ${params.subject}`, subject: params.subject, duration: params.durationMinutes, completedCount: 0, totalCount: params.itemCount } }));
    let finishing = false;
    try {
      const { jobId } = await this.service.startGeneration(params);
      if (this.disposed || !this.sessions.some(session => session.id === id)) return;
      this.update(id, session => ({ ...session, jobId }));
      const unsubscribe = this.service.onProgress(jobId, progress => {
        if (this.disposed || finishing || !this.sessions.some(session => session.id === id)) return;
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
