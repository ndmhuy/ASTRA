import React, { useState, useEffect, useSyncExternalStore, useCallback, useLayoutEffect, useMemo, useRef } from 'react';
import { flushSync } from 'react-dom';
import { meaningful, recentQuestion, redact, retrievedContext, searchSessions } from './agent/memory';
import { interpretationUnavailable, interpret } from './agent/client';
import { admit, execute, fastRoute, fold, mayDispatch, type Effect, type Runtime } from './agent/recipes';
import { displayNumber, failure, inspectQuestion, previewText, resolveQuestion, sectionId, statusText, success } from './agent/examActions';
import type { Decision, Intent } from './agent/contracts';
import { contextualSubject, resolveSemantic } from './agent/semantics';
import { familyFor, formatOverview, guidanceFor, mentionedFamilies, resolveIntake, shortSubjectIntake } from './agent/knowledge';
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
import type { ChatMessage, ExamFormat, ExamRequestParams, QuestionItem } from './types/exam';
import { QuestionEditor, type QuestionEditorControls } from './components/QuestionEditor';
import { ApiError, evaluateExamFormat, examService, getExamFormats } from './services/examService';
import { prepareParams, type Intake } from './agent/intake';
import { noteLabel, type Note } from './agent/notes';
import { ExamVersionHistory } from './components/ExamVersionHistory';
import { MathRenderer } from './components/MathRenderer';
import { ExamSessions } from './state/examSessions';
import { formatProgressStatus, formatVisualWarning } from './utils/userMessages.ts';
import './styles/workspace.css';
import './styles/classroom.css';
import './styles/studio.css';
import './styles/createVision.css';
import './styles/integratedWorkspace.css';
import './styles/integration.css';
import './styles/atelier.css';

interface RegenerationUndo {
  sessionId: string;
  jobId: string;
  previousRevision: number;
  revision: number;
}
type EditorTarget = { sessionId: string; jobId: string; question: QuestionItem; workspaceId?: string };
const CONFIRMATION_TTL_MS = 5 * 60_000;

type Confirmation = {
  workspaceId: string;
  binding: string;
  expires: number;
  run: (sourceId?: string) => Promise<Effect> | Effect;
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
  const libraryError = useSyncExternalStore(store.subscribe, store.getLibraryError);
  const browserImport = useSyncExternalStore(store.subscribe, store.getBrowserImport);
  const turn = useRef<AbortController | null>(null);
  const [admissionError, setAdmissionError] = useState('');
  const pending = useRef<Confirmation | null>(null);
  const canvas = useRef<ExamPaperControls>(null);
  const editorControls = useRef<QuestionEditorControls>(null);
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
  const [verifyingQuestionId, setVerifyingQuestionId] = useState<number | null>(null);
  const [approvingQuestionId, setApprovingQuestionId] = useState<number | null>(null);
  const [historySession, setHistorySession] = useState<string | null>(null);
  const [undo, setUndo] = useState<RegenerationUndo>();
  const [undoing, setUndoing] = useState(false);
  const [undoConflict, setUndoConflict] = useState<{ id: string; current: string; afterChange: string; beforeChange: string }>();
  const closeQuickModal = useCallback(() => {
    turn.current?.abort();
    turn.current = null;
    pending.current = null;
    setChatPending(false);
    setShowQuickModal(false);
    setAgentSelection(undefined);
  }, []);
  const active = sessions.find(session => session.id === activeId);
  const sharedId = active && !active.browserOnly && examService.workspaceLibrary ? active.id : null;
  const [recordedChat, setRecordedChat] = useState<{ id: string; messages: ChatMessage[]; signature: string }>();
  const history = examService.history;
  const canOpenHistory = Boolean(history && active?.jobId && active.package?.revision && active.status === 'complete');
  const canUndo = !sharedId && history && undo && active?.id === undo.sessionId && active.jobId === undo.jobId &&
    active.package?.revision === undo.revision;
  const messages = useMemo(() => {
    const recorded = recordedChat?.id === sharedId ? recordedChat.messages : [];
    const byId = new Map([...(active?.messages ?? []), ...recorded].map(message => [message.id, message]));
    return [...byId.values()].sort(
      (first, second) => Date.parse(first.timestamp) - Date.parse(second.timestamp)
    );
  }, [active?.messages, recordedChat, sharedId]);
  const latestUndo = sharedId && active?.package?.revision
    ? [...messages].reverse().find(message => message.changeId && message.examVersion?.jobId === active.jobId &&
        message.examVersion?.revision === active.package?.revision)
    : undefined;
  const liveQuestions = active?.questions || [];
  const examMeta = active?.meta || null;
  const isGenerating = active?.status === 'generating';
  const prevQuestionCount = active?.previousCount || 0;
  useEffect(() => {
    store.resume();
    window.addEventListener('focus', store.loadLibrary);
    return () => {
      window.removeEventListener('focus', store.loadLibrary);
      store.dispose();
    };
  }, [store]);
  useEffect(() => {
    const library = examService.workspaceLibrary;
    if (!library || !sharedId || screen !== 'workspace') return;
    let current = true;
    let pending = false;
    const refresh = async () => {
      if (pending) return;
      pending = true;
      try {
        const { messages, milestones } = await library.changes(sharedId);
        if (current) {
          const timeline = [...messages, ...milestones];
          const signature = JSON.stringify(timeline);
          setRecordedChat(previous => previous?.id === sharedId && previous.signature === signature
            ? previous : { id: sharedId, messages: timeline, signature });
        }
      } catch {
        // Leave the last server-confirmed messages visible during a disconnect.
      } finally { pending = false; }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 1500);
    return () => { current = false; window.clearInterval(timer); };
  }, [screen, sharedId]);
  useEffect(() => {
    if (activeId && !active) {
      const importedId = store.importedWorkspaceId(activeId);
      setActiveId(importedId);
      if (!importedId) setScreen('start');
    }
  }, [activeId, active, store]);
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
    let resolvedIntake: Intake | undefined;
    const runtime: Runtime = {
      binding: () => runtimeRef.current!.binding(),
      dispatch: (intent, expected, message, source) => runtimeRef.current!.dispatch(intent, expected, message, source, resolvedIntake),
    };
    const binding = runtime.binding();
    const origin = store.getSnapshot().find(s => s.id === id);
    const alive = () => !controller.signal.aborted && !!store.getSnapshot().find(s => s.id === id)?.messages.some(m => m.id === messageId);
    try {
      if (options.searchWeb || options.attachedFiles.length) {
        pending.current = null;
        answer(options.attachedFiles.length
          ? 'ASTRA chưa thể đọc tệp đính kèm. Thầy cô có thể dán phần nội dung cần dùng vào tin nhắn.'
          : 'ASTRA chưa hỗ trợ tìm trên mạng. Thầy cô có thể gửi nội dung dạng văn bản.');
        return;
      }
      await Promise.resolve();
      if (!alive()) return;
      let local = fastRoute(content);
      let intakeFormats: ExamFormat[] | undefined;
      if (!local && origin && ['draft', 'error'].includes(origin.status) && !editor && content.length <= 80) {
        const subject = shortSubjectIntake(content);
        if (subject) local = { intake: subject };
        else if (origin.intake?.missing === 'subject') {
          intakeFormats = await getExamFormats();
          const contextual = contextualSubject(content, origin.intake, intakeFormats);
          if (contextual?.intake) local = { intake: contextual.intake };
          if (!alive() || runtime.binding() !== binding) return;
        }
      }
      if (local && 'text' in local) { answer(local.text); return; }
      if (local && 'confirm' in local) {
        const prepared = pending.current;
        pending.current = null;
        if (!local.confirm) {
          const intakePending = origin?.intake?.phase === 'collecting';
          if (intakePending) store.setIntake(id, undefined);
          answer(prepared || intakePending ? 'Đã hủy yêu cầu trò chuyện đang chờ.' : 'Hiện chưa có tác vụ trò chuyện đang chờ.');
        } else if (!prepared || prepared.workspaceId !== id) {
          answer('Hiện chưa có thao tác nào đang chờ xác nhận.');
        } else if (prepared.expires < Date.now() || prepared.binding !== runtime.binding()) {
          answer('Xác nhận đã hết hiệu lực hoặc trạng thái đã thay đổi. Thầy cô hãy gửi lại yêu cầu.');
        } else {
          const effect = await prepared.run(messageId);
          if (alive() || !store.getSnapshot().some(session => session.id === id)) answer(effect.text);
        }
        return;
      }
      // An unresolved new turn may be a correction. Do not leave an older write runnable.
      if (!local || 'intake' in local || ('intents' in local && local.intents.some(intent => !['STATUS', 'WARNINGS', 'LIST_SESSIONS', 'SHOW_FORMATS', 'RECALL'].includes(intent.id)))) {
        pending.current = null;
      }
      let canAct = !!local || mayDispatch(content);
      const started = performance.now();
      const interpreted = local && 'intents' in local ? { kind: 'task', intents: local.intents } as Decision
        : local && 'intake' in local ? { kind: 'clarify', intents: [], intake: local.intake }
        : await interpret(id, messageId, redact(content), {
          screen, setup: showQuickModal, status: origin?.status ?? 'draft', view: viewMode,
          ...(origin ? retrievedContext(origin, messageId, content) : {}),
          questionRefs: origin ? [...new Set(origin.questions.map(q => q.part ?? '').filter(Boolean))].slice(0, 8) : [],
          editor: Boolean(editor),
          approved: Boolean(origin?.package?.approved),
          confirmationPending: pending.current?.workspaceId === id && pending.current.binding === binding,
          preview: origin?.preview?.status ?? null,
        }, controller.signal);
      if (!alive() || runtime.binding() !== binding) return;
      const workflow = 'dialogueAct' in interpreted ? resolveSemantic(interpreted, recentQuestion(origin)) : undefined;
      if (workflow?.invalidateConfirmation) pending.current = null;
      if (workflow?.cancel) {
        store.setIntake(id, undefined);
        answer('Đã hủy yêu cầu trò chuyện đang chờ. Công việc tạo đề đã gửi vẫn giữ trạng thái hiện tại.');
        return;
      }
      if (workflow?.text) { answer(workflow.text); return; }
      if (workflow?.inspections) {
        const stated = [...fold(content).matchAll(/\bcau\s+(\d+)\b/g)].map(match => Number(match[1]));
        const parts = [...fold(content).matchAll(/\bcau\s+(\d+)\s+(?:o\s+)?phan\s+(i{1,3}|[123]|p[123]|tv|ta|to|logic|science)\b/g)];
        const inspections = workflow.inspections.map(args => {
          const named = parts.filter(match => Number(match[1]) === args.number);
          return args.part === undefined && named.length === 1 ? { ...args, part: sectionId(named[0][2]) } : args;
        });
        if (inspections.some(args => typeof args.number !== 'number' ||
            (!stated.includes(args.number) && workflow.referenceTarget?.number !== args.number) ||
            (parts.some(match => Number(match[1]) === args.number) && !parts.some(match => Number(match[1]) === args.number && sectionId(match[2]) === sectionId(String(args.part ?? '')))))) {
          answer('Thầy cô hãy ghi rõ số câu và phần thi cần xem.'); return;
        }
        answer(inspections.map(args => redact(inspectQuestion(origin, args).text)).join('\n'));
        return;
      }
      if (workflow?.setupOnly && 'constraints' in interpreted && interpreted.constraints.includes('NO_GENERATION')) canAct = true;
      const decision = workflow?.decision ?? interpreted as Decision;
      if (import.meta.env.VITE_AGENT_TRACE === '1') {
        console.info('[ASTRA Agent]', { route: local ? 'local' : 'model', kind: decision.kind,
          intents: decision.intents.map(intent => intent.id), latencyMs: Math.round(performance.now() - started) });
      }
      if (!alive() || runtime.binding() !== binding) return;
      let intents = decision.intents;
      let suggestedTitle = decision.title;
      let titleQuality = 1;
      if (decision.intake || decision.guidance || decision.kind === 'answer') {
        if (!canAct && decision.intake?.mode === 'request') {
          answer('Thầy cô muốn xem thông tin hay chuẩn bị đề? Em chưa thực hiện thao tác.');
          return;
        }
        if (decision.intake?.mode === 'request') pending.current = null;
        const formats = decision.guidance === 'remark' ? [] : intakeFormats ?? await getExamFormats();
        if (!alive() || runtime.binding() !== binding) return;
        if (decision.intake) {
          const resolution = resolveIntake(decision.intake, content, origin?.intake, formats, messageId, !!workflow);
          suggestedTitle = resolution.title && resolution.title !== 'Chọn mẫu đề thi'
            ? resolution.title : decision.title ?? resolution.title;
          titleQuality = resolution.draft?.formatId ? 3 : resolution.draft?.family ? 2 : 1;
          if ('text' in resolution) {
            const { draft, preset } = resolution;
            flushSync(() => {
              if (draft) store.setIntake(id, draft);
              if (suggestedTitle) store.suggestTitle(id, suggestedTitle, messageId, titleQuality);
            });
            if (draft && preset) {
              const accepted: Intake = {
                ...draft, formatId: preset.id, version: preset.version, subject: preset.subjects[0],
                count: preset.totalQuestions, minutes: preset.durationMinutes, grade: preset.grades[0],
              };
              const action: Intent = !workflow?.setupOnly && (workflow?.requestGeneration || draft.topic)
                ? { id: 'PREPARE_GENERATION', args: { format: preset.id, ...(draft.topic ? { topic: draft.topic } : {}) } }
                : { id: 'SELECT_FORMAT', args: { format: preset.id, details: true } };
              const expected = runtime.binding();
              pending.current = {
                workspaceId: id,
                binding: expected,
                expires: Date.now() + CONFIRMATION_TTL_MS,
                run: (sourceId = messageId) => runtimeRef.current!.dispatch(action, expected, '', sourceId, {
                  ...accepted, sourceIds: [...new Set([...(accepted.sourceIds ?? [messageId]), sourceId])],
                }),
              };
            }
            answer(resolution.text);
            return;
          }
          resolvedIntake = resolution.draft;
          if (resolvedIntake.topic) suggestedTitle = decision.title ?? suggestedTitle;
          intents = [workflow?.requestGeneration
            ? { id: 'PREPARE_GENERATION', args: { format: resolution.draft.formatId!, ...(resolution.draft.topic ? { topic: resolution.draft.topic } : {}) } }
            : workflow?.setupOnly ? { id: 'SELECT_FORMAT', args: { format: resolution.draft.formatId!, details: true } }
              : resolution.intent];
        } else {
          if (decision.guidance !== 'remark') store.suggestTitle(
            id, decision.guidance === 'capabilities' ? 'Tìm hiểu khả năng ASTRA' : 'Hướng dẫn soạn đề', messageId,
          );
          answer(guidanceFor(decision.guidance, formats));
          return;
        }
      } else if (decision.kind !== 'task') {
        answer(decision.kind === 'temporarily_unavailable' ? interpretationUnavailable(decision.reasonCode)
          : decision.kind === 'unsupported' ? 'Tính năng này chưa có trong ASTRA.'
            : 'Thầy cô muốn thao tác nào trong ASTRA? Em cần thêm thông tin để thực hiện.');
        return;
      }
      if (!canAct) {
        answer('Em chưa thực hiện thao tác. Thầy cô hãy cho biết phần muốn xem hoặc thao tác cần thực hiện.');
        return;
      }
      if (intents.some(intent => !['STATUS', 'WARNINGS', 'LIST_SESSIONS'].includes(intent.id))) {
        pending.current = null;
      }
      const literalNumbers = [...fold(content).matchAll(/\b(?:cau|question|tin nhan|message)\s+(\d+)\b/g)].map(match => Number(match[1]));
      if (intents.some(intent => typeof intent.args.number === 'number' && !literalNumbers.includes(intent.args.number) &&
          !(workflow?.referenceTarget?.number === intent.args.number && intent.args.part === workflow.referenceTarget.part))) {
        answer('Thầy cô hãy ghi rõ số câu và phần thi để em xác định đúng câu.');
        return;
      }
      const literalPart = fold(content).match(/\bcau\s+(\d+)\s+(?:o\s+)?phan\s+(i{1,3}|[123]|p[123]|tv|ta|to|logic|science)\b/);
      if (literalPart && intents.some(intent => intent.args.number === Number(literalPart[1]) &&
          typeof intent.args.part === 'string' && sectionId(intent.args.part) !== sectionId(literalPart[2]))) {
        answer('Phần thi trong thao tác chưa khớp yêu cầu. Thầy cô hãy ghi rõ phần và số câu.');
        return;
      }
      const receipts = await execute(intents, runtime, binding, alive, content, messageId);
      if (!alive()) return;
      // A sidebar title change can affect runtime bindings. Keep a pending confirmation tied to its original state.
      if (suggestedTitle && !pending.current && receipts.some(receipt => receipt.status === 'succeeded')) {
        store.suggestTitle(id, suggestedTitle, messageId, titleQuality);
      }
      const stopped = receipts.length < intents.length;
      answer([...receipts.map(receipt => receipt.text),
        ...(stopped ? ['Các bước tiếp theo chưa được thực hiện. Thầy cô hãy kiểm tra trạng thái hiện tại.'] : []),
      ].join('\n'));
    } catch (error) {
      if (!controller.signal.aborted) {
        const reason = error instanceof Error ? error.message : '';
        answer(reason === 'agent_rate' ? 'Trợ lý đang nhận quá nhiều yêu cầu. Thầy cô thử lại sau một lát.'
          : reason.startsWith('agent_') ? 'Chưa kết nối được dịch vụ hiểu yêu cầu. Thầy cô có thể dùng các nút trong ASTRA.'
            : error instanceof ApiError ? error.message
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
      const effect = dispatch(navigation, undefined, admission.text) as Effect;
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
  const regenerateQuestion = async (
    sessionId: string, jobId: string, question: QuestionItem, instruction: string, workspaceId?: string,
  ) => {
    const previousRevision = question.examRevision;
    const regenerated = await examService.regenerateQuestion(
      jobId, question.id, instruction, previousRevision, workspaceId, question.stableId,
    );
    if (previousRevision !== undefined && regenerated.examRevision === previousRevision + 1) {
      setUndo({ sessionId, jobId, previousRevision, revision: regenerated.examRevision });
    }
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
  const handleVerifyQuestion = async (questionId: number) => {
    const session = active;
    if (!session?.jobId || session.package?.revision === undefined || !examService.verifyQuestion) return;
    setVerifyingQuestionId(questionId);
    try {
      await examService.verifyQuestion(session.jobId, questionId, session.package.revision);
      await store.refresh(session.id);
    } catch (error) {
      await store.handleActionError(session.id, error);
    } finally {
      setVerifyingQuestionId(current => (current === questionId ? null : current));
    }
  };
  const handleApproveQuestion = async (questionId: number, reason = '') => {
    const session = active;
    if (!session?.jobId || session.package?.revision === undefined || !examService.approveQuestion) return;
    setApprovingQuestionId(questionId);
    try {
      const updated = await examService.approveQuestion(
        session.jobId,
        questionId,
        session.package.revision,
        reason,
        'local-teacher',
      );
      store.acceptPackage(session.id, updated.examId, updated);
    } catch (error) {
      await store.handleActionError(session.id, error);
      throw error;
    } finally {
      setApprovingQuestionId(current => (current === questionId ? null : current));
    }
  };
  const handlePreviewOpened = useCallback(() => {
    if (activeId && !agentOpenedPdf) store.markPreviewOpened(activeId);
  }, [store, activeId, agentOpenedPdf]);
  const openPdfManually = () => { setAgentOpenedPdf(false); setViewMode('pdf'); };
  const handleRetryPreview = useCallback(() => {
    if (activeId) void store.requestPreview(activeId, true);
  }, [store, activeId]);

  const restoreVersion = async (sessionId: string, jobId: string, version: number, revision: number,
    workspaceId?: string, targetJobId?: string) => {
    if (!history) return;
    try {
      const pkg = await history.restore(jobId, version, revision, workspaceId, targetJobId);
      if (pkg.examId !== jobId) await store.loadLibrary();
      store.acceptPackage(sessionId, pkg.examId, pkg);
      setViewMode('paper');
      setUndo(previous => previous?.sessionId === sessionId ? undefined : previous);
    } catch (error) {
      await store.handleActionError(sessionId, error);
      throw error;
    }
  };

  const undoRegeneration = async () => {
    if (!canUndo || !undo || undoing) return;
    setUndoing(true);
    try { await restoreVersion(undo.sessionId, undo.jobId, undo.previousRevision, undo.revision); }
    catch { /* The workspace shows the restore error. */ }
    finally { setUndoing(false); }
  };

  const undoRecordedChange = async (message: ChatMessage) => {
    const library = examService.workspaceLibrary;
    const revision = active?.package?.revision;
    if (!library || !sharedId || !revision || !message.changeId || !message.examVersion || undoing) return;
    setUndoing(true);
    setUndoConflict(undefined);
    try {
      const pkg = await library.undoChange(sharedId, message.examVersion.jobId, message.changeId, revision);
      store.acceptPackage(sharedId, pkg.examId, pkg);
      setViewMode('paper');
    } catch (error) {
      if (error instanceof ApiError && error.code === 'exam_undo_conflict' && error.details) {
        const comparison = error.details as { current: string; afterChange: string; beforeChange: string };
        setUndoConflict({ id: sharedId, ...comparison });
      } else {
        await store.handleActionError(sharedId, error);
      }
    } finally { setUndoing(false); }
  };

  const branchFromMessage = async (id: string, message: ChatMessage) => {
    try {
      let branchId: string | null;
      try { branchId = await store.branchAtMessage(id, message.id); }
      catch (error) {
        if (!(error instanceof ApiError) || error.code !== 'branch_version_unknown') throw error;
        if (!window.confirm('Tin nhắn này chưa có phiên bản đã lưu. Tạo nhánh từ đề đang dùng?')) return;
        branchId = await store.branchAtMessage(id, message.id, true);
      }
      if (branchId) openSession(branchId);
    } catch (error) {
      await store.handleActionError(id, error);
    }
  };

  const editQuestion = async (target: EditorTarget, kind: 'save' | 'verify' | 'regen', value?: QuestionItem | string) => {
    if (editorBusy.current.has(target.sessionId)) throw new Error('Đang xử lý một thao tác chỉnh sửa.');
    editorBusy.current.add(target.sessionId);
    try {
      if (kind === 'save') await examService.updateQuestion(target.jobId, value as QuestionItem, target.workspaceId);
      else if (kind === 'regen') await regenerateQuestion(
        target.sessionId, target.jobId, target.question, value as string, target.workspaceId,
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
      current?.conversation?.questionReference,
      store.getSnapshot().map(item => [item.id, item.title])]);
  };
  const dispatch = (intent: Intent, expected?: string, message = '', messageId = '', resolved?: Intake): Effect | Promise<Effect> => {
    const failed = failure;
    const succeeded = success;
    const current = store.getSnapshot().find(session => session.id === activeId);
    const activeTurn = turn.current;
    const validTurn = () => !!activeTurn && turn.current === activeTurn && !activeTurn.signal.aborted;
    const prepare = (text: string, run: Confirmation['run']): Effect => {
      if (!current) return failed('Hãy mở không gian soạn đề trước.');
      pending.current = { workspaceId: current.id, binding: binding(), expires: Date.now() + CONFIRMATION_TTL_MS, run };
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
        if (/^(nay|do|kia)$/.test(title)) return failed('Thầy cô hãy ghi tên của đề muốn mở.');
        if (!title && !/\b(vua tao|vua roi|gan nhat|moi nhat|recent|latest)\b/.test(fold(message))) {
          return failed('Thầy cô muốn mở đề nào trong tủ đề?');
        }
        const eligible = store.getSnapshot().filter(item => title || item.id !== current?.id || item.jobId ||
          item.messages.filter(entry => entry.role === 'user').length > 1);
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
          if (!current.intake.formatId) {
            const family = current.intake.family === 'thpt' ? 'THPT' : current.intake.family === 'vact' ? 'V-ACT' : undefined;
            return succeeded(family ? 'Thầy cô đang xem xét dạng ' + family + '. Chưa chọn mẫu cụ thể.' : 'Thầy cô chưa chọn dạng đề.');
          }
          const label = current.intake.formatId === 'vact' ? 'V-ACT' : current.intake.subject && current.intake.subject !== 'Toán Học' ? current.intake.subject + ' THPT' : 'Toán THPT';
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
          return store.branchAtMessage(current.id, target.id).then(id => {
            if (!id) return failed('Chưa tạo được nhánh hội thoại.');
            flushSync(() => { setEditor(null); openSession(id); });
            store.appendMessage(id, 'assistant', 'Đã mở nhánh hội thoại.');
            return succeeded('Đã tạo nhánh hội thoại.');
          }).catch(() => failed('Chưa xác nhận được nhánh hội thoại đã lưu. Hãy tải lại tủ đề.'));
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
        return prepare(`Xóa “${target.title}” khỏi tủ đề.`, async () => {
          const latest = store.getSnapshot().find(item => item.id === target.id);
          if (!latest || latest.status === 'generating' || latest.title !== target.title) return failed('Đề đã thay đổi. Hãy kiểm tra lại tủ đề.');
          if (!await store.remove(target.id)) return failed(store.getLibraryError() || 'Chưa xóa được đề khỏi tủ đề.');
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
            if (runtimeRef.current?.binding() !== expected || !validTurn()) {
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
            if (resolved?.formatId === format.id && resolved.version && resolved.version !== format.version) {
              return failed('Mẫu đề đã đổi phiên bản. Thầy cô hãy gửi lại yêu cầu.');
            }
            const family = familyFor(format);
            const named = mentionedFamilies(message);
            if (named.length === 1 && named[0] !== family) return failed('Mẫu được đề xuất khác với dạng đề thầy cô vừa nêu.');
            const compatibility = resolveIntake({ mode: 'structure', family }, message, undefined, formats, messageId);
            if ('text' in compatibility && !compatibility.title) return failed(compatibility.text);
            const intake = { ...resolved, sourceId: messageId, formatId: format.id, version: format.version,
              family, subject: resolved?.subject ?? format.subjects[0] };
            const automaticTitle = family === 'vact' ? 'Soạn đề V-ACT' : 'Đề thi thử ' + format.displayName;
            const expanded = intent.args.details === true || intent.id === 'FORMAT_DETAILS';
            if (intent.id !== 'PREPARE_GENERATION') {
              flushSync(() => {
                store.setIntake(current.id, { ...intake, phase: 'selected' });
                store.suggestTitle(current.id, automaticTitle, messageId, 3);
                setAgentSelection({ formats, id: format.id, expanded });
                setConfigureId(current.id);
                setShowQuickModal(true);
              });
              return { ...succeeded('Đã chọn mẫu. ' + formatOverview(format)), expectedAfter: runtimeRef.current?.binding() };
            }
            const proposal = prepareParams(format, intent.args, message, resolved?.topic);
            if (!proposal.params) return failed(proposal.error);
            const payload = proposal.params;
            if (current.errorCode === 'network_error' && current.requestSignature &&
                current.requestSignature !== JSON.stringify(payload)) {
              return failed('Lần gửi trước chưa rõ kết quả. Hãy thử lại với thông số cũ trước khi đổi yêu cầu.');
            }
            try {
              await evaluateExamFormat(payload);
            } catch (error) {
              if (runtimeRef.current?.binding() === expected && validTurn()) {
                store.setIntake(current.id, { ...intake, topic: proposal.topic, phase: 'selected', validation: 'failed' });
              }
              return failed(error instanceof Error ? error.message : 'Chưa kiểm tra được chuyên đề theo mẫu đề.');
            }
            if (runtimeRef.current?.binding() !== expected || !validTurn()) {
              return failed('Màn hình đã thay đổi trong lúc kiểm tra mẫu đề.');
            }
            const summary = `${format.displayName} · ${format.totalQuestions} câu · ${format.durationMinutes} phút.${proposal.topic ? ` Chuyên đề: ${proposal.topic}.` : ''} Bấm “Tạo đề thi” để xác nhận gửi yêu cầu.`;
            flushSync(() => {
              store.setIntake(current.id, { ...intake, topic: proposal.topic, phase: 'evaluated', validation: 'passed' });
              store.suggestTitle(current.id, proposal.topic ? 'Đề ôn tập ' + proposal.topic.replace(' và ', ' – ') : automaticTitle,
                messageId, proposal.topic ? 4 : 3);
              setAgentSelection({ formats, id: format.id, expanded: true, summary });
              setConfigureId(current.id);
              setShowQuickModal(true);
            });
            pending.current = {
              workspaceId: current.id,
              binding: runtimeRef.current!.binding(),
              expires: Date.now() + CONFIRMATION_TTL_MS,
              run: async () => {
                flushSync(() => { setShowQuickModal(false); setAgentSelection(undefined); });
                store.setIntake(current.id, { ...intake, topic: proposal.topic, phase: 'confirmed', validation: 'passed' });
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
      case 'PATCH_EDITOR':
      case 'VERIFY_QUESTION':
      case 'REGENERATE_QUESTION': {
        if (!current?.jobId || current.status !== 'complete' || !current.package || showQuickModal) return failed('Chỉ có thể thao tác với câu hỏi trong đề đã tạo xong.');
        const question = resolveQuestion(current, intent.args, editor?.question.stableId);
        if (!question || !question.stableId) return failed('Chưa xác định được câu hỏi. Thầy cô hãy ghi số câu và phần thi hoặc mở câu trong trình chỉnh sửa.');
        const label = `câu ${displayNumber(question)}${question.part ? ` (${question.part})` : ''}`;
        const target = { sessionId: current.id, jobId: current.jobId, question, workspaceId: !current.browserOnly && examService.workspaceLibrary ? current.id : undefined };
        const revision = current.package.revision;
        const remember = () => { if (typeof revision === 'number') flushSync(() => store.rememberQuestion(current.id, question.stableId!, current.jobId!, revision, messageId)); };
        if (intent.id === 'FOCUS_QUESTION') {
          if (editor) return failed('Hãy đóng trình chỉnh sửa trước khi chuyển tới câu hỏi.');
          const view = intent.args.view as ExamCanvasViewMode | undefined;
          if (view || viewMode === 'pdf') flushSync(() => setViewMode(view ?? 'paper'));
          if (!canvas.current?.question(question.stableId)) return failed('Câu hỏi chưa hiển thị trong chế độ hiện tại.');
          remember();
          return succeeded(`Đã chuyển đến ${label}.`);
        }
        if (intent.id === 'PATCH_EDITOR') {
          const field = String(intent.args.field);
          const value = String(intent.args.value);
          if (!fold(message).includes(fold(value)) || redact(value) !== value) {
            return failed('Thầy cô hãy ghi chính xác nội dung muốn điền vào câu hỏi.');
          }
          if (editor && editor.question.stableId !== question.stableId) return failed('Thầy cô hãy hoàn tất câu đang mở trước.');
          if (!editor) flushSync(() => setEditor(target));
          let patched = false;
          flushSync(() => { patched = editorControls.current?.patch(field, value) ?? false; });
          return patched ? succeeded(`Đã điền bản nháp cho ${label}. Thầy cô hãy kiểm tra và bấm nút trong trình chỉnh sửa để tiếp tục.`)
            : failed('Nội dung này không phù hợp với trường của câu hỏi đang mở.');
        }
        if (intent.id === 'OPEN_EDITOR') {
          if (editor && editor.question.stableId !== question.stableId) return failed('Hãy hoàn tất hoặc đóng trình chỉnh sửa đang mở.');
          flushSync(() => setEditor(target));
          remember();
          return succeeded(`Đã mở chỉnh sửa ${label}.`);
        }
        if (intent.id === 'VERIFY_QUESTION' && !examService.verifyQuestion) return failed('Kiểm tra lại đáp án chưa khả dụng trong chế độ hiện tại.');
        const verify = intent.id === 'VERIFY_QUESTION';
        if (!verify && (typeof intent.args.instruction !== 'string' ||
            !fold(message).includes(fold(intent.args.instruction)) || redact(intent.args.instruction) !== intent.args.instruction)) {
          return failed('Thầy cô hãy ghi chính xác yêu cầu muốn dùng để tạo lại câu hỏi.');
        }
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
      dispatch: (intent, expected, message, source, intake) => binding() === expected ? dispatch(intent, expected, message, source, intake)
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
        <SidebarExamLibrary sessions={sessions} activeId={screen === 'workspace' ? activeId : null}
          error={libraryError} onRetry={store.retryLibrary} onNew={newExam} onOpen={openManually}
          collapsed={controlsCollapsed} searchSaved={examService.workspaceLibrary?.search}
          browserImport={browserImport} onImport={store.importBrowserLibrary}
          onDelete={async id => {
            if (await store.remove(id) && configureId === id) { setConfigureId(null); setShowQuickModal(false); }
          }} />
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
                <div className="session-context"><strong>{active.mode === 'template' ? active.meta?.title ?? active.title : active.title}</strong></div>
                {(!active.generationId && (active.status === 'draft' || active.status === 'error')) && <div className="session-create-action">
                  {active.error && <p className="session-error-note">{active.error}</p>}
                  <button type="button" className="button-primary" onClick={() => { cancelTurn(); setAgentSelection(undefined); setConfigureId(active.id); setShowQuickModal(true); }}>{active.status === 'error' ? 'Thử tạo lại' : 'Tạo đề từ yêu cầu'}</button>
                </div>}
                {undoConflict?.id === active.id && <div className="editor-error-box" role="alert">
                  <strong>Có xung đột khi hoàn tác. Hãy kiểm tra câu hỏi và ngữ liệu chung.</strong>
                  <details open><summary>So sánh đề bài</summary>
                    <div>Hiện tại: <MathRenderer content={undoConflict.current} /></div>
                    <div>Sau thay đổi: <MathRenderer content={undoConflict.afterChange} /></div>
                    <div>Trước thay đổi: <MathRenderer content={undoConflict.beforeChange} /></div>
                  </details>
                  <button type="button" className="button-secondary" onClick={() => setUndoConflict(undefined)}>Đóng</button>
                </div>}
                <ChatHistory messages={messages} onSuggestion={value => store.setDraft(active.id, value)} onEditMessage={message => store.setDraft(active.id, message.content)} onRetractMessage={message => { cancelTurn(); store.retractMessage(active.id, message.id); }} onBranchMessage={message => { cancelTurn(); void branchFromMessage(active.id, message); }}
                  currentJobId={active.jobId} undoing={undoing} onUndoChange={sharedId && active.package?.revision ? message => void undoRecordedChange(message) : undefined} />
              </>
            ),
            right: (
              <>
                {(active.error || active.generationError) && (
                  <div className="canvas-alert-banner is-error" role="alert">
                    <AlertCircle size={17} aria-hidden="true" />
                    <span>{active.error || active.generationError}</span>
                  </div>
                )}
                {(isGenerating || active.generationId) && active.progress && (
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
                      <span>Cảnh báo cần kiểm tra ({active.package.warnings.length})</span>
                    </summary>
                    <div className="canvas-source-warnings-body">
                      {active.package.warnings.map((warning, i) => (
                        <p key={i}>{warning.questionId && <strong>{warning.questionId} · </strong>}{warning.message}</p>
                      ))}
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
                    onShowHistory={canOpenHistory ? () => setHistorySession(active.id) : undefined}
                    onUndoRegeneration={latestUndo ? () => void undoRecordedChange(latestUndo)
                      : canUndo ? () => void undoRegeneration() : undefined}
                    undoing={undoing}
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
                  warnings={active.package?.warnings}
                  visualWarnings={active.package?.visualWarnings}
                  previewLog={active.previewLog}
                  previewError={active.previewError}
                  previewErrorCode={active.previewErrorCode}
                  artifactChanged={active.artifactChanged}
                  onRetryPreview={handleRetryPreview}
                  onPreviewOpened={handlePreviewOpened}
                  verifyingQuestionId={verifyingQuestionId}
                  approvingQuestionId={approvingQuestionId}
                  onVerifyQuestion={examService.verifyQuestion && active.jobId && active.package?.revision !== undefined && !isGenerating ? id => { void handleVerifyQuestion(id); } : undefined}
                  onApproveQuestion={examService.approveQuestion && active.jobId && active.package?.revision !== undefined && !isGenerating ? (id, reason) => handleApproveQuestion(id, reason) : undefined}
                  onEditQuestion={id => {
                    const question = active.questions.find(item => item.id === id);
                    if (active.jobId && question) setEditor({
                      sessionId: active.id, jobId: active.jobId, question, workspaceId: sharedId ?? undefined,
                    });
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
          onDialogMount={node => { presetDialog.current = node; }}
          agentSelection={agentSelection}
          onManualSelect={() => { pending.current = null; setAgentSelection(undefined); }}
          onStart={handleQuickStart}
          onClose={closeQuickModal}
        />
      )}
      {history && active?.jobId && active.package?.revision && historySession === active.id && (
        <ExamVersionHistory key={active.jobId} history={history} jobId={active.jobId} revision={active.package.revision}
          workspaceId={active.browserOnly ? undefined : active.id}
          onClose={() => setHistorySession(null)} onRestore={async (version, revision, jobId, targetJobId) => {
            await restoreVersion(active.id, jobId, version, revision, active.browserOnly ? undefined : active.id, targetJobId);
            setHistorySession(null);
          }} />
      )}
      {editor && <QuestionEditor controlsRef={editorControls} question={editor.question} onClose={() => setEditor(null)}
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
