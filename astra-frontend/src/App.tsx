import React, { useState, useEffect, useSyncExternalStore, useCallback, useLayoutEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
import { meaningful, redact, retrievedContext, searchSessions } from './agent/memory';
import { interpret } from './agent/client';
import { admit, execute, fastRoute, fold, mayDispatch, type Effect, type Runtime } from './agent/recipes';
import { displayNumber, failure, previewText, resolveQuestion, sectionId, statusText, success } from './agent/examActions';
import type { Intent } from './agent/contracts';
import { AlertCircle, AlertTriangle, LoaderCircle, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { WorkspaceStart } from './components/WorkspaceStart';
import { AstraWelcome } from './components/AstraWelcome';
import { SidebarExamLibrary } from './components/SidebarExamLibrary';
import { AstraLogo } from './components/AstraLogo';
import { QuickPresetModal } from './components/QuickPresetModal';
import { WorkspaceLayout } from './components/Workspace/WorkspaceLayout';
import { ChatHistory } from './components/Workspace/ChatPane/ChatHistory';
import { ModernChatBar } from './components/Workspace/ChatPane/ModernChatBar';
import { CanvasHeader } from './components/Workspace/LiveCanvas/CanvasHeader';
import { ExamPaperView, type ExamCanvasViewMode, type ExamPaperControls } from './components/Workspace/LiveCanvas/ExamPaperView';
import type { ExamFormat, ExamRequestParams, QuestionItem } from './types/exam';
import { QuestionEditor } from './components/QuestionEditor';
import { evaluateExamFormat, examService, getExamFormats } from './services/examService';
import { prepareParams } from './agent/intake';
import { noteLabel, type Note } from './agent/notes';
import { ExamSessions } from './state/examSessions';
import { formatProgressStatus, formatVisualWarning } from './utils/userMessages.ts';
import './styles/workspace.css';
import './styles/classroom.css';
import './styles/studio.css';
import './styles/createVision.css';
import './styles/integratedWorkspace.css';
import './styles/integration.css';
import './styles/atelier.css';

type EditorTarget = { sessionId: string; jobId: string; question: QuestionItem };
type Confirmation = {
  workspaceId: string;
  binding: string;
  expires: number;
  run: () => Promise<Effect> | Effect;
};

export const App: React.FC = () => {
  const [showWelcome, setShowWelcome] = useState(true);
  const finishWelcome = useCallback(() => setShowWelcome(false), []);
  const [landingDraft, setLandingDraft] = useState('');
  const [leavingStart, setLeavingStart] = useState(false);
  const [revealingWorkspace, setRevealingWorkspace] = useState(false);
  const transitionTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const composerOrigin = useRef<DOMRect | null>(null);
  const [store] = useState(() => new ExamSessions(examService));
  const sessions = useSyncExternalStore(store.subscribe, store.getSnapshot);
  const turn = useRef<AbortController | null>(null);
  const [admissionError, setAdmissionError] = useState('');
  const pending = useRef<Confirmation | null>(null);
  const canvas = useRef<ExamPaperControls>(null);
  const editorBusy = useRef(new Set<string>());
  const [agentOpenedPdf, setAgentOpenedPdf] = useState(false);
  const presetDialog = useRef<HTMLDivElement>(null);
  const renderEpoch = useRef({ version: 0, state: '' });
  const activeRef = useRef<string | null>(null);
  const runtimeRef = useRef<Runtime | null>(null);
  const [chatPending, setChatPending] = useState(false);
  const cancelTurn = () => { turn.current?.abort(); turn.current = null; pending.current = null; setChatPending(false); };
  useEffect(() => () => turn.current?.abort(), []);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [screen, setScreen] = useState<'start' | 'workspace'>('start');
  const [viewMode, setViewMode] = useState<ExamCanvasViewMode>('paper');
  const [controlsCollapsed, setControlsCollapsed] = useState(false);
  const [showQuickModal, setShowQuickModal] = useState(false);
  const [agentSelection, setAgentSelection] = useState<{ formats: ExamFormat[]; id: string; expanded: boolean; summary?: string }>();
  const [configureId, setConfigureId] = useState<string | null>(null);
  const [editor, setEditor] = useState<EditorTarget | null>(null);
  const [approving, setApproving] = useState(false);
  const closeQuickModal = useCallback(() => {
    turn.current?.abort();
    turn.current = null;
    pending.current = null;
    setChatPending(false);
    setShowQuickModal(false);
    setAgentSelection(undefined);
  }, []);
  const active = sessions.find(session => session.id === activeId);
  const messages = active?.messages || [];
  const liveQuestions = active?.questions || [];
  const examMeta = active?.meta || null;
  const isGenerating = active?.status === 'generating';
  const prevQuestionCount = active?.previousCount || 0;
  useEffect(() => { store.resume(); return () => store.dispose(); }, [store]);
  useEffect(() => {
    store.setActiveSession(screen === 'workspace' ? activeId : null);
  }, [store, screen, activeId]);
  useEffect(() => () => { if (transitionTimer.current) clearTimeout(transitionTimer.current); }, []);
  const cancelTransition = () => { composerOrigin.current = null; if (transitionTimer.current) clearTimeout(transitionTimer.current); setLeavingStart(false); setRevealingWorkspace(false); };
  const openSession = (id: string) => { cancelTransition(); setAgentOpenedPdf(false); setViewMode('paper'); setActiveId(id); setScreen('workspace'); };
  const openManually = (id: string) => { cancelTurn(); setAgentSelection(undefined); setShowQuickModal(false); setConfigureId(null); setEditor(null); openSession(id); };
  const newExam = () => { cancelTurn(); cancelTransition(); setActiveId(null); setConfigureId(null); setLandingDraft(''); setAgentSelection(undefined); setShowQuickModal(false); setScreen('start'); };
  const revealSession = (id: string) => {
    if (screen === 'workspace') { openSession(id); return; }
    composerOrigin.current = document.querySelector('.integrated-start .composer-box')?.getBoundingClientRect() || null;
    setLeavingStart(true);
    transitionTimer.current = setTimeout(() => {
      setActiveId(id); setAgentOpenedPdf(false); setViewMode('paper'); setScreen('workspace'); setLeavingStart(false); setRevealingWorkspace(true);
      transitionTimer.current = setTimeout(() => setRevealingWorkspace(false), 420);
    }, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 180);
  };
  useLayoutEffect(() => {
    const from = composerOrigin.current;
    if (screen !== 'workspace' || !from) return;
    composerOrigin.current = null;
    const target = document.querySelector<HTMLElement>('.workspace-composer-slot .composer-box');
    if (!target || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const to = target.getBoundingClientRect();
    const animation = target.animate([{ transform: `translate(${from.left - to.left}px, ${from.top - to.top}px)`, width: `${from.width}px` }, { transform: 'translate(0, 0)', width: `${to.width}px` }], { duration: 360, easing: 'cubic-bezier(.2,.75,.25,1)' });
    return () => animation.cancel();
  }, [screen, activeId]);
  useLayoutEffect(() => {
    if (showWelcome || revealingWorkspace || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const view = document.querySelector<HTMLElement>(screen === 'workspace' ? '.astra-workspace-stage' : '.integrated-start');
    if (!view) return;
    const animation = view.animate([
      { opacity: 0, transform: 'translateY(8px)' },
      { opacity: 1, transform: 'translateY(0)' },
    ], { duration: 220, easing: 'cubic-bezier(.2,.75,.25,1)' });
    return () => animation.cancel();
    // Session updates and sidebar resizing must not replay the navigation animation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screen, activeId, showWelcome]);
  const handleDetailedStart = () => {
    const id = configureId || store.create('custom');
    store.setDraft(id, landingDraft);
    setShowQuickModal(false);
    setConfigureId(null);
    revealSession(id);
  };
  const sendTurn = async (id: string, content: string, options: { searchWeb: boolean; attachedFiles: File[] }) => {
    if (turn.current) return;
    const admission = admit(content);
    setAdmissionError(admission.error || '');
    if (admission.error) return;
    content = admission.text;
    const controller = new AbortController();
    turn.current = controller;
    setChatPending(true);
    const messageId = crypto.randomUUID();
    const answer = (text: string) => {
      if (store.getSnapshot().some(session => session.id === id)) store.appendMessage(id, 'assistant', text);
      else setAdmissionError(text);
    };
    flushSync(() => store.appendMessage(id, 'user', content, messageId, true));
    const runtime: Runtime = {
      binding: () => runtimeRef.current!.binding(),
      dispatch: (intent, expected, message, source) => runtimeRef.current!.dispatch(intent, expected, message, source),
    };
    const binding = runtime.binding();
    const origin = store.getSnapshot().find(s => s.id === id);
    const alive = () => !controller.signal.aborted && !!store.getSnapshot().find(s => s.id === id)?.messages.some(m => m.id === messageId);
    try {
      if (options.searchWeb || options.attachedFiles.length) {
        answer('ASTRA hiện chưa hỗ trợ tìm web hoặc tải tệp. Thầy cô có thể gửi nội dung dạng văn bản.');
        return;
      }
      await Promise.resolve();
      if (!alive()) return;
      const local = fastRoute(content);
      if (local && 'text' in local) { answer(local.text); return; }
      if (local && 'confirm' in local) {
        const prepared = pending.current;
        pending.current = null;
        if (!local.confirm) {
          answer(prepared ? 'Đã hủy thao tác đang chờ. Công việc đã gửi vẫn tiếp tục.' : 'Hiện chưa có tác vụ trò chuyện đang chờ.');
        } else if (!prepared || prepared.workspaceId !== id) {
          answer('Hiện chưa có thao tác nào đang chờ xác nhận.');
        } else if (prepared.expires < Date.now() || prepared.binding !== runtime.binding()) {
          answer('Xác nhận đã hết hiệu lực hoặc trạng thái đã thay đổi. Thầy cô hãy gửi lại yêu cầu.');
        } else {
          const effect = await prepared.run();
          if (alive() || !store.getSnapshot().some(session => session.id === id)) answer(effect.text);
        }
        return;
      }
      if (!local && !mayDispatch(content)) {
        answer('Thầy cô muốn em thực hiện thao tác cụ thể nào? Em chưa thao tác.');
        return;
      }
      const decision = local && 'intents' in local ? { kind: 'task', intents: local.intents }
        : await interpret(id, messageId, redact(content), {
          screen, setup: showQuickModal, status: origin?.status ?? 'draft', view: viewMode,
          ...(origin ? retrievedContext(origin, messageId, content) : {}),
          questionRefs: origin ? [...new Set(origin.questions.map(q => q.part ?? '').filter(Boolean))].slice(0, 8) : [],
          editor: Boolean(editor),
          approved: Boolean(origin?.package?.approved),
          preview: origin?.preview?.status ?? null,
        }, controller.signal);
      if (!alive()) return;
      if (decision.kind !== 'task') {
        answer(decision.kind === 'temporarily_unavailable'
          ? ('reasonCode' in decision && (decision.reasonCode === 'quota' || decision.reasonCode === 'budget')
            ? 'Trợ lý đang hết lượt hiểu yêu cầu. Thầy cô có thể dùng nút trong ASTRA hoặc thử lại sau.'
            : 'Dịch vụ hiểu yêu cầu đang chưa sẵn sàng. Thầy cô vẫn có thể dùng các nút trong ASTRA.')
          : decision.kind === 'unsupported'
            ? 'Tính năng này chưa có trong ASTRA.'
            : 'Thầy cô muốn thao tác nào trong ASTRA? Em cần thêm thông tin để thực hiện.');
        return;
      }
      if (decision.intents.some(intent => !['STATUS', 'WARNINGS', 'LIST_SESSIONS'].includes(intent.id))) {
        pending.current = null;
      }
      const literalNumbers = [...fold(content).matchAll(/\b(?:cau|question|tin nhan|message)\s+(\d+)\b/g)].map(match => Number(match[1]));
      if (decision.intents.some(intent => typeof intent.args.number === 'number' && !literalNumbers.includes(intent.args.number))) {
        answer('Thầy cô hãy ghi rõ số câu và phần thi để em xác định đúng câu.');
        return;
      }
      const receipts = await execute(decision.intents, runtime, binding, alive, content, messageId);
      if (!alive()) return;
      const stopped = receipts.length < decision.intents.length;
      answer([...receipts.map(receipt => receipt.text),
        ...(stopped ? ['Các bước tiếp theo chưa được thực hiện. Thầy cô hãy kiểm tra trạng thái hiện tại.'] : []),
      ].join('\n'));
    } catch (error) {
      if (!controller.signal.aborted) {
        const reason = error instanceof Error ? error.message : '';
        answer(reason === 'agent_rate' ? 'Trợ lý đang nhận quá nhiều yêu cầu. Thầy cô thử lại sau một lát.'
          : reason.startsWith('agent_') ? 'Chưa kết nối được dịch vụ hiểu yêu cầu. Thầy cô có thể dùng các nút trong ASTRA.'
            : 'Chưa xác định được kết quả của thao tác. Thầy cô hãy kiểm tra trạng thái trước khi thử lại.');
      }
    } finally {
      if (turn.current === controller) { turn.current = null; setChatPending(false); }
    }
  };
  const handleLandingSend = (content: string, options: { searchWeb: boolean; attachedFiles: File[] }) => {
    if (turn.current) return;
    const admission = admit(content);
    setAdmissionError(admission.error || '');
    if (admission.error) return;
    const quick = fastRoute(admission.text);
    const navigation = quick && 'intents' in quick && !options.searchWeb && !options.attachedFiles.length
      ? quick.intents[0] : undefined;
    if (navigation && ['HOME', 'SET_SIDEBAR', 'OPEN_SESSION'].includes(navigation.id)) {
      const effect = dispatch(navigation) as Effect;
      if (effect.status === 'failed') setAdmissionError(effect.text);
      else setLandingDraft('');
      return;
    }
    const id = configureId || store.create('custom');
    flushSync(() => { setLandingDraft(''); openSession(id); });
    if (navigation?.id === 'CREATE_SESSION') {
      store.appendMessage(id, 'user', admission.text);
      store.appendMessage(id, 'assistant', 'Đã mở một không gian soạn đề mới.');
      return;
    }
    void sendTurn(id, content, options);
  };
  const handleQuickStart = (params: ExamRequestParams) => {
    if (agentSelection?.summary) {
      const prepared = pending.current;
      pending.current = null;
      if (prepared?.workspaceId && prepared.workspaceId === configureId &&
          prepared.expires >= Date.now() && prepared.binding === runtimeRef.current?.binding() &&
          params.formatId === agentSelection.id) {
        void Promise.resolve(prepared.run()).then(effect => store.appendMessage(prepared.workspaceId, 'assistant', effect.text));
      } else {
        setAdmissionError('Xác nhận đã hết hiệu lực. Thầy cô hãy đóng cấu hình và gửi lại yêu cầu.');
      }
      return;
    }
    pending.current = null;
    const id = configureId || store.create('template');
    const session = store.getSnapshot().find(item => item.id === id);
    const instructions = session?.messages.filter(message => message.role === 'user' && !message.agentTurn).map(message => message.content).join('\n');
    setShowQuickModal(false);
    revealSession(id);
    setAgentSelection(undefined);
    void store.generate(id, { ...params, uploadedFiles: [], prompt: instructions ? `${params.prompt}\n${instructions}` : params.prompt });
  };
  const handleSendMessage = (content: string, options: { searchWeb: boolean; attachedFiles: File[] }) => {
    if (activeId) void sendTurn(activeId, content, options);
  };
  const exportFile = async (type: 'STUDENT_EXAM' | 'TEACHER_KEY', format: 'tex' | 'pdf' | 'json') => {
    const session = active;
    if (!session?.jobId) return false;
    try { await examService.downloadExport(session.jobId, type, format); return true; }
    catch (error) { await store.handleActionError(session.id, error); return false; }
  };
  const handleExportPdf = () => { void exportFile('STUDENT_EXAM', 'pdf'); };
  const handleExportWord = () => { void exportFile('STUDENT_EXAM', 'tex'); };
  const handleExportAnswer = () => { void exportFile('TEACHER_KEY', 'json'); };
  const approve = async () => {
    const session = active;
    if (!session?.jobId || !session.package || !examService.approveExam || !store.canApprove(session.id)) return false;
    setApproving(true);
    try {
      await examService.approveExam(session.jobId, session.package);
      await store.refresh(session.id);
      return store.getSnapshot().find(item => item.id === session.id)?.package?.approved === true;
    } catch (error) {
      await store.handleActionError(session.id, error);
      return false;
    }
    finally { setApproving(false); }
  };
  const handlePreviewOpened = useCallback(() => {
    if (activeId && !agentOpenedPdf) store.markPreviewOpened(activeId);
  }, [store, activeId, agentOpenedPdf]);
  const openPdfManually = () => { setAgentOpenedPdf(false); setViewMode('pdf'); };
  const handleRetryPreview = useCallback(() => {
    if (activeId) void store.requestPreview(activeId, true);
  }, [store, activeId]);


  const editQuestion = async (target: EditorTarget, kind: 'save' | 'verify' | 'regen', value?: QuestionItem | string) => {
    if (editorBusy.current.has(target.sessionId)) throw new Error('Đang xử lý một thao tác chỉnh sửa.');
    editorBusy.current.add(target.sessionId);
    try {
      if (kind === 'save') await examService.updateQuestion(target.jobId, value as QuestionItem);
      else if (kind === 'regen') await examService.regenerateQuestion(
        target.jobId, target.question.id, value as string, target.question.examRevision,
      );
      else if (examService.verifyQuestion && target.question.examRevision !== undefined) {
        await examService.verifyQuestion(target.jobId, target.question.id, target.question.examRevision);
      } else throw new Error('Tính năng kiểm tra lại hiện chưa sẵn sàng.');
      if (kind !== 'verify') store.invalidatePreview(target.sessionId);
      await store.refresh(target.sessionId);
      setEditor(current => current?.sessionId === target.sessionId && current?.question.id === target.question.id ? null : current);
      return store.getSnapshot().find(session => session.id === target.sessionId);
    } catch (error) {
      await store.handleActionError(target.sessionId, error);
      throw error;
    } finally {
      editorBusy.current.delete(target.sessionId);
    }
  };

  const binding = (versioned = true) => {
    const current = store.getSnapshot().find(s => s.id === activeId);
    return JSON.stringify([versioned ? renderEpoch.current.version : 0, screen, activeId, showQuickModal, configureId, controlsCollapsed, viewMode,
      editor?.question.stableId, current?.status, current?.jobId, current?.package?.revision,
      current?.package?.contentHash, current?.package?.approved, current?.previewOpenedRevision,
      current?.preview?.status, current?.artifactChanged,
      agentSelection?.id, agentSelection?.formats.find(format => format.id === agentSelection?.id)?.version,
      current?.intake, current?.notes,
      store.getSnapshot().map(item => [item.id, item.title])]);
  };
  const dispatch = (intent: Intent, expected?: string, message = '', messageId = ''): Effect | Promise<Effect> => {
    const failed = failure;
    const succeeded = success;
    const current = store.getSnapshot().find(session => session.id === activeId);
    const prepare = (text: string, run: Confirmation['run']): Effect => {
      if (!current) return failed('Hãy mở không gian soạn đề trước.');
      pending.current = { workspaceId: current.id, binding: binding(), expires: Date.now() + 5 * 60_000, run };
      return { status: 'pending', text: `${text} Nếu đồng ý, hãy nhắn “Xác nhận”.` };
    };
    switch (intent.id) {
      case 'OPEN_SETUP':
        if (!current || !['draft', 'error'].includes(current.status) || editor) return failed('Chỉ có thể mở cấu hình cho đề nháp hoặc lần tạo bị lỗi.');
        flushSync(() => { setAgentSelection(undefined); setConfigureId(current.id); setShowQuickModal(true); });
        return presetDialog.current
          ? succeeded('Đã mở phần cấu hình mẫu đề.')
          : failed('Chưa mở được phần cấu hình mẫu đề.');
      case 'HOME':
        flushSync(() => { cancelTransition(); setEditor(null); setShowQuickModal(false); setConfigureId(null); setActiveId(null); setScreen('start'); });
        return succeeded('Đã về màn hình bắt đầu.');
      case 'CREATE_SESSION': {
        const id = store.create('custom');
        flushSync(() => { setAgentSelection(undefined); setShowQuickModal(false); setConfigureId(null); setEditor(null); openSession(id); });
        return succeeded('Đã mở một không gian soạn đề mới.');
      }
      case 'OPEN_SESSION': {
        const title = typeof intent.args.title === 'string' ? fold(intent.args.title) : '';
        const eligible = store.getSnapshot().filter(item => item.id !== current?.id || title);
        const matches = title ? searchSessions(eligible, title)
          : eligible.slice().sort((a, b) => b.createdAt.localeCompare(a.createdAt));
        const target = matches[0];
        if (!target) return failed('Chưa tìm thấy đề phù hợp trong tủ đề trên trình duyệt này.');
        if (matches.length > 1 && (title || matches[1].createdAt === target.createdAt)) {
          return failed('Có nhiều đề phù hợp. Thầy cô hãy chọn đúng đề trong tủ đề.');
        }
        flushSync(() => { setShowQuickModal(false); setConfigureId(null); setEditor(null); openSession(target.id); });
        return succeeded(`Đã mở “${target.title}”.`);
      }
      case 'SET_SIDEBAR':
        if (window.matchMedia('(max-width: 800px)').matches) return failed('Chế độ thu gọn thanh điều hướng chỉ có trên màn hình rộng.');
        flushSync(() => setControlsCollapsed(intent.args.collapsed === true));
        return succeeded(intent.args.collapsed ? 'Đã thu gọn thanh điều hướng.' : 'Đã mở rộng thanh điều hướng.');
      case 'CLOSE_SETUP':
        if (!showQuickModal) return failed('Phần cấu hình đang đóng.');
        flushSync(() => { setShowQuickModal(false); setAgentSelection(undefined); });
        return succeeded('Đã đóng phần cấu hình.');
      case 'LIST_SESSIONS': {
        const title = typeof intent.args.title === 'string' ? fold(intent.args.title) : '';
        const matches = (title ? searchSessions(store.getSnapshot(), title) : store.getSnapshot()).slice(0, 8);
        return succeeded(matches.length ? matches.map(item => `• ${item.title}`).join('\n') : 'Chưa có đề phù hợp trong tủ đề.');
      }
      case 'RENAME': {
        const title = String(intent.args.title);
        if (!current || !fold(message).includes(fold(title))) return failed('Thầy cô hãy ghi rõ tên mới cho cuộc trò chuyện đang mở.');
        return store.rename(current.id, title)
          ? succeeded(`Đã đổi tên cuộc trò chuyện thành “${store.getSnapshot().find(item => item.id === current.id)?.title}”.`)
          : failed('Chưa đặt được tên đã yêu cầu.');
      }
      case 'RECALL': {
        if (!current) return failed('Hãy mở cuộc trò chuyện mà thầy cô muốn xem lại.');
        if (intent.args.what === 'format') {
          const source = current.messages.find(item => item.id === current.intake?.sourceId);
          if (!current.intake || !source) return failed('Cuộc trò chuyện này chưa lưu lựa chọn mẫu đề.');
          const label = current.intake.formatId === 'vact' ? 'V-ACT' : 'Toán THPT';
          return succeeded(`Mẫu gần nhất là ${label}. Yêu cầu gốc: “${source.content}”.`);
        }
        const first = current.messages.find(item => item.id !== messageId && meaningful(item)) ??
          current.messages.find(item => item.id !== messageId && item.role === 'user' &&
            !fastRoute(item.content));
        return first ? succeeded(`Yêu cầu đầu tiên của thầy cô: “${first.content}”`) : failed('Chưa tìm thấy yêu cầu trước đó trong chat này.');
      }
      case 'SET_DRAFT': {
        const value = String(intent.args.text);
        if (!current || !fold(message).includes(fold(value))) return failed('Thầy cô hãy ghi rõ nội dung cần đưa vào ô nhập.');
        store.setDraft(current.id, value);
        return succeeded('Đã đưa nội dung vào ô nhập.');
      }
      case 'CHAT_MESSAGE': {
        if (!current) return failed('Hãy mở cuộc trò chuyện trước.');
        const target = current.messages[Number(intent.args.number) - 1];
        if (!target || target.id === messageId) return failed('Không tìm thấy số tin nhắn này trong cuộc trò chuyện.');
        if (intent.args.operation === 'draft') {
          store.setDraft(current.id, target.content);
          return succeeded('Đã đưa tin nhắn vào ô nhập.');
        }
        if (intent.args.operation === 'copy') {
          if (!navigator.clipboard) return failed('Trình duyệt chưa cho phép sao chép. Thầy cô hãy dùng nút sao chép trên tin nhắn.');
          return navigator.clipboard.writeText(target.content).then(
            () => succeeded('Đã sao chép tin nhắn.'), () => failed('Trình duyệt chưa cho phép truy cập bảng tạm.'),
          );
        }
        if (intent.args.operation === 'branch') {
          const id = store.branchAtMessage(current.id, target.id);
          if (!id) return failed('Chưa tạo được nhánh hội thoại.');
          flushSync(() => { setEditor(null); openSession(id); });
          store.appendMessage(id, 'assistant', 'Đã mở nhánh hội thoại.');
          return succeeded('Đã tạo nhánh hội thoại.');
        }
        if (target.role !== 'user') return failed('Chỉ thu hồi được tin nhắn của thầy cô.');
        return prepare('Thu hồi tin nhắn đã chọn và các tin sau. Công việc đã gửi hoặc chỉnh sửa đã lưu vẫn giữ nguyên.', () => {
          store.retractMessage(current.id, target.id);
          return succeeded('Đã thu hồi đoạn hội thoại. Trạng thái công việc trên máy chủ vẫn giữ nguyên.');
        });
      }
      case 'DELETE_SESSION': {
        const name = typeof intent.args.title === 'string' ? fold(intent.args.title) : '';
        const matches = name ? store.getSnapshot().filter(item => fold(item.title) === name) : current ? [current] : [];
        if (matches.length !== 1) return failed('Thầy cô hãy ghi rõ tên của một cuộc trò chuyện trong tủ đề.');
        const target = matches[0];
        if (target.status === 'generating') return failed('Đề đang được tạo. Hiện chưa thể hủy công việc này.');
        return prepare(`Xóa “${target.title}” khỏi tủ đề trên trình duyệt này.`, () => {
          const latest = store.getSnapshot().find(item => item.id === target.id);
          if (!latest || latest.status === 'generating' || latest.title !== target.title) return failed('Đề đã thay đổi. Hãy kiểm tra lại tủ đề.');
          store.remove(target.id);
          if (current?.id === target.id) flushSync(() => { setEditor(null); setShowQuickModal(false); setConfigureId(null); setActiveId(null); setScreen('start'); });
          return succeeded(`Đã xóa “${target.title}” khỏi tủ đề.`);
        });
      }
      case 'SHOW_FORMATS':
      case 'SELECT_FORMAT':
      case 'FORMAT_DETAILS':
      case 'PREPARE_GENERATION': {
        if (intent.id !== 'SHOW_FORMATS' && (!current || !['draft', 'error'].includes(current.status) || editor)) {
          return failed('Đề phải ở trạng thái nháp hoặc lần tạo bị lỗi mới có thể thiết lập.');
        }
        return (async () => {
          try {
            const formats = await getExamFormats();
            if (runtimeRef.current?.binding() !== expected || turn.current?.signal.aborted || !turn.current) {
              return failed('Màn hình đã thay đổi trong lúc tải các mẫu đề.');
            }
            const available = formats.filter(format => format.available);
            const list = available.map(format => `${format.displayName}: ${format.totalQuestions} câu, ${format.durationMinutes} phút`).join('; ');
            if (intent.id === 'SHOW_FORMATS') return succeeded(list || 'Chưa có mẫu đề khả dụng.');
            const selected = intent.args.format ?? agentSelection?.id ?? current?.intake?.formatId;
            if (!selected) return failed(list
              ? `Thầy cô muốn dùng mẫu nào? ${list}. Với Toán THPT, thầy cô có thể nêu thêm chuyên đề.`
              : 'Chưa tải được mẫu đề khả dụng.');
            const format = available.find(item => item.id === selected);
            if (!format || !current) return failed('Mẫu yêu cầu hiện không khả dụng.');
            const intake = { sourceId: messageId, formatId: format.id, version: format.version };
            const expanded = intent.args.details === true || intent.id === 'FORMAT_DETAILS';
            if (intent.id !== 'PREPARE_GENERATION') {
              flushSync(() => {
                store.setIntake(current.id, { ...intake, phase: 'selected' });
                setAgentSelection({ formats, id: format.id, expanded });
                setConfigureId(current.id);
                setShowQuickModal(true);
              });
              return { ...succeeded(`Đã chọn ${format.displayName}: ${format.totalQuestions} câu, ${format.durationMinutes} phút.`), expectedAfter: runtimeRef.current?.binding() };
            }
            const proposal = prepareParams(format, intent.args, message);
            if (!proposal.params) return failed(proposal.error);
            const payload = proposal.params;
            if (current.errorCode === 'network_error' && current.requestSignature &&
                current.requestSignature !== JSON.stringify(payload)) {
              return failed('Lần gửi trước chưa rõ kết quả. Hãy thử lại với thông số cũ trước khi đổi yêu cầu.');
            }
            await evaluateExamFormat(payload);
            if (runtimeRef.current?.binding() !== expected || !turn.current || turn.current.signal.aborted) {
              return failed('Màn hình đã thay đổi trong lúc kiểm tra mẫu đề.');
            }
            const summary = `${format.displayName} · ${format.totalQuestions} câu · ${format.durationMinutes} phút.${proposal.topic ? ` Chuyên đề: ${proposal.topic}.` : ''} Bấm “Tạo đề thi” để xác nhận gửi yêu cầu.`;
            flushSync(() => {
              store.setIntake(current.id, { ...intake, topic: proposal.topic, phase: 'evaluated' });
              setAgentSelection({ formats, id: format.id, expanded: true, summary });
              setConfigureId(current.id);
              setShowQuickModal(true);
            });
            pending.current = {
              workspaceId: current.id,
              binding: runtimeRef.current!.binding(),
              expires: Date.now() + 5 * 60_000,
              run: async () => {
                flushSync(() => { setShowQuickModal(false); setAgentSelection(undefined); });
                store.setIntake(current.id, { ...intake, topic: proposal.topic, phase: 'confirmed' });
                const job = await store.generate(current.id, payload);
                if (job) return { status: 'accepted', text: 'Máy chủ đã nhận công việc tạo đề. Thầy cô có thể trao đổi tiếp trong khi đợi.' };
                const actual = store.getSnapshot().find(item => item.id === current.id);
                return actual?.errorCode === 'network_error'
                  ? { status: 'unknown', text: 'Chưa rõ máy chủ đã nhận yêu cầu hay chưa. Chỉ thử lại với cùng thông số.' }
                  : failed(actual?.error || 'Chưa nhận được mã công việc tạo đề.');
              },
            };
            return { status: 'pending', text: summary };
          } catch (error) {
            return failed(error instanceof Error ? error.message : 'Chưa kiểm tra được mẫu đề với máy chủ.');
          }
        })();
      }
      case 'STATUS': return succeeded(statusText(current));
      case 'WARNINGS': {
        if (!current?.package) return failed('Chưa có đề hoàn chỉnh để đọc cảnh báo.');
        const pkg = current.package;
        const flagged = current.questions.filter(q => q.answerCheck === 'mismatched')
          .slice(0, 8).map(q => `${q.part || ''} Câu ${displayNumber(q)}`.trim());
        return succeeded(`Cảnh báo nguồn: ${pkg.warnings?.length || 0}. Cảnh báo hình: ${pkg.visualWarnings?.length || 0}. ${flagged.length ? `Câu có đáp án lệch: ${flagged.join(', ')}.` : 'Chưa có cảnh báo lệch đáp án trong dữ liệu hiện tại.'}`);
      }
      case 'SET_VIEW': {
        if (!current?.package || editor || showQuickModal) return failed('Cần đề đã tạo xong và đóng hộp thoại trước khi đổi chế độ xem.');
        const view = intent.args.view as ExamCanvasViewMode;
        flushSync(() => { setAgentOpenedPdf(view === 'pdf'); setViewMode(view); });
        return succeeded(view === 'pdf' ? previewText(current) : view === 'review' ? 'Đã mở chế độ xem đáp án.' : 'Đã mở đề thi.');
      }
      case 'FOCUS_SECTION': {
        if (viewMode === 'pdf' || !current?.package || !canvas.current) return failed('Hãy mở đề thi hoặc chế độ đáp án trước.');
        return canvas.current.section(sectionId(String(intent.args.part))) ? succeeded('Đã cuộn đến phần thi yêu cầu.') : failed('Chưa tìm thấy phần thi trong đề hiện tại.');
      }
      case 'SCROLL_TOP':
        return viewMode !== 'pdf' && canvas.current?.top() ? succeeded('Đã cuộn lên đầu đề.') : failed('Hãy mở trang đề thi trước.');
      case 'FOCUS_QUESTION':
      case 'OPEN_EDITOR':
      case 'VERIFY_QUESTION':
      case 'REGENERATE_QUESTION': {
        if (!current?.jobId || current.status !== 'complete' || !current.package || showQuickModal) return failed('Chỉ có thể thao tác với câu hỏi trong đề đã tạo xong.');
        const question = resolveQuestion(current, intent.args, editor?.question.stableId);
        if (!question || !question.stableId) return failed('Chưa xác định được câu hỏi. Thầy cô hãy ghi số câu và phần thi hoặc mở câu trong trình chỉnh sửa.');
        const label = `câu ${displayNumber(question)}${question.part ? ` (${question.part})` : ''}`;
        const target = { sessionId: current.id, jobId: current.jobId, question };
        if (intent.id === 'FOCUS_QUESTION') {
          if (editor) return failed('Hãy đóng trình chỉnh sửa trước khi chuyển tới câu hỏi.');
          const view = intent.args.view as ExamCanvasViewMode | undefined;
          if (view || viewMode === 'pdf') flushSync(() => setViewMode(view ?? 'paper'));
          return canvas.current?.question(question.stableId) ? succeeded(`Đã chuyển đến ${label}.`) : failed('Câu hỏi chưa hiển thị trong chế độ hiện tại.');
        }
        if (intent.id === 'OPEN_EDITOR') {
          if (editor && editor.question.stableId !== question.stableId) return failed('Hãy hoàn tất hoặc đóng trình chỉnh sửa đang mở.');
          flushSync(() => setEditor(target));
          return succeeded(`Đã mở chỉnh sửa ${label}.`);
        }
        if (intent.id === 'VERIFY_QUESTION' && !examService.verifyQuestion) return failed('Kiểm tra lại đáp án chưa khả dụng trong chế độ hiện tại.');
        const verify = intent.id === 'VERIFY_QUESTION';
        if (!verify && current.package.blueprint.examType === 'DGNL_DHQG') return failed('V-ACT hỗ trợ sửa trực tiếp và kiểm tra đáp án. Tạo lại từng câu hiện chỉ có cho Toán THPT.');
        return prepare(verify
          ? `Kiểm tra lại đáp án ${label} bằng bộ giải. Thao tác dùng lượt gọi AI.`
          : `Sinh lại ${label} bằng AI theo yêu cầu “${intent.args.instruction}”.`, async () => {
          try {
            const latest = await editQuestion(target, verify ? 'verify' : 'regen', String(intent.args.instruction ?? ''));
            const result = latest?.questions.find(item => item.stableId === question.stableId);
            if (verify && result?.answerCheck) {
              const verdict = { matched: 'hai đáp án khớp nhau', mismatched: 'hai đáp án khác nhau', needs_recheck: 'vẫn cần kiểm tra' }[result.answerCheck];
              return succeeded(`Kết quả kiểm tra ${label}: ${verdict}.`);
            }
            if (!verify && result && latest?.package?.revision !== current.package?.revision) return succeeded(`Đã cập nhật ${label}. Hãy xem lại phiên bản mới.`);
          } catch {
            return { status: 'unknown', text: 'Chưa xác nhận được kết quả. Hãy kiểm tra phiên bản hiện tại trước khi thử lại.' };
          }
          return { status: 'unknown', text: 'Chưa quan sát được thay đổi trong đề.' };
        });
      }
      case 'CLOSE_EDITOR':
        if (!editor || editorBusy.current.has(editor.sessionId)) return failed('Trình chỉnh sửa chưa mở hoặc đang xử lý.');
        flushSync(() => setEditor(null));
        return succeeded('Đã đóng trình chỉnh sửa.');
      case 'RETRY_PREVIEW':
        if (!current || !['failed', 'unavailable'].includes(current.preview?.status ?? '') || current.artifactChanged) return failed('Chỉ thử lại được khi bản xem trước hiện tại gặp lỗi.');
        return store.requestPreview(current.id, true).then(() => {
          const latest = store.getSnapshot().find(item => item.id === current.id);
          return latest?.preview?.status === 'ready' ? succeeded('Bản xem trước đã sẵn sàng.')
            : ['queued', 'compiling'].includes(latest?.preview?.status ?? '')
              ? { status: 'accepted', text: 'Máy chủ đã nhận yêu cầu dựng lại PDF.' }
              : failed(latest?.previewError || 'Chưa dựng lại được bản xem trước.');
        });
      case 'ADD_NOTE':
      case 'CANCEL_NOTE': {
        if (intent.id === 'ADD_NOTE' && current?.status === 'complete') {
          return dispatch({ id: 'REGENERATE_QUESTION', args: intent.args }, expected, message, messageId);
        }
        if (!current?.jobId) return failed('Chưa có công việc tạo đề để gắn ghi chú.');
        const notes = current.notes ?? [];
        const number = Number(intent.args.number);
        const part = typeof intent.args.part === 'string' ? sectionId(intent.args.part) : undefined;
        const matches = notes.filter(note => note.jobId === current.jobId && note.number === number &&
          (!part || note.part === part) && ['recorded', 'awaiting_review', 'unresolved', 'failed'].includes(note.status));
        if (matches.length > 1) return failed('Có nhiều ghi chú cùng số câu. Thầy cô hãy nêu rõ phần thi.');
        if (intent.id === 'CANCEL_NOTE') {
          if (!matches.length) return failed('Chưa tìm thấy ghi chú của câu này.');
          store.setNotes(current.id, notes.map(note => note.id === matches[0].id ? { ...note, status: 'cancelled' } : note));
          return succeeded(`Đã bỏ ghi chú cho ${noteLabel(matches[0])}.`);
        }
        if (current.status !== 'generating') return failed('Chưa thể ghi chú chỉnh sửa cho công việc hiện tại.');
        const instruction = String(intent.args.instruction);
        if (!fold(message).includes(fold(instruction))) return failed('Thầy cô hãy nêu rõ nội dung muốn chỉnh.');
        if (!matches.length && notes.length >= 32) return failed('Phiên này đã có 32 ghi chú. Thầy cô hãy xử lý các ghi chú trước khi thêm.');
        const note: Note = { id: matches[0]?.id ?? crypto.randomUUID(), sourceId: messageId, jobId: current.jobId,
          number, part: part ?? matches[0]?.part, instruction, status: 'recorded' };
        store.setNotes(current.id, [...notes.filter(item => item.id !== note.id), note]);
        return succeeded(`Đã lưu ghi chú cho ${noteLabel(note)}. Đề đang chạy theo yêu cầu đã gửi.`);
      }
      case 'REVIEW_NOTES':
      case 'APPLY_NOTES': {
        const notes = current?.notes?.filter(note => note.jobId === current.jobId && note.status !== 'cancelled') ?? [];
        if (!notes.length) return failed('Chưa có ghi chú cho công việc hiện tại.');
        const summary = notes.slice(0, 12).map(note => `${noteLabel(note)}: ${note.instruction} (${{
          recorded: 'đã lưu', awaiting_review: 'chờ duyệt', unresolved: 'chưa xác định được câu', applied: 'đã áp dụng',
          failed: 'chưa xác nhận kết quả', cancelled: 'đã hủy',
        }[note.status]})`).join('\n');
        if (intent.id === 'REVIEW_NOTES') return succeeded(summary);
        if (!current?.package || current.status !== 'complete') return failed('Hãy đợi máy chủ tạo xong đề trước khi áp dụng ghi chú.');
        if (current.package.blueprint.examType === 'DGNL_DHQG') return failed('Thầy cô hãy mở từng câu V-ACT để sửa trực tiếp. Mẫu này chưa hỗ trợ sinh lại từng câu.');
        const ready = notes.filter(note => note.status === 'awaiting_review' && note.stableId).slice(0, 4);
        if (!ready.length) return failed('Chưa có ghi chú đã xác định đúng câu và đang chờ duyệt.');
        return prepare(`Áp dụng ${ready.length} ghi chú dưới đây với AI:\n${ready.map(note => `${noteLabel(note)}: ${note.instruction}`).join('\n')}`, async () => {
          const controller = turn.current;
          let revision = current.package?.revision;
          let applied = 0;
          for (const note of ready) {
            const latest = store.getSnapshot().find(session => session.id === current.id);
            const question = latest?.questions.find(item => item.stableId === note.stableId && item.examRevision === revision);
            if (!latest?.jobId || latest.jobId !== current.jobId || latest.package?.revision !== revision ||
                !question || controller?.signal.aborted || activeRef.current !== current.id) break;
            try {
              const after = await editQuestion({ sessionId: latest.id, jobId: latest.jobId, question }, 'regen', note.instruction);
              if (!after?.package || after.package.revision === revision) throw new Error('Chưa nhận được phiên bản mới.');
              revision = after.package.revision;
              store.setNotes(latest.id, (after.notes ?? []).map(item => item.id === note.id
                ? { ...item, status: 'applied', appliedRevision: revision } : item));
              applied++;
            } catch {
              const actual = store.getSnapshot().find(session => session.id === current.id);
              store.setNotes(latest.id, (actual?.notes ?? []).map(item => item.id === note.id ? { ...item, status: 'failed' } : item));
              return { status: 'unknown', text: `Đã áp dụng ${applied} ghi chú. Kết quả cho ${noteLabel(note)} chưa được xác nhận. Các bước sau vẫn chờ.` };
            }
          }
          return applied === ready.length ? succeeded(`Đã áp dụng ${applied} ghi chú. Hãy xem lại phiên bản mới.`)
            : failed(`Đã áp dụng ${applied} ghi chú. Các bước còn lại đang chờ kiểm tra.`);
        });
      }
      case 'APPROVE':
        if (!current || editor || !store.canApprove(current.id)) return failed('Thầy cô hãy tự mở và kiểm tra PDF của phiên bản hiện tại trước khi phê duyệt.');
        return prepare(`Phê duyệt phiên bản ${current.package?.revision}. Hãy xác nhận sau khi đã xem kỹ PDF và các cảnh báo.`, async () =>
          await approve() ? succeeded('Đã phê duyệt phiên bản hiện tại.') : failed('Chưa xác nhận được phê duyệt. Hãy kiểm tra trạng thái của đề.'));
      case 'EXPORT': {
        const format = intent.args.format as 'pdf' | 'tex' | 'json';
        if (!current?.package?.approved || current.artifactChanged || editor) return failed('Phiên bản hiện tại cần được phê duyệt trước khi tải tệp.');
        if (format === 'pdf' && (current.preview?.status !== 'ready' || current.preview.revision !== current.package.revision ||
            current.preview.contentHash !== current.package.contentHash)) return failed('Bản PDF của phiên bản hiện tại chưa sẵn sàng.');
        return prepare(`Tải tệp ${format.toUpperCase()} của phiên bản ${current.package.revision}.`, async () =>
          await exportFile(format === 'json' ? 'TEACHER_KEY' : 'STUDENT_EXAM', format)
            ? succeeded('Đã yêu cầu trình duyệt tải tệp.') : failed('Chưa tải được tệp.'));
      }
      default: return failed('Thao tác này chưa có liên kết với màn hình hiện tại.');
    }
  };
  useLayoutEffect(() => {
    const state = binding(false);
    if (state !== renderEpoch.current.state) renderEpoch.current = { version: renderEpoch.current.version + 1, state };
    activeRef.current = activeId;
    runtimeRef.current = {
      binding,
      dispatch: (intent, expected, message, source) => binding() === expected ? dispatch(intent, expected, message, source)
        : { status: 'failed', text: 'Trạng thái đã thay đổi. Thầy cô hãy gửi lại yêu cầu.' },
    };
  });

  const sidebarLabel = controlsCollapsed ? 'Mở rộng thanh điều hướng' : 'Thu gọn thanh điều hướng';

  if (showWelcome) return <AstraWelcome onComplete={finishWelcome} />;

  return (
    <div className={`app-shell create-mode workspace-active integrated-shell ${revealingWorkspace ? 'workspace-revealing' : ''} ${controlsCollapsed ? 'controls-collapsed' : ''}`}>
      <header className="app-header">
        <div className="sidebar-brand-row">
          <button type="button" className="app-brand" aria-label="ASTRA — Về màn hình bắt đầu" title="Về màn hình bắt đầu" onClick={newExam}>
            <span className="brand-emblem"><AstraLogo className="app-brand-logo" /></span>
            <span className="brand-wordmark">ASTRA</span>
          </button>
          <button type="button" className="sidebar-collapse-btn" onClick={() => setControlsCollapsed(value => !value)} aria-label={sidebarLabel} aria-expanded={!controlsCollapsed} title={sidebarLabel}>
            {controlsCollapsed ? <PanelLeftOpen size={16} aria-hidden="true" /> : <PanelLeftClose size={16} aria-hidden="true" />}
          </button>
        </div>
        <SidebarExamLibrary sessions={sessions} activeId={screen === 'workspace' ? activeId : null} onNew={newExam} onOpen={openManually} onDelete={id => { store.remove(id); if (activeId === id) newExam(); if (configureId === id) { setConfigureId(null); setShowQuickModal(false); } }} />
        <button className="side-rail-edge" type="button" onClick={() => setControlsCollapsed(value => !value)} aria-label={sidebarLabel} aria-expanded={!controlsCollapsed} title={sidebarLabel} />
        <div className="header-right"><span className="header-avatar" aria-label="Người dùng: Cùng thầy cô" title="Cùng thầy cô">GV</span><span className="header-session">Cùng thầy cô</span></div>
      </header>

      {store.storageWarning && <div className="canvas-alert-banner is-error" role="alert">{store.storageWarning}</div>}
      {admissionError && <div className="canvas-alert-banner is-error" role="alert">{admissionError}</div>}
      {/* Main content */}
      {screen === 'start' && <WorkspaceStart exiting={leavingStart} draft={landingDraft} onDraftChange={setLandingDraft} onTemplate={() => { setConfigureId(null); setAgentSelection(undefined); setShowQuickModal(true); }} onDetailed={handleDetailedStart} onSend={handleLandingSend} />}

      {screen === 'workspace' && active && (
        <WorkspaceLayout key={active.id}>
          {{
            left: (
              <>
                <div className="studio-chat-heading"><div><span className="studio-kicker">KHÔNG GIAN SOẠN ĐỀ</span><h2>Cùng soạn đề</h2></div></div>
                <div className="session-context"><strong>{active.title}</strong></div>
                {(active.status === 'draft' || active.status === 'error') && <div className="session-create-action">
                  {active.error && <p className="session-error-note">{active.error}</p>}
                  <button type="button" className="button-primary" onClick={() => { cancelTurn(); setAgentSelection(undefined); setConfigureId(active.id); setShowQuickModal(true); }}>{active.status === 'error' ? 'Thử tạo lại' : 'Tạo đề từ yêu cầu'}</button>
                </div>}
                <ChatHistory messages={messages} onSuggestion={value => store.setDraft(active.id, value)} onEditMessage={message => store.setDraft(active.id, message.content)} onRetractMessage={message => {
                  cancelTurn(); store.retractMessage(active.id, message.id);
                  if (active.jobId) store.appendMessage(active.id, 'system', 'Đã thu hồi đoạn hội thoại. Trạng thái công việc trên máy chủ vẫn giữ nguyên.');
                }} onBranchMessage={message => { const branchId = store.branchAtMessage(active.id, message.id); if (branchId) openManually(branchId); }} />
              </>
            ),
            right: (
              <>
                {active.error && (
                  <div className="canvas-alert-banner is-error" role="alert">
                    <AlertCircle size={17} aria-hidden="true" />
                    <span>{active.error}</span>
                  </div>
                )}
                {isGenerating && active.progress && (
                  <div className="canvas-progress-banner" role="status" aria-live="polite">
                    <div className="canvas-progress-top">
                      <span className="canvas-progress-label">
                        <LoaderCircle className="exam-status-spinner" size={15} aria-hidden="true" />
                        <span>{formatProgressStatus(active.progress.statusMessage)}</span>
                      </span>
                      <strong className="canvas-progress-pct">{active.progress.percent}%</strong>
                    </div>
                    <div className="canvas-progress-track" aria-hidden="true">
                      <div className="canvas-progress-fill" style={{ width: `${Math.max(4, Math.min(100, active.progress.percent))}%` }} />
                    </div>
                  </div>
                )}
                {!!active.package?.warnings?.length && (
                  <details className="canvas-source-warnings">
                    <summary>
                      <AlertTriangle size={14} aria-hidden="true" />
                      <span>Cảnh báo nguồn ({active.package.warnings.length})</span>
                    </summary>
                    <div className="canvas-source-warnings-body">
                      {active.package.warnings.map((warning, i) => <p key={i}><strong>{warning.questionId}:</strong> {warning.message}</p>)}
                    </div>
                  </details>
                )}
                {!!active.package?.visualWarnings?.length && (
                  <div className="pdf-preview-warning" role="alert">
                    <strong>Cảnh báo hình vẽ / bảng biểu ({active.package.visualWarnings.length})</strong>
                    <p>Đề thi chưa tự sinh hình vẽ còn thiếu. Thầy cô hãy sửa câu hỏi bị ảnh hưởng.</p>
                    {active.package.visualWarnings.map((warning, i) => {
                      const target = active.questions.find(q => q.stableId === warning.questionId);
                      const label = target ? `Câu ${target.id}` : warning.questionId;
                      return (
                        <p key={`${warning.questionId}-${i}`}>
                          <strong>{label}:</strong> {formatVisualWarning(warning.code)}
                        </p>
                      );
                    })}
                  </div>
                )}
                <ExamPaperView
                  header={<CanvasHeader
                    examMeta={examMeta}
                    isGenerating={isGenerating}
                    canExport={active.package?.approved === true && !active.artifactChanged}
                    canExportPdf={Boolean(
                      active.package?.approved &&
                      !active.artifactChanged &&
                      active.preview?.status === 'ready' &&
                      active.preview.revision === active.package.revision &&
                      active.preview.contentHash === active.package.contentHash
                    )}
                    showApprove={active.status === 'complete' && !active.package?.approved && !active.artifactChanged}
                    canApprove={store.canApprove(active.id)}
                    approving={approving}
                    onOpenPdfPreview={openPdfManually}
                    onApprove={() => { void approve(); }}
                    onExportPdf={handleExportPdf}
                    onExportWord={handleExportWord}
                    onExportAnswer={handleExportAnswer}
                  />}
                  controlsRef={canvas}
                  onManualPdfOpen={() => store.markPreviewOpened(active.id)}
                  questions={liveQuestions}
                  passages={active.package?.passages}
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  latestQuestionCount={prevQuestionCount}
                  viewMode={viewMode}
                  onViewModeChange={mode => { setAgentOpenedPdf(false); setViewMode(mode); }}
                  examId={active.jobId || active.package?.examId}
                  revision={active.package?.revision}
                  contentHash={active.package?.contentHash}
                  approved={active.package?.approved}
                  preview={active.preview}
                  visualWarnings={active.package?.visualWarnings}
                  previewLog={active.previewLog}
                  previewError={active.previewError}
                  previewErrorCode={active.previewErrorCode}
                  artifactChanged={active.artifactChanged}
                  onRetryPreview={handleRetryPreview}
                  onPreviewOpened={handlePreviewOpened}
                  onEditQuestion={id => {
                    const question = active.questions.find(item => item.id === id);
                    if (active.jobId && question) setEditor({ sessionId: active.id, jobId: active.jobId, question });
                  }}
                />
              </>
            ),
            composer: <ModernChatBar onSend={handleSendMessage} disabled={chatPending} draft={active.draft} onDraftChange={value => store.setDraft(active.id, value)} />,
          }}
        </WorkspaceLayout>
      )}

      {/* Quick preset modal */}
      {showQuickModal && (
        <QuickPresetModal
          title={configureId ? 'Thiết lập đề theo yêu cầu' : 'Tạo đề từ mẫu'}
          dialogRef={presetDialog}
          agentSelection={agentSelection}
          onManualSelect={() => { pending.current = null; setAgentSelection(undefined); }}
          onStart={handleQuickStart}
          onClose={closeQuickModal}
        />
      )}
      {editor && <QuestionEditor question={editor.question} onClose={() => setEditor(null)}
        onVerify={examService.verifyQuestion && editor.question.examRevision !== undefined ? async () => {
          await editQuestion(editor, 'verify');
          if (activeRef.current === editor.sessionId) setViewMode('review');
        } : undefined}
        onSave={async question => { await editQuestion(editor, 'save', question); }}
        onRegenerate={async instruction => { await editQuestion(editor, 'regen', instruction); }}
      />}
    </div>
  );
};

export default App;
