import React, { useState, useEffect, useSyncExternalStore, useCallback, useLayoutEffect, useRef } from 'react';
import { WorkspaceStart } from './components/WorkspaceStart';
import { AstraWelcome } from './components/AstraWelcome';
import { SidebarExamLibrary } from './components/SidebarExamLibrary';
import { AstraLogo } from './components/AstraLogo';
import { QuickPresetModal } from './components/QuickPresetModal';
import { WorkspaceLayout } from './components/Workspace/WorkspaceLayout';
import { ChatHistory } from './components/Workspace/ChatPane/ChatHistory';
import { ModernChatBar } from './components/Workspace/ChatPane/ModernChatBar';
import { CanvasHeader } from './components/Workspace/LiveCanvas/CanvasHeader';
import { ExamPaperView, type ExamCanvasViewMode } from './components/Workspace/LiveCanvas/ExamPaperView';
import type { ExamFormat, ExamRequestParams, QuestionItem } from './types/exam';
import { QuestionEditor } from './components/QuestionEditor';
import { AgentNotes } from './components/AgentNotes';
import { examService } from './services/examService';
import { ExamSessions } from './state/examSessions';
import { AgentClient, AgentTransportError } from './agent/client';
import { UI_CAPABILITY_MANIFEST } from './agent/capabilities';
import { UiContextTracker, type UnversionedUiContext } from './agent/context';
import { UiActionExecutor } from './agent/executor';
import { AgentTaskController, isExplicitConfirmation } from './agent/orchestrator';
import type { PendingAgentConfirmation, UiActionProposal, UiContextSnapshot } from './agent/contracts';
import './styles/workspace.css';
import './styles/classroom.css';
import './styles/studio.css';
import './styles/createVision.css';
import './styles/integratedWorkspace.css';
import './styles/integration.css';

export const App: React.FC = () => {
  const [showWelcome, setShowWelcome] = useState(true);
  const finishWelcome = useCallback(() => setShowWelcome(false), []);
  const [landingDraft, setLandingDraft] = useState('');
  const [leavingStart, setLeavingStart] = useState(false);
  const [revealingWorkspace, setRevealingWorkspace] = useState(false);
  const transitionTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const composerOrigin = useRef<DOMRect | null>(null);
  const attachedFiles = useRef<File[]>([]);
  const [store] = useState(() => new ExamSessions(examService));
  const sessions = useSyncExternalStore(store.subscribe, store.getSnapshot);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [screen, setScreen] = useState<'start' | 'workspace'>('start');
  const [viewMode, setViewMode] = useState<ExamCanvasViewMode>('paper');
  const [controlsCollapsed, setControlsCollapsed] = useState(false);
  const [showQuickModal, setShowQuickModal] = useState(false);
  const [configureId, setConfigureId] = useState<string | null>(null);
  const [editor, setEditor] = useState<{ sessionId: string; jobId: string; question: QuestionItem } | null>(null);
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | null>(null);
  const [pendingConfirmation, setPendingConfirmation] = useState<PendingAgentConfirmation | null>(null);
  const [setupState, setSetupState] = useState<{ status: 'closed' | 'loading' | 'ready' | 'error'; formats: ExamFormat[]; selectedId: string; prompt: string; error?: string }>({ status: 'closed', formats: [], selectedId: '', prompt: '' });
  const [approving, setApproving] = useState(false);
  const [agentBusy, setAgentBusy] = useState(false);
  const [agentClient] = useState(() => new AgentClient());
  const [contextTracker] = useState(() => new UiContextTracker());
  const executorRef = useRef<UiActionExecutor | null>(null);
  const [taskController] = useState(() => new AgentTaskController());
  const runtimeRef = useRef({ screen: 'start' as 'start' | 'workspace', activeId: null as string | null, showQuickModal: false, controlsCollapsed: false, viewMode: 'paper' as ExamCanvasViewMode, editor: null as typeof editor, selectedQuestionId: null as number | null, pendingConfirmation: null as PendingAgentConfirmation | null, setupState });
  const closeQuickModal = useCallback(() => { setShowQuickModal(false); setSetupState(value => ({ ...value, status: 'closed' })); setPendingConfirmation(null); }, []);
  const handleSetupState = useCallback((value: { status: 'loading' | 'ready' | 'error'; formats: ExamFormat[]; selectedId: string; error?: string }) => {
    setSetupState(current => ({ ...current, ...value }));
  }, []);
  const active = sessions.find(session => session.id === activeId);
  const messages = active?.messages || [];
  const liveQuestions = active?.questions || [];
  const examMeta = active?.meta || null;
  const isGenerating = active?.status === 'generating';
  const prevQuestionCount = active?.previousCount || 0;
  useEffect(() => { store.resume(); return () => store.dispose(); }, [store]);
  useEffect(() => {
    setViewMode('paper');
    store.setActiveSession(screen === 'workspace' ? activeId : null);
  }, [store, screen, activeId]);
  useEffect(() => () => { if (transitionTimer.current) clearTimeout(transitionTimer.current); }, []);
  useLayoutEffect(() => {
    runtimeRef.current = { screen, activeId, showQuickModal, controlsCollapsed, viewMode, editor, selectedQuestionId, pendingConfirmation, setupState };
  }, [screen, activeId, showQuickModal, controlsCollapsed, viewMode, editor, selectedQuestionId, pendingConfirmation, setupState]);
  const cancelTransition = () => { composerOrigin.current = null; if (transitionTimer.current) clearTimeout(transitionTimer.current); setLeavingStart(false); setRevealingWorkspace(false); };
  const openSession = (id: string) => { cancelTransition(); setActiveId(id); setScreen('workspace'); };
  const newExam = () => { cancelTransition(); setActiveId(null); setConfigureId(null); setLandingDraft(''); attachedFiles.current = []; setShowQuickModal(false); setPendingConfirmation(null); setSelectedQuestionId(null); setSetupState({ status: 'closed', formats: [], selectedId: '', prompt: '' }); setScreen('start'); };
  const revealSession = (id: string) => {
    if (screen === 'workspace') { openSession(id); return; }
    composerOrigin.current = document.querySelector('.integrated-start .composer-box')?.getBoundingClientRect() || null;
    setLeavingStart(true);
    transitionTimer.current = setTimeout(() => {
      setActiveId(id); setScreen('workspace'); setLeavingStart(false); setRevealingWorkspace(true);
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
  function handleLandingSend(content: string) { setLandingDraft(''); void processAgentTurn(null, content); }
  const handleQuickStart = (params: ExamRequestParams) => {
    const id = configureId || store.create('template');
    const session = store.getSnapshot().find(item => item.id === id);
    const instructions = session?.messages.filter(message => message.role === 'user').map(message => message.content).join('\n');
    setShowQuickModal(false);
    revealSession(id);
    void store.generate(id, { ...params, uploadedFiles: [...params.uploadedFiles, ...attachedFiles.current.map(file => file.name)], prompt: instructions ? `${params.prompt}\n${instructions}` : params.prompt });
  };
  const exportFile = async (type: 'STUDENT_EXAM' | 'TEACHER_KEY', format: 'tex' | 'pdf' | 'json') => {
    const session = active;
    if (!session?.jobId) return;
    try { await examService.downloadExport(session.jobId, type, format); }
    catch (error) { await store.handleActionError(session.id, error); }
  };
  const handleExportPdf = () => { void exportFile('STUDENT_EXAM', 'pdf'); };
  const handleExportWord = () => { void exportFile('STUDENT_EXAM', 'tex'); };
  const handleExportAnswer = () => { void exportFile('TEACHER_KEY', 'json'); };
  const approve = async () => {
    const session = active;
    if (!session?.jobId || !session.package || !examService.approveExam || !store.canApprove(session.id)) return;
    setApproving(true);
    try { await examService.approveExam(session.jobId, session.package); await store.refresh(session.id); }
    catch (error) { await store.handleActionError(session.id, error); }
    finally { setApproving(false); }
  };
  const handlePreviewOpened = useCallback(() => {
    if (activeId) store.markPreviewOpened(activeId);
  }, [store, activeId]);
  const handleRetryPreview = useCallback(() => {
    if (activeId) void store.requestPreview(activeId, true);
  }, [store, activeId]);


  const sidebarLabel = controlsCollapsed ? 'Mở rộng thanh điều hướng' : 'Thu gọn thanh điều hướng';
  const handleLogoClick = () => {
    if (window.matchMedia('(min-width: 801px)').matches) setControlsCollapsed(value => !value);
    else newExam();
  };

  const unversionedContext = (): UnversionedUiContext => {
    const runtime = runtimeRef.current;
    const currentSessions = store.getSnapshot();
    const current = currentSessions.find(session => session.id === runtime.activeId);
    const progressSource = import.meta.env.VITE_SERVICE_MODE === 'mock' ? 'mock' : 'real';
    return {
      workspaceId: runtime.screen === 'workspace' ? runtime.activeId : null,
      screen: runtime.screen,
      activeModal: runtime.editor ? 'question_editor' : runtime.showQuickModal ? 'exam_setup' : null,
      sidebarCollapsed: runtime.controlsCollapsed,
      activeJob: current?.status === 'generating' && current.jobId ? {
        id: current.jobId,
        stage: current.progress?.stageName || current.progress?.statusMessage || 'Đang khởi tạo',
        percent: Math.max(0, Math.min(100, current.progress?.percent || 0)),
        source: progressSource,
      } : null,
      examRevision: current?.package?.revision || null,
      examId: current?.package?.examId || null,
      contentHash: current?.package?.contentHash || null,
      selectedQuestion: runtime.selectedQuestionId ? {
        id: runtime.selectedQuestionId,
        stableId: current?.questions.find(item => item.id === runtime.selectedQuestionId)?.stableId || null,
      } : null,
      questions: (current?.questions || []).map(question => ({ id: question.id, stableId: question.stableId || null })),
      viewMode: runtime.viewMode,
      preview: current?.preview ? { status: current.preview.status, revision: current.preview.revision || null, opened: Boolean(current.previewOpenedRevision) } : null,
      approved: current?.package?.approved === true,
      setup: {
        status: runtime.showQuickModal ? runtime.setupState.status : 'closed',
        selectedFormatId: runtime.setupState.selectedId || null,
        prompt: runtime.setupState.prompt,
        formats: runtime.setupState.formats.map(format => ({ id: format.id, version: format.version, displayName: format.displayName, subject: format.subjects[0], grade: format.grades[0], durationMinutes: format.durationMinutes, totalQuestions: format.totalQuestions, available: format.available })),
        ...(runtime.setupState.error ? { errorCode: 'CATALOG_LOAD_FAILED' } : {}),
      },
      pendingConfirmation: runtime.pendingConfirmation,
      activeTask: current?.agentTask || null,
      sessions: currentSessions.slice(0, 50).map(session => ({ id: session.id, title: session.title, status: session.status, createdAt: session.createdAt })),
      notes: (current?.agentNotes || []).map(note => ({ id: note.id, targetQuestion: note.targetQuestion, stableQuestionId: note.stableQuestionId, requestedChange: note.requestedChange, status: note.status })),
      capabilities: UI_CAPABILITY_MANIFEST,
    };
  };
  const captureContext = (): UiContextSnapshot => contextTracker.capture(unversionedContext());

  if (!executorRef.current) {
    executorRef.current = new UiActionExecutor(captureContext, {
      'ui.navigate': params => {
        if (params.destination === 'start') newExam();
        else openSession(String(params.workspaceId));
      },
      'ui.session.create': params => {
        const workspaceId = store.create(params.mode === 'template' ? 'template' : 'custom');
        openSession(workspaceId);
        return { workspaceId };
      },
      'ui.session.open': params => { openSession(String(params.workspaceId)); },
      'ui.exam.open_setup': () => {
        const workspaceId = runtimeRef.current.activeId;
        setConfigureId(workspaceId);
        attachedFiles.current = [];
        setShowQuickModal(true);
      },
      'ui.exam.close_setup': () => closeQuickModal(),
      'ui.exam.configure_setup': params => {
        const runtime = runtimeRef.current;
        const formatId = typeof params.formatId === 'string' ? params.formatId : runtime.setupState.selectedId;
        const prompt = typeof params.prompt === 'string' ? params.prompt : runtime.setupState.prompt;
        const workspaceId = runtime.activeId;
        if (!workspaceId) throw new Error('No active workspace');
        const confirmation: PendingAgentConfirmation = {
          id: crypto.randomUUID(), kind: 'generation', workspaceId,
          summary: `Tạo đề theo định dạng ${formatId}`, createdAt: new Date().toISOString(),
        };
        setSetupState(value => ({ ...value, selectedId: formatId, prompt }));
        setPendingConfirmation(confirmation);
        return { pendingConfirmation: 'generation', confirmationId: confirmation.id };
      },
      'exam.generate.start': async () => {
        const runtime = runtimeRef.current;
        const format = runtime.setupState.formats.find(item => item.id === runtime.setupState.selectedId && item.available);
        if (!runtime.activeId || !format) throw new Error('Setup is not ready');
        const result = await store.generate(runtime.activeId, {
          formatId: format.id, formatVersion: format.version, subject: format.subjects[0], grade: format.grades[0],
          examType: format.examType, durationMinutes: format.durationMinutes, itemCount: format.totalQuestions,
          prompt: runtime.setupState.prompt.trim() || `Tạo đề ${format.displayName}`, uploadedFiles: [],
        });
        if (!result) throw new Error('Generation was not started');
        setPendingConfirmation(null); setShowQuickModal(false);
        return result;
      },
      'ui.exam.view_mode': params => setViewMode(params.mode as ExamCanvasViewMode),
      'ui.question.focus': params => { setSelectedQuestionId(Number(params.questionId)); setViewMode('paper'); },
      'ui.question.open_editor': params => {
        const runtime = runtimeRef.current;
        const session = store.getSnapshot().find(item => item.id === runtime.activeId);
        const question = session?.questions.find(item => item.id === Number(params.questionId));
        if (!session?.jobId || !question) throw new Error('Question is not available');
        setSelectedQuestionId(question.id);
        setEditor({ sessionId: session.id, jobId: session.jobId, question });
      },
      'ui.sidebar.set_collapsed': params => { setControlsCollapsed(params.collapsed === true); },
      'ui.note.add': params => {
        const workspaceId = runtimeRef.current.activeId;
        if (!workspaceId) throw new Error('No active workspace');
        const note = store.addNote(workspaceId, {
          targetQuestion: typeof params.targetQuestion === 'number' ? params.targetQuestion : undefined,
          requestedChange: String(params.requestedChange),
          teacherText: String(params.teacherText || params.requestedChange),
        });
        if (!note) throw new Error('Note was not stored');
        return { noteId: note.id };
      },
      'ui.note.update': params => {
        const workspaceId = runtimeRef.current.activeId;
        if (!workspaceId || !store.updateNote(workspaceId, String(params.noteId), String(params.requestedChange))) throw new Error('Note was not updated');
        return { noteId: String(params.noteId) };
      },
      'ui.note.cancel': params => {
        const workspaceId = runtimeRef.current.activeId;
        if (!workspaceId || !store.cancelNote(workspaceId, String(params.noteId))) throw new Error('Note was not cancelled');
        return { noteId: String(params.noteId) };
      },
      'ui.note.approve': params => {
        const workspaceId = runtimeRef.current.activeId;
        if (!workspaceId || !store.approveNote(workspaceId, String(params.noteId))) throw new Error('Note was not approved');
        const confirmation: PendingAgentConfirmation = {
          id: crypto.randomUUID(), kind: 'revision', workspaceId, noteId: String(params.noteId),
          summary: `Áp dụng ghi chú ${String(params.noteId)}`, createdAt: new Date().toISOString(),
        };
        setPendingConfirmation(confirmation);
        return { pendingConfirmation: 'revision', confirmationId: confirmation.id };
      },
      'exam.note.apply': async params => {
        const workspaceId = runtimeRef.current.activeId;
        if (!workspaceId) throw new Error('No active workspace');
        const result = await store.applyNote(workspaceId, String(params.noteId));
        setPendingConfirmation(null);
        return result;
      },
    }, () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  }

  async function processAgentTurn(initialSessionId: string | null, content: string) {
    if (agentBusy) return;
    let messageSessionId = initialSessionId;
    if (messageSessionId) store.sendMessage(messageSessionId, content);
    setAgentBusy(true);
    try {
      const response = await agentClient.interpret(content, captureContext());
      let proposals = response.decisions.filter((decision): decision is UiActionProposal => decision.kind === 'propose_ui_action');
      const plain = response.decisions.filter(decision => decision.kind !== 'propose_ui_action');
      const pending = runtimeRef.current.pendingConfirmation;
      if (pending && isExplicitConfirmation(content)) {
        const capabilityId = pending.kind === 'generation' ? 'exam.generate.start' : pending.kind === 'revision' ? 'exam.note.apply' : '';
        if (capabilityId) {
          const existing = proposals.find(proposal => proposal.capabilityId === capabilityId);
          const confirmed: UiActionProposal = existing ? {
            ...existing, params: { ...existing.params, confirmationId: pending.id, ...(pending.noteId ? { noteId: pending.noteId } : {}) },
          } : {
            kind: 'propose_ui_action', text: 'Tôi sẽ tiếp tục tác vụ đã chờ xác nhận.', actionId: crypto.randomUUID(),
            capabilityId, expectedStateVersion: captureContext().stateVersion,
            params: { confirmationId: pending.id, ...(pending.noteId ? { noteId: pending.noteId } : {}) }, target: { workspaceId: pending.workspaceId },
          };
          proposals = existing ? proposals.map(item => item === existing ? confirmed : item) : [confirmed];
        }
      }
      const initialContext = captureContext();
      const previousTask = store.getSnapshot().find(item => item.id === initialContext.workspaceId)?.agentTask || null;
      const execution = await taskController.execute(content, initialContext.workspaceId, proposals, executorRef.current!, captureContext, previousTask, task => {
        const workspaceId = task.workspaceId || runtimeRef.current.activeId;
        if (workspaceId) store.setAgentTask(workspaceId, { ...task, workspaceId });
      });
      const receipts = execution.receipts;
      const created = receipts.find(receipt => receipt.status === 'success' && typeof receipt.result?.workspaceId === 'string');
      if (!messageSessionId && created) messageSessionId = String(created.result?.workspaceId);
      if (!messageSessionId) {
        const currentId = runtimeRef.current.activeId;
        messageSessionId = currentId || store.create('custom');
        if (!currentId) openSession(messageSessionId);
      }
      if (!initialSessionId) store.sendMessage(messageSessionId, content);
      store.setAgentTask(messageSessionId, { ...execution.task, workspaceId: messageSessionId });
      for (const decision of plain) store.addAssistantMessage(messageSessionId, decision.text);
      proposals.forEach((proposal, index) => {
        const receipt = receipts[index];
        if (receipt.status === 'success') {
          store.addAssistantMessage(messageSessionId!, `${proposal.text} Giao diện đã xác nhận thao tác thành công.`);
        } else {
          const detail = receipt.errorCode === 'STALE_CONTEXT'
            ? 'Trạng thái giao diện đã thay đổi nên tôi không thực hiện thao tác cũ.'
            : receipt.errorCode === 'DEPENDENCY_FAILED'
              ? 'Bước trước không thành công nên bước phụ thuộc đã được bỏ qua.'
              : 'Giao diện không xác nhận được kết quả nên thao tác đã dừng an toàn.';
          store.addAssistantMessage(messageSessionId!, `${proposal.text} ${detail}`);
        }
      });
    } catch (error) {
      if (!messageSessionId) {
        messageSessionId = store.create('custom');
        openSession(messageSessionId);
        store.sendMessage(messageSessionId, content);
      }
      const text = error instanceof AgentTransportError ? error.message : 'Agent gặp lỗi cục bộ và chưa thực hiện thao tác nào.';
      store.addAssistantMessage(messageSessionId, text);
    } finally {
      setAgentBusy(false);
    }
  }

  const handleSendMessage = (content: string) => { if (activeId) void processAgentTurn(activeId, content); };

  if (showWelcome) return <AstraWelcome onComplete={finishWelcome} />;

  return (
    <div className={`app-shell create-mode workspace-active integrated-shell ${revealingWorkspace ? 'workspace-revealing' : ''} ${controlsCollapsed ? 'controls-collapsed' : ''}`}>
      <header className="app-header">
        <button className="app-brand rail-logo-toggle" aria-label={`ASTRA — ${sidebarLabel}`} aria-expanded={!controlsCollapsed} title={sidebarLabel} onClick={handleLogoClick}>
          <AstraLogo className="app-brand-logo" /><span>ASTRA</span>
        </button>
        <SidebarExamLibrary sessions={sessions} activeId={screen === 'workspace' ? activeId : null} onNew={newExam} onOpen={openSession} onDelete={id => { store.remove(id); if (activeId === id) newExam(); if (configureId === id) { setConfigureId(null); setShowQuickModal(false); } }} />
        <button className="side-rail-edge" type="button" onClick={() => setControlsCollapsed(value => !value)} aria-label={sidebarLabel} aria-expanded={!controlsCollapsed} title={sidebarLabel} />
        <div className="header-right"><span className="header-avatar" aria-label="Người dùng: Cùng thầy cô" title="Cùng thầy cô">GV</span><span className="header-session">Cùng thầy cô</span></div>
      </header>

      {/* Main content */}
      {screen === 'start' && <WorkspaceStart exiting={leavingStart} draft={landingDraft} onDraftChange={setLandingDraft} onTemplate={() => { setConfigureId(null); attachedFiles.current = []; setShowQuickModal(true); }} onDetailed={handleDetailedStart} onSend={handleLandingSend} />}

      {screen === 'workspace' && active && (
        <WorkspaceLayout key={active.id}>
          {{
            left: (
              <>
                <div className="studio-chat-heading"><div><span className="studio-kicker">KHÔNG GIAN SOẠN ĐỀ</span><h2>Cùng soạn đề</h2></div></div>
                <div className="session-context"><strong>{active.title}</strong></div>
                {(active.status === 'draft' || active.status === 'error') && <div className="session-create-action">
                  {active.error && <p role="alert">{active.error}</p>}
                  <button className="button-primary" onClick={() => { setConfigureId(active.id); setShowQuickModal(true); }}>{active.status === 'error' ? 'Thử tạo lại' : 'Tạo đề từ yêu cầu'}</button>
                </div>}
                <ChatHistory messages={messages} onSuggestion={value => store.setDraft(active.id, value)} onEditMessage={message => store.setDraft(active.id, message.content)} onRetractMessage={message => store.retractMessage(active.id, message.id)} onBranchMessage={message => { const branchId = store.branchAtMessage(active.id, message.id); if (branchId) setActiveId(branchId); }} />
                <AgentNotes notes={active.agentNotes || []}
                  onCancel={noteId => store.cancelNote(active.id, noteId)}
                  onPrepareEdit={note => store.setDraft(active.id, `Sửa ghi chú ${note.id}: ${note.requestedChange}`)}
                  onApprove={noteId => {
                    if (!store.approveNote(active.id, noteId)) return;
                    setPendingConfirmation({ id: crypto.randomUUID(), kind: 'revision', workspaceId: active.id, noteId, summary: `Áp dụng ghi chú ${noteId}`, createdAt: new Date().toISOString() });
                  }}
                  onApply={noteId => { void store.applyNote(active.id, noteId).then(() => setPendingConfirmation(null)); }} />
              </>
            ),
            right: (
              <>
                {active.error && <p role="alert">{active.error}</p>}
                {isGenerating && active.progress && <p role="status">{active.progress.statusMessage} ({active.progress.percent}%)</p>}
                {!!active.package?.warnings?.length && <details><summary>Cảnh báo nguồn ({active.package.warnings.length})</summary>{active.package.warnings.map((warning, i) => <p key={i}>{warning.questionId}: {warning.message}</p>)}</details>}
                {!!active.package?.visualWarnings?.length && (
                  <div className="pdf-preview-warning" role="alert">
                    <strong>Cảnh báo hình vẽ / bảng biểu ({active.package.visualWarnings.length})</strong>
                    <p>Các đề đã tạo không tự sinh hình vẽ còn thiếu trong PDF. Hãy sửa hoặc tạo lại câu hỏi bị ảnh hưởng.</p>
                    {active.package.visualWarnings.map((warning, i) => (
                      <p key={`${warning.questionId}-${i}`}><code>{warning.questionId}</code>: {warning.code}</p>
                    ))}
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
                    onOpenPdfPreview={() => setViewMode('pdf')}
                    onApprove={() => { void approve(); }}
                    onExportPdf={handleExportPdf}
                    onExportWord={handleExportWord}
                    onExportAnswer={handleExportAnswer}
                  />}
                  questions={liveQuestions}
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  latestQuestionCount={prevQuestionCount}
                  viewMode={viewMode}
                  onViewModeChange={setViewMode}
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
                  focusedQuestionId={selectedQuestionId}
                  onEditQuestion={id => {
                    const question = active.questions.find(item => item.id === id);
                    if (active.jobId && question) { setSelectedQuestionId(id); setEditor({ sessionId: active.id, jobId: active.jobId, question }); }
                  }}
                />
              </>
            ),
            composer: <ModernChatBar onSend={handleSendMessage} busy={agentBusy} draft={active.draft} onDraftChange={value => store.setDraft(active.id, value)} />,
          }}
        </WorkspaceLayout>
      )}

      {/* Quick preset modal */}
      {showQuickModal && (
        <QuickPresetModal
          title={configureId ? 'Thiết lập đề theo yêu cầu' : 'Tạo đề từ mẫu'}
          onStart={handleQuickStart}
          onClose={closeQuickModal}
          selectedId={setupState.selectedId}
          prompt={setupState.prompt}
          onStateChange={handleSetupState}
        />
      )}
      {editor && <QuestionEditor question={editor.question} onClose={() => setEditor(null)}
        onSave={async question => {
          try {
            await examService.updateQuestion(editor.jobId, question);
            store.invalidatePreview(editor.sessionId);
            await store.refresh(editor.sessionId);
            setEditor(null);
          } catch (error) {
            await store.handleActionError(editor.sessionId, error);
            throw error;
          }
        }}
        onRegenerate={async instruction => {
          try {
            await examService.regenerateQuestion(editor.jobId, editor.question.id, instruction, editor.question.examRevision);
            store.invalidatePreview(editor.sessionId);
            await store.refresh(editor.sessionId);
            setEditor(null);
          } catch (error) {
            await store.handleActionError(editor.sessionId, error);
            throw error;
          }
        }}
      />}
    </div>
  );
};

export default App;
