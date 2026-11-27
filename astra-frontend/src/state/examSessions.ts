import type { ChatMessage, ExamPackage, ExamPreviewState, ExamRequestParams, QuestionItem, GenerationProgress } from '../types/exam';
import type { IExamService, SavedWorkspace, WorkspaceDraft } from '../services/examService';
import { conversationFor, suggestedTitle, titleFrom, touched, type Conversation } from '../agent/memory.ts';
import type { Intake } from '../agent/intake.ts';
import { reconcileNotes, type Note } from '../agent/notes.ts';
import { formatProgressStatus, humanizeErrorMessage } from '../utils/userMessages.ts';

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
  generationId?: string;
  generationError?: string;
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
  conversation?: Conversation;
  intake?: Intake;
  notes?: Note[];
  browserOnly?: boolean;
}

interface WorkspaceSave {
  revision: number;
  saved?: string;
  unconfirmed?: { draft: WorkspaceDraft; encoded: string };
  pending?: Promise<boolean>;
  archiving?: boolean;
  error?: string;
}

const LEGACY_SESSIONS_KEY = 'astra.sessions.v1';
const AGENT_MEMORY_KEY = 'astra.agent.workspaces.v1';
type AgentMemory = Pick<ExamSession, 'conversation' | 'intake' | 'notes'>;
const agentMemory = ({ conversation, intake, notes }: AgentMemory): AgentMemory => ({ conversation, intake, notes });
const BROWSER_ID_PREFIX = 'browser:';

function originalId(session: ExamSession) {
  return session.browserOnly ? session.id.slice(BROWSER_ID_PREFIX.length) : session.id;
}

const importMarker = (id: string) => `${LEGACY_SESSIONS_KEY}.imported.${id}`;

function newestFirst(first: ExamSession, second: ExamSession) {
  return String(second.createdAt ?? '').localeCompare(String(first.createdAt ?? '')) ||
    first.id.localeCompare(second.id);
}

function workspaceDraft({ mode, title, draft, messages }: ExamSession): WorkspaceDraft {
  return { schema_version: 1, mode, title, draft,
    messages: messages.filter(message => message.recorded || !message.id.startsWith('exam-ready:')) };
}

function sharedSession(entry: SavedWorkspace, previous?: ExamSession, memory?: AgentMemory): ExamSession {
  const { id, mode, createdAt, title, draft, messages, jobId, jobMeta, jobStatus } = entry;
  const jobError = entry.jobError;
  const status = jobStatus === 'completed' ? 'complete' : jobStatus === 'failed' ? 'error' : jobId ? 'generating' : 'draft';
  const sameJob = previous?.jobId === jobId;
  const notice = sameJob && previous?.messages.find(message => message.id === `exam-ready:${jobId}`);
  return {
    questions: [], previousCount: 0,
    ...agentMemory(previous ?? memory ?? {}),
    ...(sameJob ? previous : undefined),
    id, mode, createdAt, title, draft, messages: notice ? [...messages, notice] : messages, jobId, status,
    generationId: entry.generationStatus === 'queued' || entry.generationStatus === 'running'
      ? entry.generationId ?? undefined : undefined,
    generationError: status === 'complete' && entry.generationError
      ? humanizeErrorMessage(entry.generationError.message, entry.generationError.code) : undefined,
    meta: sameJob && previous?.meta ? previous.meta : jobMeta && {
      title: `Đề thi ${jobMeta.subject}`, subject: jobMeta.subject, duration: jobMeta.durationMinutes,
      completedCount: status === 'complete' ? jobMeta.itemCount : 0, totalCount: jobMeta.itemCount,
    },
    error: jobError ? humanizeErrorMessage(jobError.message, jobError.code) : undefined,
    errorCode: jobError?.code,
  };
}

function previewBindingKey(jobId: string, revision: number, contentHash: string): string {
  return `${jobId}:${revision}:${contentHash}`;
}

function formatPreviewError(code?: string): string {
  switch (code) {
    case 'latex_compile_timeout':
      return 'Quá trình tạo bản in PDF mất nhiều thời gian hơn dự kiến. Thầy cô hãy bấm thử tạo lại bản xem trước.';
    case 'preview_interrupted':
      return 'Quá trình tạo bản xem trước PDF bị gián đoạn. Thầy cô hãy bấm thử lại.';
    case 'preview_artifact_changed':
      return 'Tệp bản xem trước bị thay đổi ngoài luồng. Thầy cô hãy bấm tạo lại bản xem trước.';
    case 'latex_compiler_unavailable':
      return 'Máy chủ chưa cài đặt bộ tạo bản in PDF. Không cần tạo lại đề, hãy liên hệ người phụ trách kỹ thuật.';
    default:
      return 'Chưa tạo được bản xem trước PDF. Thầy cô hãy kiểm tra lại các câu hỏi hoặc thử tạo lại bản xem trước.';
  }
}

function extractErrorDetails(error: unknown): { code?: string; message: string } {
  const code = error && typeof error === 'object' && 'code' in error && typeof error.code === 'string'
    ? error.code
    : undefined;
  const rawMessage = error instanceof Error ? error.message : 'Có lỗi xảy ra';
  return { code, message: humanizeErrorMessage(rawMessage, code) };
}

// Every asynchronous result is addressed to its originating session, never the selected tab.
export class ExamSessions {
  private sessions: ExamSession[] = [];
  private listeners = new Set<() => void>();
  private subscriptions = new Map<string, () => void>();
  private previewTimers = new Map<string, ReturnType<typeof setTimeout>>();
  private activeSessionId: string | null = null;
  private disposed = false;
  private storageImage: string | null = null;
  private agentImage: string | null = null;
  private agentMemories = new Map<string, AgentMemory>();
  private storageReadOnly = false;
  storageWarning = '';
  private readonly storageChanged = (event: StorageEvent) => {
    if (event.key !== LEGACY_SESSIONS_KEY && event.key !== AGENT_MEMORY_KEY && event.key !== null) return;
    if (event.key !== null && event.newValue === (event.key === AGENT_MEMORY_KEY ? this.agentImage : this.storageImage)) return;
    this.storageReadOnly = true;
    this.storageWarning = 'Tủ đề đã được cập nhật trong tab khác. Hãy tải lại trang để tiếp tục lưu.';
    this.sessions = [...this.sessions];
    this.listeners.forEach(listener => listener());
  };
  private service: IExamService;
  private workspaceSaves = new Map<string, WorkspaceSave>();
  private starting = new Set<string>();
  private libraryRequest = 0;
  private libraryError = '';
  private localSnapshot: string;
  private browserBackups = new Map<string, ExamSession>();
  private browserImport = { pending: false, message: '' };

  constructor(service: IExamService) {
    this.service = service;
    if (typeof localStorage !== 'undefined') {
      try {
        this.storageImage = localStorage.getItem('astra.sessions.v1');
        if (service.workspaceLibrary) {
          this.agentImage = localStorage.getItem(AGENT_MEMORY_KEY);
          const cached = JSON.parse(this.agentImage ?? '{"schemaVersion":1,"workspaces":[]}');
          if (cached.schemaVersion !== 1 || !Array.isArray(cached.workspaces) || cached.workspaces.some(
            (entry: unknown) => !Array.isArray(entry) || typeof entry[0] !== 'string' || !entry[1] || typeof entry[1] !== 'object'
          )) throw new Error('Invalid local Agent memory');
          this.agentMemories = new Map(cached.workspaces);
        }
        const saved = JSON.parse(this.storageImage ?? '[]');
        if (!Array.isArray(saved) || saved.some(item => !item || typeof item.id !== 'string' ||
            typeof item.title !== 'string' || !Array.isArray(item.messages))) {
          this.storageReadOnly = true;
          this.storageWarning = 'Một phần tủ đề chưa đọc được. Dữ liệu cũ vẫn được giữ trong trình duyệt.';
        }
        if (Array.isArray(saved)) {
          this.sessions = saved
            .filter(item => item && typeof item.id === 'string' && typeof item.title === 'string' && Array.isArray(item.messages))
            .map(item => ({
              ...item,
              id: service.workspaceLibrary ? BROWSER_ID_PREFIX + item.id : item.id,
              browserOnly: !!service.workspaceLibrary,
              conversation: conversationFor(item),
              error: item.error ? humanizeErrorMessage(item.error, item.errorCode) : item.error,
              progress: item.progress
                ? {
                    ...item.progress,
                    statusMessage: formatProgressStatus(item.progress.statusMessage),
                  }
                : item.progress,
            }))
            .filter((session: ExamSession) => {
              if (!session.browserOnly || localStorage.getItem(importMarker(originalId(session))) !== '1') return true;
              this.browserBackups.set(session.id, session);
              return false;
            });
        }
      } catch {
        this.storageReadOnly = true;
        this.storageWarning = 'Chưa đọc được tủ đề. Dữ liệu cũ vẫn được giữ trong trình duyệt.';
      }
    }
    this.localSnapshot = this.serializeLocal();
  }
  getSnapshot = () => this.sessions;
  getLibraryError = () => this.libraryError || [...this.workspaceSaves.values()].find(state => state.error)?.error || '';
  getBrowserImport = () => this.browserImport;
  importedWorkspaceId(id: string) {
    const backup = this.browserBackups.get(id);
    const sharedId = backup && originalId(backup);
    return sharedId && this.workspaceSaves.has(sharedId) ? sharedId : null;
  }
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private serializeLocal() {
    return JSON.stringify([
      ...this.browserBackups.values(),
      ...this.sessions.filter(session => !this.workspaceSaves.has(session.id)),
    ].sort(newestFirst).map(session => ({ ...session, id: originalId(session) })));
  }

  private emit() {
    if (typeof localStorage !== 'undefined' && !this.storageReadOnly) {
      try {
        if (localStorage.getItem(LEGACY_SESSIONS_KEY) !== this.storageImage ||
            (this.service.workspaceLibrary && localStorage.getItem(AGENT_MEMORY_KEY) !== this.agentImage)) {
          this.storageReadOnly = true;
          this.storageWarning = 'Tủ đề đã thay đổi trong tab khác. Hãy tải lại trang để tiếp tục lưu.';
        } else {
          const next = this.serializeLocal();
          if (next !== this.localSnapshot) {
            localStorage.setItem(LEGACY_SESSIONS_KEY, next);
            this.storageImage = next;
            this.localSnapshot = next;
          }
          if (this.service.workspaceLibrary) {
            for (const session of this.sessions.filter(item => this.workspaceSaves.has(item.id))) {
              this.agentMemories.set(session.id, agentMemory(session));
            }
            const agent = JSON.stringify({ schemaVersion: 1, workspaces: [...this.agentMemories] });
            if (agent !== this.agentImage) localStorage.setItem(AGENT_MEMORY_KEY, agent);
            this.agentImage = agent;
          }
          this.storageWarning = '';
        }
      } catch {
        this.storageWarning = 'Trình duyệt chưa lưu được thay đổi. Hãy giữ tab này mở và kiểm tra dung lượng lưu trữ.';
      }
    }
    this.listeners.forEach(listener => listener());
  }
  resume() {
    this.disposed = false;
    if (typeof window !== 'undefined') window.addEventListener('storage', this.storageChanged);
    for (const session of this.sessions.filter(item => item.status === 'generating' && !item.jobId)) {
      this.fail(session.id, Object.assign(new Error('Chưa nhận được mã công việc từ máy chủ.'), { code: 'network_error' }));
    }
    this.resumeGeneration();
    void this.loadLibrary();
  }

  loadLibrary = async () => {
    const library = this.service.workspaceLibrary;
    if (!library) return;
    const request = ++this.libraryRequest;
    const before = new Map(this.sessions.map(session => [session.id, session]));
    try {
      const { workspaces } = await library.list();
      if (this.disposed || request !== this.libraryRequest) return;
      const entries = new Map(workspaces.map(entry => [entry.id, entry]));
      const sessions = this.sessions.flatMap(session => {
        const state = this.workspaceSaves.get(session.id);
        if (!state || state.pending || state.unconfirmed || state.archiving || this.starting.has(session.id) ||
            before.get(session.id) !== session || state.saved !== JSON.stringify(workspaceDraft(session))) return [session];
        const entry = entries.get(session.id);
        if (!entry) {
          this.stopWatching(session.id);
          this.workspaceSaves.delete(session.id);
          return [];
        }
        if (entry.revision < state.revision) return [session];
        const loaded = sharedSession(entry, session);
        if (entry.jobId !== session.jobId || loaded.generationId !== session.generationId) this.stopWatching(session.id);
        state.revision = entry.revision;
        state.saved = JSON.stringify(workspaceDraft(loaded));
        return [loaded];
      });
      const known = new Set(sessions.map(session => session.id));
      for (const entry of workspaces) {
        if (known.has(entry.id)) continue;
        const legacy = this.sessions.find(item => item.browserOnly && originalId(item) === entry.id);
        const session = sharedSession(entry, undefined, legacy ?? this.agentMemories.get(entry.id));
        this.workspaceSaves.set(entry.id, { revision: entry.revision, saved: JSON.stringify(workspaceDraft(session)) });
        sessions.push(session);
      }
      this.sessions = sessions.sort(newestFirst);
      this.libraryError = '';
      this.emit();
      this.resumeGeneration();
      if (this.activeSessionId) this.refreshSavedExam(this.activeSessionId);
      return entries;
    } catch {
      if (this.disposed || request !== this.libraryRequest) return;
      this.libraryError = 'Chưa tải được tủ đề từ máy chủ.';
      this.emit();
    }
  };

  private resumeGeneration() {
    for (const session of this.sessions) {
      const jobId = session.generationId ?? (session.status === 'generating' ? session.jobId : null);
      if (jobId && !this.subscriptions.has(session.id) && !this.starting.has(session.id)) this.watch(session.id, jobId);
    }
  }

  importBrowserLibrary = async () => {
    const library = this.service.workspaceLibrary;
    const sources = this.sessions.filter(session => session.browserOnly);
    if (!library || this.browserImport.pending || !sources.length) return;
    this.browserImport = { pending: true, message: '' };
    this.emit();

    const accepted = new Map<string, { data: string; status: 'imported' | 'existing' }>();
    let missing = 0;
    let conflicts = 0;
    let unconfirmed = 0;
    for (const session of sources) {
      try {
        const payload = {
          ...workspaceDraft(session), createdAt: session.createdAt, jobId: session.jobId ?? null,
        };
        const { status } = await library.importLegacy(originalId(session), payload);
        accepted.set(session.id, { data: JSON.stringify(payload), status });
      } catch (error) {
        const { code } = extractErrorDetails(error);
        if (code === 'workspace_import_missing_job') missing++;
        else if (code === 'workspace_import_conflict') conflicts++;
        else unconfirmed++;
      }
    }

    const visible = await this.loadLibrary();
    let added = 0;
    let existing = 0;
    this.sessions = this.sessions.filter(session => {
      const receipt = accepted.get(session.id);
      if (!receipt) return true;
      const id = originalId(session);
      if (!visible?.has(id)) {
        unconfirmed++;
        return true;
      }
      const current = { ...workspaceDraft(session), createdAt: session.createdAt, jobId: session.jobId ?? null };
      if (JSON.stringify(current) !== receipt.data) {
        conflicts++;
        return true;
      }
      this.stopWatching(session.id);
      this.browserBackups.set(session.id, session);
      try { localStorage.setItem(importMarker(id), '1'); }
      catch { console.warn('Could not remember the imported exam in this browser'); }
      if (receipt.status === 'imported') added++;
      else existing++;
      return false;
    });

    const message = [
      added > 0 && `Đã nhập ${added} đề.`,
      existing > 0 && `${existing} đề đã có trong tủ đề chung.`,
      missing > 0 && `Không tìm thấy tệp hoặc phiên tạo của ${missing} đề trên máy chủ.`,
      conflicts > 0 && `Giữ riêng ${conflicts} bản có xung đột với tủ đề chung.`,
      unconfirmed > 0 && `Chưa xác nhận ${unconfirmed} đề. Hãy thử nhập lại.`,
      'Bản sao vẫn được giữ trên trình duyệt này.',
    ].filter(Boolean).join(' ');
    this.browserImport = { pending: false, message };
    this.emit();
  };

  retryLibrary = async () => {
    await Promise.all([...this.workspaceSaves.keys()].map(id => this.saveWorkspace(id)));
    await this.loadLibrary();
  };

  private saveWorkspace(id: string): Promise<boolean> {
    const state = this.workspaceSaves.get(id);
    const library = this.service.workspaceLibrary;
    if (!state || !library || state.archiving) return Promise.resolve(true);
    state.pending ??= Promise.resolve().then(async () => {
      try {
        let session = this.sessions.find(item => item.id === id);
        while (session && !state.archiving) {
          const draft = workspaceDraft(session);
          const encoded = JSON.stringify(draft);
          if (!state.unconfirmed && encoded === state.saved) break;
          state.unconfirmed ??= { draft, encoded };
          const { revision } = await library.save(id, state.unconfirmed.draft, state.revision);
          state.revision = revision;
          state.saved = state.unconfirmed.encoded;
          state.unconfirmed = undefined;
          session = this.sessions.find(item => item.id === id);
        }
        state.error = undefined;
        return true;
      } catch (error) {
        const { code } = extractErrorDetails(error);
        if (code !== 'network_error') state.unconfirmed = undefined;
        state.error = code === 'workspace_changed' || code === 'workspace_not_found'
          ? 'Đề đã thay đổi trong cửa sổ khác. Hãy sao chép phần chưa lưu trước khi tải lại trang.'
          : 'Chưa lưu được bản nháp vào máy chủ.';
        return false;
      } finally {
        state.pending = undefined;
        this.emit();
      }
    });
    return state.pending;
  }

  private refreshSavedExam(id: string) {
    if (this.workspaceSaves.has(id) && this.sessions.find(session => session.id === id)?.status === 'complete') {
      void this.refresh(id).catch(error => this.setError(id, error));
    }
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
    if (this.workspaceSaves.has(id)) {
      this.refreshSavedExam(id);
      return;
    }
    const session = this.sessions.find(item => item.id === id);
    if (session?.status === 'complete' && this.service.verifyQuestion &&
        session.questions.some(question => !question.answerCheck)) {
      void this.refresh(id).catch(error => this.setError(id, error));
      return;
    }
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

  private update(id: string, change: (session: ExamSession) => ExamSession, save = false) {
    if (this.disposed) return;
    this.sessions = this.sessions.map(session => session.id === id ? change(session) : session);
    this.emit();
    if (save) void this.saveWorkspace(id);
  }
  create(mode: ExamSession['mode']) {
    this.disposed = false;
    const id = crypto.randomUUID();
    const number = this.sessions.length + 1;
    if (this.service.workspaceLibrary) this.workspaceSaves.set(id, { revision: 0 });
    this.sessions = [{ id, mode, title: `Đề ${number} · ${mode === 'custom' ? 'Theo yêu cầu' : 'Từ mẫu'}`, status: 'draft', createdAt: new Date().toISOString(), messages: [], questions: [], draft: '', jobId: null, meta: null, previousCount: 0 }, ...this.sessions];
    this.emit();
    void this.saveWorkspace(id);
    return id;
  }
  private stopWatching(id: string) {
    this.subscriptions.get(id)?.();
    this.subscriptions.delete(id);
    this.stopPreviewPoll(id);
  }

  async remove(id: string): Promise<boolean> {
    const state = this.workspaceSaves.get(id);
    if (state && this.service.workspaceLibrary) {
      if (state.archiving) return false;
      state.archiving = true;
      try {
        await state.pending;
        await this.service.workspaceLibrary.archive(id);
        this.workspaceSaves.delete(id);
        this.libraryRequest++;
        this.libraryError = '';
      } catch {
        state.archiving = false;
        this.libraryError = 'Chưa xóa được đề khỏi tủ đề. Hãy thử xóa lại.';
        this.emit();
        return false;
      }
    }
    this.stopWatching(id);
    this.agentMemories.delete(id);
    this.sessions = this.sessions.filter(session => session.id !== id);
    this.emit();
    if (state) void this.loadLibrary();
    return true;
  }
  setDraft(id: string, draft: string) { this.update(id, session => ({ ...session, draft }), true); }
  rename(id: string, value: string) {
    const title = titleFrom(value);
    if (!title) return false;
    this.update(id, session => ({ ...session, title, conversation: { ...touched(session), titleOrigin: 'manual' } }), true);
    return this.sessions.find(session => session.id === id)?.title === title;
  }
  suggestTitle(id: string, value: string, sourceId: string, quality = 1) {
    this.update(id, session => {
      const conversation = conversationFor(session);
      if (conversation.titleOrigin === 'manual' || conversation.titleOrigin === 'legacy' ||
          (conversation.titleQuality ?? 0) >= quality ||
          session.messages.filter(message => message.role === 'user' && !/^(chào(?: em)?|xin chào|hello|hi)[ !.]*$/iu.test(message.content)).length > 3) return session;
      const source = session.messages.find(message => message.id === sourceId && message.role === 'user');
      const title = source && suggestedTitle(value, source.content);
      if (!title) return session;
      return { ...session, title, conversation: {
        ...conversation, titleOrigin: 'auto', titleSourceId: sourceId, titleQuality: quality,
      } };
    }, true);
  }

  setIntake(id: string, intake: Intake | undefined) { this.update(id, session => ({ ...session, intake })); }
  rememberQuestion(id: string, stableId: string, jobId: string, revision: number, sourceId: string) {
    this.update(id, session => session.jobId === jobId && session.package?.revision === revision &&
      session.messages.some(message => message.id === sourceId && message.role === 'user')
      ? { ...session, conversation: { ...touched(session), questionReference: { sourceId, stableId, jobId, revision } } } : session);
  }
  setNotes(id: string, notes: Note[]) { this.update(id, session => ({ ...session, notes })); }
  retractMessage(id: string, messageId: string) {
    this.update(id, session => {
      const index = session.messages.findIndex(message => message.id === messageId);
      if (index < 0) return session;
      const messages = session.messages.slice(0, index);
      const ids = new Set(messages.map(message => message.id));
      const conversation = touched(session);
      if (conversation.questionReference && !ids.has(conversation.questionReference.sourceId)) conversation.questionReference = undefined;
      const titleLost = conversation.titleOrigin === 'auto' && conversation.titleSourceId && !ids.has(conversation.titleSourceId);
      return {
        ...session, messages,
        title: titleLost ? 'Cuộc trò chuyện mới' : session.title,
        conversation: titleLost ? { ...conversation, titleOrigin: 'default', titleSourceId: undefined, titleQuality: undefined } : conversation,
        intake: session.intake && (session.intake.sourceIds ?? [session.intake.sourceId]).every(source => ids.has(source))
          ? session.intake : undefined,
        notes: session.notes?.filter(note => note.status === 'applied' || ids.has(note.sourceId)),
      };
    }, true);
  }
  private branchRequests = new Map<string, string>();

  async branchAtMessage(id: string, messageId: string, copyCurrent = false) {
    const source = this.sessions.find(session => session.id === id);
    if (!source) return null;
    const library = this.service.workspaceLibrary;
    if (library && this.workspaceSaves.has(id)) {
      if (!await this.saveWorkspace(id)) throw new Error('Hãy lưu hội thoại trước khi tạo nhánh.');
      const key = JSON.stringify([id, messageId, copyCurrent]);
      const destinationId = this.branchRequests.get(key) ?? crypto.randomUUID();
      this.branchRequests.set(key, destinationId);
      try {
        const { workspaceId } = await library.branch(id, destinationId, messageId, copyCurrent);
        await this.loadLibrary();
        if (!this.sessions.some(item => item.id === workspaceId)) {
          throw Object.assign(new Error('Nhánh đã lưu. Hãy thử tải lại tủ đề.'), { code: 'network_error' });
        }
        this.update(workspaceId, child => {
          const ids = new Set(child.messages.map(message => message.id));
          const conversation = touched(source);
          const lostTitle = conversation.titleOrigin === 'auto' && conversation.titleSourceId && !ids.has(conversation.titleSourceId);
          return { ...child, conversation: { ...conversation, revision: 0, questionReference: undefined,
            ...(lostTitle ? { titleOrigin: 'default', titleSourceId: undefined, titleQuality: undefined } : {}) },
            intake: source.intake && (source.intake.sourceIds ?? [source.intake.sourceId]).every(id => ids.has(id))
              ? { ...source.intake, phase: source.intake.formatId ? 'selected' : 'collecting' } : undefined,
            notes: undefined };
        });
        this.branchRequests.delete(key);
        return workspaceId;
      } catch (error) {
        if (extractErrorDetails(error).code !== 'network_error') this.branchRequests.delete(key);
        throw error;
      }
    }
    if (source.browserOnly && source.jobId) throw new Error('Hãy nhập đề vào tủ đề chung trước khi tạo nhánh.');
    const index = source?.messages.findIndex(message => message.id === messageId) ?? -1;
    if (!source || index < 0) return null;
    const prefix = source.messages.slice(0, index + 1);
    const ids = new Set(prefix.map(message => message.id));
    const conversation = touched(source);
    const titleLost = conversation.titleOrigin === 'auto' && conversation.titleSourceId && !ids.has(conversation.titleSourceId);
    const branch: ExamSession = {
      ...source,
      conversation: { ...conversation, titleOrigin: titleLost ? 'default' : conversation.titleOrigin,
        questionReference: undefined,
        titleSourceId: titleLost ? undefined : conversation.titleSourceId,
        titleQuality: titleLost ? undefined : conversation.titleQuality, revision: 0 },
      intake: source.intake && (source.intake.sourceIds ?? [source.intake.sourceId]).every(sourceId => ids.has(sourceId))
        ? { ...source.intake, phase: source.intake.formatId ? 'selected' : 'collecting' } : undefined,
      notes: undefined, progress: undefined, previousCount: 0, requestId: undefined,
      requestSignature: undefined, error: undefined, errorCode: undefined,
      id: crypto.randomUUID(),
      browserOnly: false,
      title: titleLost ? 'Cuộc trò chuyện mới' : 'Nhánh · ' + source.title,
      createdAt: new Date().toISOString(),
      messages: prefix,
      draft: '',
      jobId: null, package: undefined, questions: [], meta: null, status: 'draft',
      preview: undefined, previewOpenedRevision: null, previewLog: undefined,
      previewError: undefined, previewErrorCode: undefined, artifactChanged: false,
    };
    if (this.service.workspaceLibrary) this.workspaceSaves.set(branch.id, { revision: 0 });
    this.sessions = [branch, ...this.sessions];
    this.emit();
    void this.saveWorkspace(branch.id);
    return branch.id;
  }
  appendMessage(id: string, role: ChatMessage['role'], content: string, messageId = crypto.randomUUID(), agentTurn = false) {
    this.update(id, session => {
      if (session.messages.some(message => message.id === messageId)) return session;
      const conversation = touched(session);
      const examVersion = session.jobId && session.package?.revision
        ? { jobId: session.jobId, revision: session.package.revision }
        : session.status === 'complete' ? undefined : null;
      const message: ChatMessage = { id: messageId, role, content, agentTurn, examVersion, timestamp: conversation.updatedAt };
      return {
        ...session, conversation,
        draft: role === 'user' ? '' : session.draft,
        messages: [...session.messages, message],
      };
    }, true);
  }
  sendMessage(id: string, content: string) { this.appendMessage(id, 'user', content); }
  async generate(id: string, params: ExamRequestParams) {
    const start = () => {
      if (this.storageReadOnly || (typeof localStorage !== 'undefined' &&
        localStorage.getItem('astra.sessions.v1') !== this.storageImage)) {
        this.setError(id, new Error('Tủ đề đã thay đổi trong tab khác. Hãy tải lại trước khi tạo đề.'));
        return undefined;
      }
      return this.startGeneration(id, params);
    };
    if (typeof navigator !== 'undefined' && navigator.locks) {
      return navigator.locks.request(`astra-generate:${id}`, { ifAvailable: true }, lock => {
        if (lock) return start();
        const session = this.sessions.find(item => item.id === id);
        if (session?.status !== 'generating') this.setError(id, new Error('Một tab đang gửi yêu cầu cho đề này.'));
        return undefined;
      });
    }
    return start();
  }

  private async startGeneration(id: string, params: ExamRequestParams) {
    const existing = this.sessions.find(session => session.id === id);
    if (!existing || existing.status === 'generating' || existing.generationId || this.starting.has(id)) return;
    const shared = this.workspaceSaves.has(id);
    if (shared) {
      this.starting.add(id);
      const saved = await this.saveWorkspace(id);
      if (!saved || this.disposed || !this.workspaceSaves.has(id) || this.workspaceSaves.get(id)?.archiving) {
        this.starting.delete(id);
        return;
      }
    }
    this.subscriptions.get(id)?.();
    this.stopPreviewPoll(id);
    const requestSignature = JSON.stringify(params);
    const requestId = existing.errorCode === 'network_error' && existing.requestSignature === requestSignature
      ? existing.requestId || crypto.randomUUID() : crypto.randomUUID();
    const keepExam = shared && existing.status === 'complete';
    this.update(id, session => ({
      ...session,
      requestId,
      requestSignature,
      error: undefined,
      errorCode: undefined,
      progress: undefined,
      generationError: undefined,
      ...(keepExam ? {} : {
      status: 'generating',
      package: undefined,
      preview: undefined,
      previewOpenedRevision: null,
      previewLog: undefined,
      previewError: undefined,
      previewErrorCode: undefined,
      artifactChanged: false,
      questions: [],
      previousCount: 0,
      title: !shared && session.mode === 'template' ? `Đề thi ${params.subject}` : session.title,
      meta: { title: `Đề thi ${params.subject}`, subject: params.subject, duration: params.durationMinutes, completedCount: 0, totalCount: params.itemCount },
      }),
    }));
    try {
      if (this.storageWarning) {
        const error = this.storageWarning;
        this.fail(id, new Error(error));
        return undefined;
      }
      const { jobId } = await this.service.startGeneration({ ...params, clientRequestId: requestId }, shared ? id : undefined);
      if (this.disposed || !this.sessions.some(session => session.id === id)) return;
      this.update(id, session => ({ ...session, ...(keepExam ? { generationId: jobId } : { jobId }) }));
      this.watch(id, jobId);
      return jobId;
    } catch (error) { this.fail(id, error); }
    finally { this.starting.delete(id); }
  }
  private watch(id: string, jobId: string) {
    let finishing = false;
    let detach: (() => void) | undefined;
    const unsubscribe = () => detach?.();
    const stop = () => {
      if (this.subscriptions.get(id) !== unsubscribe) return;
      unsubscribe();
      this.subscriptions.delete(id);
    };
    this.subscriptions.set(id, unsubscribe);
    detach = this.service.onProgress(jobId, progress => {
        const session = this.sessions.find(item => item.id === id);
        if (this.disposed || finishing || !session || (session.generationId ?? session.jobId) !== jobId) return;
        if (progress.status === 'failed') {
          finishing = true;
          const rawMessage = progress.error?.message || progress.statusMessage;
          const error = Object.assign(
            new Error(humanizeErrorMessage(rawMessage, progress.error?.code)),
            { code: progress.error?.code }
          );
          this.fail(id, error);
          stop();
          return;
        }
        this.update(id, session => {
          if (session.progress && (progress.percent < session.progress.percent || progress.stage < session.progress.stage)) return session;
          if (session.generationId && session.generationId !== session.jobId) return { ...session, progress };
          const item = progress.latestItemPreview;
          const append = item && !session.questions.some(question => question.id === item.id);
          return { ...session, progress, meta: session.meta ? { ...session.meta, completedCount: progress.completedItems, totalCount: progress.totalItems || session.meta.totalCount } : null, previousCount: append ? session.questions.length : session.previousCount, questions: append ? [...session.questions, item] : session.questions };
        });
        if (progress.status === 'completed' || progress.stage >= 5 && progress.percent >= 100) {
          finishing = true;
          void this.service.getExamPackage(jobId).then(pkg => {
            if (this.sessions.some(session => session.id === id && (session.generationId ?? session.jobId) === jobId)) {
              if (session.jobId !== jobId) {
                this.update(id, current => ({ ...current, jobId, status: 'generating', generationId: undefined,
                  previewOpenedRevision: null, package: undefined }));
              }
              this.complete(id, pkg);
            }
          }).catch(error => {
            if (this.subscriptions.get(id) === unsubscribe) this.fail(id, error);
          }).finally(stop);
        }
      });
    if (this.subscriptions.get(id) !== unsubscribe) detach();
  }
  async refresh(id: string) {
    const session = this.sessions.find(item => item.id === id);
    if (!session?.jobId) return;
    const pkg = await this.service.getExamPackage(session.jobId);
    this.acceptPackage(id, session.jobId, pkg);
  }

  acceptPackage(id: string, jobId: string, pkg: ExamPackage) {
    const current = this.sessions.find(item => item.id === id);
    if (current?.jobId === jobId && (current.package?.revision || 0) <= (pkg.revision || 0)) this.complete(id, pkg);
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
        if (this.workspaceSaves.has(id)) await this.loadLibrary();
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
        error: 'Tệp đề thi đã bị thay đổi bên ngoài phiên làm việc nên không thể duyệt hoặc tải xuống.',
        previewErrorCode: 'artifact_changed',
        previewError: 'Tệp đề thi đã bị thay đổi ngoài luồng xử lý.',
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
    const shared = this.workspaceSaves.has(id);
    const noticeId = shared ? `exam-ready:${prev?.jobId}` : crypto.randomUUID();
    const notice = `Đã soạn xong ${pkg.questions.length} câu. Hãy kiểm tra bản xem trước PDF và phê duyệt bản hiện tại trước khi xuất file.`;
    const bindingChanged =
      !prev?.package ||
      prev.package.revision !== pkg.revision ||
      prev.package.contentHash !== pkg.contentHash;
    if (bindingChanged) {
      this.stopPreviewPoll(id);
    }
    this.update(id, session => ({
      ...session,
      notes: reconcileNotes(session.notes, pkg.examId, pkg.questions),
      package: pkg,
      generationId: session.generationId === session.jobId ? undefined : session.generationId,
      error: undefined,
      errorCode: undefined,
      status: 'complete',
      title: session.conversation?.titleOrigin === 'manual' || session.mode === 'custom' || shared ? session.title : pkg.title,
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
      messages: (session.status === 'complete' && (!shared || session.package)) ||
        session.messages.some(message => message.id === noticeId ||
          (session.status === 'complete' && message.role === 'assistant' && message.content === notice))
        ? session.messages
        : [...session.messages.filter(message => !message.id.startsWith('exam-ready:')), { id: noticeId, role: 'assistant', content: notice, timestamp: shared ? pkg.createdAt : new Date().toISOString() }],
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
    const code = error && typeof error === 'object' && 'code' in error ? String(error.code) : undefined;
    const rawMessage = error instanceof Error ? error.message : undefined;
    this.update(id, session => ({
      ...session,
      status: session.status === 'complete' ? 'complete' : 'error',
      generationId: undefined,
      [session.status === 'complete' ? 'generationError' : 'error']:
        rawMessage ? humanizeErrorMessage(rawMessage, code) : 'Chưa tạo được đề. Thầy cô hãy kiểm tra kết nối rồi thử lại.',
      notes: session.notes?.map(note => note.jobId === session.jobId && note.status === 'recorded'
        ? { ...note, status: 'unresolved' } : note),
      errorCode: code,
    }));
  }
  dispose() {
    this.disposed = true;
    if (typeof window !== 'undefined') window.removeEventListener('storage', this.storageChanged);
    this.subscriptions.forEach(stop => stop());
    this.subscriptions.clear();
    this.previewTimers.forEach(timer => clearTimeout(timer));
    this.previewTimers.clear();
  }
}
