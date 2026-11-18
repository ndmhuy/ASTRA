import type { ChatMessage, ExamPackage, ExamPreviewState, ExamRequestParams, QuestionItem, GenerationProgress } from '../types/exam';
import type { IExamService } from '../services/examService';
import type { DeferredAgentNote } from '../agent/contracts';

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
  preview?: ExamPreviewState;
  previewOpenedRevision?: string | null;
  previewLog?: string;
  previewError?: string;
  previewErrorCode?: string;
  artifactChanged?: boolean;
  requestId?: string;
  requestSignature?: string;
  progress?: GenerationProgress;
  agentNotes: DeferredAgentNote[];
}

function previewBindingKey(jobId: string, revision: number, contentHash: string): string {
  return `${jobId}:${revision}:${contentHash}`;
}

function formatPreviewError(code?: string): string {
  switch (code) {
    case 'latex_compile_timeout':
      return 'Biên dịch PDF quá thời gian (có thể do lần đầu tải gói TeX). Hãy thử biên dịch lại.';
    case 'preview_interrupted':
      return 'Quá trình biên dịch PDF bị gián đoạn. Hãy thử biên dịch lại từ nguồn đã lưu.';
    case 'preview_artifact_changed':
      return 'Tệp PDF xem trước bị thay đổi ngoài luồng. Hãy thử biên dịch lại.';
    case 'latex_compiler_unavailable':
      return 'Máy chủ chưa có trình biên dịch LaTeX (Tectonic/XeLaTeX/LuaLaTeX). Kiểm tra cài đặt backend; không cần tạo lại đề.';
    default:
      return 'Biên dịch LaTeX thất bại. Kiểm tra nhật ký biên dịch hoặc sửa câu hỏi rồi thử lại.';
  }
}

function extractErrorDetails(error: unknown): { code?: string; message: string } {
  const code = error && typeof error === 'object' && 'code' in error && typeof error.code === 'string'
    ? error.code
    : undefined;
  const message = error instanceof Error ? error.message : 'Có lỗi xảy ra';
  return { code, message };
}

// Every asynchronous result is addressed to its originating session, never the selected tab.
export class ExamSessions {
  private sessions: ExamSession[] = [];
  private listeners = new Set<() => void>();
  private subscriptions = new Map<string, () => void>();
  private previewTimers = new Map<string, ReturnType<typeof setTimeout>>();
  private activeSessionId: string | null = null;
  private disposed = false;
  private service: IExamService;

  constructor(service: IExamService) {
    this.service = service;
    if (typeof localStorage !== 'undefined') {
      try {
        const saved = JSON.parse(localStorage.getItem('astra.sessions.v1') || '[]');
        if (Array.isArray(saved)) this.sessions = saved
          .filter(item => typeof item.id === 'string' && Array.isArray(item.messages))
          .map(item => ({ ...item, agentNotes: Array.isArray(item.agentNotes) ? item.agentNotes : [] }));
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
  private stopPreviewPoll(id: string) {
    const timer = this.previewTimers.get(id);
    if (timer) {
      clearTimeout(timer);
      this.previewTimers.delete(id);
    }
  }

  setActiveSession(id: string | null) {
    this.activeSessionId = id;
    for (const sessionId of Array.from(this.previewTimers.keys())) {
      if (sessionId !== id) {
        this.stopPreviewPoll(sessionId);
      }
    }
    if (!id) return;
    const session = this.sessions.find(item => item.id === id);
    if (
      session &&
      session.status === 'complete' &&
      session.jobId &&
      session.package?.revision &&
      session.package?.contentHash &&
      !session.artifactChanged &&
      this.service.requestPreview
    ) {
      const status = session.preview?.status;
      if (!status || status === 'not_requested' || status === 'queued' || status === 'compiling') {
        void this.requestPreview(id);
      }
    }
  }

  invalidatePreview(id: string) {
    this.stopPreviewPoll(id);
    this.update(id, session => ({
      ...session,
      preview: undefined,
      previewOpenedRevision: null,
      previewLog: undefined,
      previewError: undefined,
      previewErrorCode: undefined,
      package: session.package
        ? { ...session.package, approved: false, approval: null, preview: undefined }
        : undefined,
    }));
  }

  markPreviewOpened(id: string) {
    const session = this.sessions.find(item => item.id === id);
    const revision = session?.package?.revision;
    const contentHash = session?.package?.contentHash;
    if (
      !session ||
      !session.jobId ||
      !revision ||
      !contentHash ||
      session.preview?.status !== 'ready' ||
      session.preview.revision !== revision ||
      session.preview.contentHash !== contentHash
    ) {
      return;
    }
    const key = previewBindingKey(session.jobId, revision, contentHash);
    if (session.previewOpenedRevision === key) return;
    this.update(id, item => ({ ...item, previewOpenedRevision: key }));
  }

  canApprove(id: string): boolean {
    const session = this.sessions.find(item => item.id === id);
    const revision = session?.package?.revision;
    const contentHash = session?.package?.contentHash;
    if (
      !session ||
      session.status !== 'complete' ||
      session.artifactChanged ||
      session.package?.approved ||
      !session.jobId ||
      !revision ||
      !contentHash ||
      session.preview?.status !== 'ready' ||
      session.preview.revision !== revision ||
      session.preview.contentHash !== contentHash
    ) {
      return false;
    }
    return session.previewOpenedRevision === previewBindingKey(session.jobId, revision, contentHash);
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
    this.sessions = [{ id, mode, title: `Đề ${number} · ${mode === 'custom' ? 'Theo yêu cầu' : 'Từ mẫu'}`, status: 'draft', createdAt: new Date().toISOString(), messages: [], questions: [], draft: '', jobId: null, meta: null, previousCount: 0, agentNotes: [] }, ...this.sessions];
    this.emit();
    return id;
  }
  remove(id: string) {
    this.subscriptions.get(id)?.();
    this.subscriptions.delete(id);
    this.stopPreviewPoll(id);
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
      preview: undefined, previewOpenedRevision: null, previewLog: undefined,
      previewError: undefined, previewErrorCode: undefined, artifactChanged: false,
      agentNotes: [],
    };
    this.sessions = [branch, ...this.sessions];
    this.emit();
    return branch.id;
  }
  private message(role: ChatMessage['role'], content: string): ChatMessage {
    return { id: crypto.randomUUID(), role, content, timestamp: new Date().toISOString() };
  }
  sendMessage(id: string, content: string) {
    this.update(id, session => ({
      ...session,
      title: session.mode === 'custom' && !session.meta && session.messages.length === 0 ? content.slice(0, 72) : session.title,
      draft: '',
      messages: [...session.messages, this.message('user', content)],
    }));
  }
  addAssistantMessage(id: string, content: string) {
    this.update(id, session => ({ ...session, messages: [...session.messages, this.message('assistant', content)] }));
  }
  addNote(id: string, input: { targetQuestion?: number; requestedChange: string; teacherText: string }): DeferredAgentNote | null {
    const session = this.sessions.find(item => item.id === id);
    if (!session || session.status !== 'generating') return null;
    const now = new Date().toISOString();
    const note: DeferredAgentNote = {
      id: crypto.randomUUID(), workspaceId: id, jobId: session.jobId,
      targetQuestion: input.targetQuestion || null,
      requestedChange: input.requestedChange.trim(), teacherText: input.teacherText,
      status: 'pending', createdAt: now, updatedAt: now,
    };
    this.update(id, item => ({ ...item, agentNotes: [...item.agentNotes, note] }));
    return note;
  }
  updateNote(id: string, noteId: string, requestedChange: string): boolean {
    const session = this.sessions.find(item => item.id === id);
    if (!session?.agentNotes.some(note => note.id === noteId && note.status === 'pending')) return false;
    const updatedAt = new Date().toISOString();
    this.update(id, item => ({ ...item, agentNotes: item.agentNotes.map(note => note.id === noteId ? { ...note, requestedChange: requestedChange.trim(), updatedAt } : note) }));
    return true;
  }
  cancelNote(id: string, noteId: string): boolean {
    const session = this.sessions.find(item => item.id === id);
    if (!session?.agentNotes.some(note => note.id === noteId && note.status === 'pending')) return false;
    const updatedAt = new Date().toISOString();
    this.update(id, item => ({ ...item, agentNotes: item.agentNotes.map(note => note.id === noteId ? { ...note, status: 'cancelled', updatedAt } : note) }));
    return true;
  }
  async generate(id: string, params: ExamRequestParams) {
    const existing = this.sessions.find(session => session.id === id);
    if (!existing || existing.status === 'generating') return;
    this.subscriptions.get(id)?.();
    this.stopPreviewPoll(id);
    const requestSignature = JSON.stringify(params);
    const requestId = existing.errorCode === 'network_error' && existing.requestSignature === requestSignature
      ? existing.requestId || crypto.randomUUID() : crypto.randomUUID();
    this.update(id, session => ({
      ...session,
      requestId,
      requestSignature,
      status: 'generating',
      error: undefined,
      errorCode: undefined,
      package: undefined,
      preview: undefined,
      previewOpenedRevision: null,
      previewLog: undefined,
      previewError: undefined,
      previewErrorCode: undefined,
      artifactChanged: false,
      questions: [],
      previousCount: 0,
      title: session.mode === 'template' ? `Đề thi ${params.subject}` : session.title,
      meta: { title: `Đề thi ${params.subject}`, subject: params.subject, duration: params.durationMinutes, completedCount: 0, totalCount: params.itemCount }
    }));
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
  async requestPreview(id: string, force = false, allowReloadOnStale = true): Promise<void> {
    const session = this.sessions.find(item => item.id === id);
    const revision = session?.package?.revision;
    const contentHash = session?.package?.contentHash;
    if (
      !session ||
      !session.jobId ||
      !revision ||
      !contentHash ||
      session.artifactChanged ||
      !this.service.requestPreview
    ) {
      return;
    }
    const jobId = session.jobId;
    const binding = { revision, contentHash };
    this.stopPreviewPoll(id);
    this.update(id, item => ({
      ...item,
      previewError: undefined,
      previewErrorCode: undefined,
      previewLog: undefined,
    }));
    if (
      !force &&
      session.preview?.status === 'ready' &&
      session.preview.revision === revision &&
      session.preview.contentHash === contentHash
    ) {
      return;
    }
    try {
      const state = await this.service.requestPreview(jobId, binding);
      await this.applyPreviewState(id, jobId, binding, state);
    } catch (error) {
      await this.handlePreviewRequestError(id, jobId, binding, error, allowReloadOnStale);
    }
  }

  private async pollPreview(
    id: string,
    jobId: string,
    binding: { revision: number; contentHash: string },
    statusUrl?: string
  ): Promise<void> {
    this.previewTimers.delete(id);
    const latest = this.sessions.find(item => item.id === id);
    if (
      this.disposed ||
      !latest ||
      latest.jobId !== jobId ||
      latest.package?.revision !== binding.revision ||
      latest.package?.contentHash !== binding.contentHash ||
      latest.artifactChanged ||
      (this.activeSessionId !== null && this.activeSessionId !== id)
    ) {
      return;
    }
    try {
      const state = this.service.getPreviewStatus
        ? await this.service.getPreviewStatus(jobId, binding, statusUrl)
        : await this.service.requestPreview!(jobId, binding);
      await this.applyPreviewState(id, jobId, binding, state);
    } catch (error) {
      await this.handlePreviewRequestError(id, jobId, binding, error, true);
    }
  }

  private async applyPreviewState(
    id: string,
    jobId: string,
    binding: { revision: number; contentHash: string },
    state: ExamPreviewState
  ): Promise<void> {
    const latest = this.sessions.find(item => item.id === id);
    if (
      this.disposed ||
      !latest ||
      latest.jobId !== jobId ||
      latest.package?.revision !== binding.revision ||
      latest.package?.contentHash !== binding.contentHash ||
      latest.artifactChanged
    ) {
      return;
    }
    this.update(id, item => ({
      ...item,
      preview: state,
      package: item.package ? { ...item.package, preview: state } : item.package,
    }));
    if (state.status === 'queued' || state.status === 'compiling') {
      if (this.activeSessionId === null || this.activeSessionId === id) {
        this.stopPreviewPoll(id);
        const timer = setTimeout(() => {
          void this.pollPreview(id, jobId, binding, state.statusUrl);
        }, 1200);
        this.previewTimers.set(id, timer);
      }
      return;
    }
    this.stopPreviewPoll(id);
    if (state.status === 'failed' || state.status === 'unavailable') {
      await this.handleTerminalPreviewState(id, jobId, binding, state);
    }
  }

  private async handleTerminalPreviewState(
    id: string,
    jobId: string,
    binding: { revision: number; contentHash: string },
    state: ExamPreviewState
  ): Promise<void> {
    const code = state.status === 'unavailable'
      ? 'latex_compiler_unavailable'
      : state.error || 'latex_compile_failed';
    const message = formatPreviewError(code);
    this.update(id, item => ({
      ...item,
      previewErrorCode: code,
      previewError: message,
    }));
    if (state.status === 'failed' && state.logUrl && this.service.getPreviewLog) {
      const logText = await this.service.getPreviewLog(state.logUrl);
      const latest = this.sessions.find(item => item.id === id);
      if (
        this.disposed ||
        !latest ||
        latest.jobId !== jobId ||
        latest.package?.revision !== binding.revision ||
        latest.package?.contentHash !== binding.contentHash
      ) {
        return;
      }
      this.update(id, item => ({ ...item, previewLog: logText }));
    }
  }

  private async handlePreviewRequestError(
    id: string,
    jobId: string,
    binding: { revision: number; contentHash: string },
    error: unknown,
    allowReloadOnStale: boolean
  ): Promise<void> {
    const latest = this.sessions.find(item => item.id === id);
    if (
      this.disposed ||
      !latest ||
      latest.jobId !== jobId ||
      latest.package?.revision !== binding.revision ||
      latest.package?.contentHash !== binding.contentHash
    ) {
      return;
    }
    const { code, message } = extractErrorDetails(error);
    if ((code === 'stale_revision' || code === 'stale_hash') && allowReloadOnStale) {
      await this.handleActionError(id, error);
      return;
    }
    if (code === 'artifact_changed') {
      await this.handleActionError(id, error);
      return;
    }
    if (code === 'latex_compiler_unavailable') {
      this.update(id, item => ({
        ...item,
        previewErrorCode: 'latex_compiler_unavailable',
        previewError: message || formatPreviewError('latex_compiler_unavailable'),
        preview: item.preview
          ? { ...item.preview, status: 'unavailable', compilerAvailable: false }
          : undefined,
      }));
      return;
    }
    this.update(id, item => ({
      ...item,
      previewErrorCode: code || 'preview_request_failed',
      previewError: message,
    }));
  }

  async handleActionError(id: string, error: unknown): Promise<void> {
    const { code, message } = extractErrorDetails(error);
    if (code === 'stale_revision' || code === 'stale_hash') {
      try {
        await this.refresh(id);
        this.update(id, session => ({
          ...session,
          errorCode: code,
          error: 'Đề thi đã chuyển sang phiên bản mới. Đã tải lại dữ liệu và khởi động lại xem trước PDF.',
        }));
      } catch (refreshError) {
        const details = extractErrorDetails(refreshError);
        this.update(id, session => ({
          ...session,
          errorCode: details.code || code,
          error: details.message,
        }));
      }
      return;
    }
    if (code === 'artifact_changed') {
      this.stopPreviewPoll(id);
      this.update(id, session => ({
        ...session,
        artifactChanged: true,
        errorCode: 'artifact_changed',
        error: message || 'Nguồn LaTeX đã thay đổi bên ngoài phiên làm việc. Không thể phê duyệt hoặc xuất file.',
        previewErrorCode: 'artifact_changed',
        previewError: message || 'Nguồn LaTeX đã thay đổi ngoài luồng xử lý.',
      }));
      return;
    }
    if (code === 'preview_not_ready') {
      this.stopPreviewPoll(id);
      this.update(id, session => ({
        ...session,
        preview: undefined,
        previewOpenedRevision: null,
        errorCode: 'preview_not_ready',
        error: 'Bản xem trước PDF của phiên bản hiện tại chưa sẵn sàng. Đang biên dịch lại...',
      }));
      await this.requestPreview(id, true);
      return;
    }
    if (code === 'approval_required') {
      this.update(id, session => ({
        ...session,
        errorCode: 'approval_required',
        error: 'Vui lòng mở xem trước PDF và phê duyệt phiên bản hiện tại trước khi xuất file.',
      }));
      return;
    }
    if (code === 'latex_compiler_unavailable') {
      this.update(id, session => ({
        ...session,
        errorCode: 'latex_compiler_unavailable',
        error: message || formatPreviewError('latex_compiler_unavailable'),
        previewErrorCode: 'latex_compiler_unavailable',
        previewError: message || formatPreviewError('latex_compiler_unavailable'),
      }));
      return;
    }
    this.update(id, session => ({ ...session, error: message, errorCode: code }));
  }

  setError(id: string, error: unknown) {
    const { code, message } = extractErrorDetails(error);
    this.update(id, session => ({ ...session, error: message, errorCode: code }));
  }
  private complete(id: string, pkg: ExamPackage) {
    const prev = this.sessions.find(session => session.id === id);
    const bindingChanged =
      !prev?.package ||
      prev.package.revision !== pkg.revision ||
      prev.package.contentHash !== pkg.contentHash;
    if (bindingChanged) {
      this.stopPreviewPoll(id);
    }
    this.update(id, session => ({
      ...session,
      package: pkg,
      error: undefined,
      errorCode: undefined,
      status: 'complete',
      title: session.mode === 'custom' ? session.title : pkg.title,
      questions: pkg.questions,
      meta: { title: pkg.title, subject: pkg.subject, duration: pkg.durationMinutes, completedCount: pkg.questions.length, totalCount: pkg.questions.length },
      preview: pkg.preview,
      ...(bindingChanged
        ? {
            previewOpenedRevision: null,
            previewLog: undefined,
            previewError: undefined,
            previewErrorCode: undefined,
            artifactChanged: false,
          }
        : {}),
      messages: session.status === 'complete'
        ? session.messages
        : [...session.messages, this.message('assistant', session.agentNotes.some(note => note.status === 'pending')
          ? `Đã soạn xong ${pkg.questions.length} câu. Có ${session.agentNotes.filter(note => note.status === 'pending').length} ghi chú đang chờ; hãy xem lại, sửa hoặc hủy ghi chú trước khi điều chỉnh từng câu. Ghi chú chưa được tự động áp dụng.`
          : `Đã soạn xong ${pkg.questions.length} câu. Hãy kiểm tra bản xem trước PDF và phê duyệt bản hiện tại trước khi xuất file.`)],
    }));
    if (this.service.requestPreview && pkg.revision && pkg.contentHash) {
      const status = pkg.preview?.status;
      if (!status || status === 'not_requested' || status === 'queued' || status === 'compiling') {
        if (this.activeSessionId === null || this.activeSessionId === id) {
          void this.requestPreview(id, false, false);
        }
      } else if ((status === 'failed' || status === 'unavailable') && pkg.preview) {
        const jobId = prev?.jobId || pkg.examId;
        void this.handleTerminalPreviewState(
          id,
          jobId,
          { revision: pkg.revision, contentHash: pkg.contentHash },
          pkg.preview
        );
      }
    }
  }
  private fail(id: string, error?: unknown) {
    this.stopPreviewPoll(id);
    this.update(id, session => ({ ...session, status: 'error', error: error instanceof Error ? error.message : 'Chưa tạo được đề. Hãy kiểm tra kết nối và thử lại.', errorCode: error && typeof error === 'object' && 'code' in error ? String(error.code) : undefined }));
  }
  dispose() {
    this.disposed = true;
    this.subscriptions.forEach(stop => stop());
    this.subscriptions.clear();
    this.previewTimers.forEach(timer => clearTimeout(timer));
    this.previewTimers.clear();
  }
}
