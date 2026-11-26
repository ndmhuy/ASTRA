import React, { useState, useEffect, useSyncExternalStore, useCallback, useLayoutEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
import { interpret } from './agent/client';
import { admit, execute, fastRoute, fold, mayDispatch, type Effect, type Runtime } from './agent/recipes';
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
import { ExamPaperView, type ExamCanvasViewMode } from './components/Workspace/LiveCanvas/ExamPaperView';
import type { ExamRequestParams, QuestionItem } from './types/exam';
import { QuestionEditor } from './components/QuestionEditor';
import { examService } from './services/examService';
import { ExamSessions } from './state/examSessions';
import { formatProgressStatus, formatVisualWarning } from './utils/userMessages.ts';
import './styles/workspace.css';
import './styles/classroom.css';
import './styles/studio.css';
import './styles/createVision.css';
import './styles/integratedWorkspace.css';
import './styles/integration.css';
import './styles/atelier.css';

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
  const turn = useRef<AbortController | null>(null);
  const [admissionError, setAdmissionError] = useState('');
  const runtimeRef = useRef<Runtime | null>(null);
  const [chatPending, setChatPending] = useState(false);
  const cancelTurn = () => { turn.current?.abort(); turn.current = null; setChatPending(false); };
  useEffect(() => () => turn.current?.abort(), []);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [screen, setScreen] = useState<'start' | 'workspace'>('start');
  const [viewMode, setViewMode] = useState<ExamCanvasViewMode>('paper');
  const [controlsCollapsed, setControlsCollapsed] = useState(false);
  const [showQuickModal, setShowQuickModal] = useState(false);
  const [configureId, setConfigureId] = useState<string | null>(null);
  const [editor, setEditor] = useState<{ sessionId: string; jobId: string; question: QuestionItem } | null>(null);
  const [approving, setApproving] = useState(false);
  const closeQuickModal = useCallback(() => setShowQuickModal(false), []);
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
  const openSession = (id: string) => { cancelTransition(); setViewMode('paper'); setActiveId(id); setScreen('workspace'); };
  const openManually = (id: string) => { cancelTurn(); setShowQuickModal(false); setConfigureId(null); setEditor(null); openSession(id); };
  const newExam = () => { cancelTurn(); cancelTransition(); setActiveId(null); setConfigureId(null); setLandingDraft(''); attachedFiles.current = []; setShowQuickModal(false); setScreen('start'); };
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
    const answer = (text: string) => store.appendMessage(id, 'assistant', text);
    store.appendMessage(id, 'user', content, messageId);
    const runtime: Runtime = {
      binding: () => runtimeRef.current!.binding(),
      dispatch: (intent, expected) => runtimeRef.current!.dispatch(intent, expected),
    };
    const binding = runtime.binding();
    const alive = () => !controller.signal.aborted && !!store.getSnapshot().find(s => s.id === id)?.messages.some(m => m.id === messageId);
    try {
      if (options.searchWeb || options.attachedFiles.length) {
        answer('ASTRA hiện chưa hỗ trợ tìm web hoặc tải tệp. Thầy cô có thể gửi nội dung dạng văn bản.');
        return;
      }
      const local = fastRoute(content);
      if (local && 'text' in local) { answer(local.text); return; }
      if (local && 'confirm' in local) {
        answer(local.confirm ? 'Hiện chưa có thao tác nào đang chờ xác nhận.' : 'Hiện chưa có tác vụ trò chuyện đang chờ.');
        return;
      }
      if (!mayDispatch(content)) {
        answer('Thầy cô muốn em thực hiện thao tác cụ thể nào? Em chưa thao tác.');
        return;
      }
      const decision = local && 'intents' in local ? { kind: 'task', intents: local.intents }
        : await interpret(id, messageId, content, {
          screen, setup: showQuickModal, status: store.getSnapshot().find(s => s.id === id)?.status ?? 'draft', view: viewMode,
        }, controller.signal);
      if (!alive()) return;
      if (decision.kind !== 'task') {
        answer(decision.kind === 'temporarily_unavailable'
          ? 'Dịch vụ hiểu yêu cầu đang chưa sẵn sàng. Thầy cô vẫn có thể dùng các nút trong ASTRA.'
          : decision.kind === 'unsupported'
            ? 'Tính năng này chưa có trong ASTRA.'
            : 'Thầy cô muốn thao tác nào trong ASTRA? Em cần thêm thông tin để thực hiện.');
        return;
      }
      const receipts = await execute(decision.intents, runtime, binding, alive);
      if (!alive()) return;
      const stopped = receipts.length < decision.intents.length;
      answer([...receipts.map(receipt => receipt.text),
        ...(stopped ? ['Các bước tiếp theo chưa được thực hiện. Thầy cô hãy kiểm tra trạng thái hiện tại.'] : []),
      ].join('\n'));
    } catch {
      if (!controller.signal.aborted) answer('Chưa kết nối được với trợ lý ASTRA. Thầy cô có thể thử lại.');
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
      const effect = dispatch(navigation);
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
    const id = configureId || store.create('template');
    const session = store.getSnapshot().find(item => item.id === id);
    const instructions = session?.messages.filter(message => message.role === 'user').map(message => message.content).join('\n');
    setShowQuickModal(false);
    revealSession(id);
    void store.generate(id, { ...params, uploadedFiles: [...params.uploadedFiles, ...attachedFiles.current.map(file => file.name)], prompt: instructions ? `${params.prompt}\n${instructions}` : params.prompt });
  };
  const handleSendMessage = (content: string, options: { searchWeb: boolean; attachedFiles: File[] }) => {
    if (activeId) void sendTurn(activeId, content, options);
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


  const binding = () => {
    const current = store.getSnapshot().find(s => s.id === activeId);
    return JSON.stringify([screen, activeId, showQuickModal, configureId, controlsCollapsed, viewMode,
      editor?.question.stableId, current?.status, current?.jobId, current?.package?.revision,
      current?.package?.contentHash, current?.package?.approved, current?.previewOpenedRevision]);
  };
  const dispatch = (intent: Intent): Effect => {
    const failed = (text: string): Effect => ({ status: 'failed', text });
    const succeeded = (text: string): Effect => ({ status: 'succeeded', text });
    const current = store.getSnapshot().find(session => session.id === activeId);
    switch (intent.id) {
      case 'OPEN_SETUP':
        if (!current || !['draft', 'error'].includes(current.status) || editor) return failed('Chỉ có thể mở cấu hình cho đề nháp hoặc lần tạo bị lỗi.');
        flushSync(() => { setConfigureId(current.id); setShowQuickModal(true); });
        return runtimeRef.current!.binding() !== '' && document.getElementById('astra-preset-dialog')
          ? succeeded('Đã mở phần cấu hình mẫu đề.')
          : failed('Chưa mở được phần cấu hình mẫu đề.');
      case 'HOME':
        flushSync(() => { cancelTransition(); setEditor(null); setShowQuickModal(false); setConfigureId(null); setActiveId(null); setScreen('start'); });
        return succeeded('Đã về màn hình bắt đầu.');
      case 'CREATE_SESSION': {
        const id = store.create('custom');
        flushSync(() => { setShowQuickModal(false); setConfigureId(null); setEditor(null); openSession(id); });
        return succeeded('Đã mở một không gian soạn đề mới.');
      }
      case 'OPEN_SESSION': {
        const title = typeof intent.args.title === 'string' ? fold(intent.args.title) : '';
        const eligible = store.getSnapshot().filter(item => item.id !== current?.id || title);
        const exact = eligible.filter(item => fold(item.title) === title);
        const matches = title ? (exact.length ? exact : eligible.filter(item => fold(item.title).includes(title)))
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
        flushSync(() => setControlsCollapsed(intent.args.collapsed === true));
        return succeeded(intent.args.collapsed ? 'Đã thu gọn thanh điều hướng.' : 'Đã mở rộng thanh điều hướng.');
      default: return failed('Thao tác này chưa có liên kết với màn hình hiện tại.');
    }
  };
  useLayoutEffect(() => {
    runtimeRef.current = {
      binding,
      dispatch: (intent, expected) => binding() === expected ? dispatch(intent)
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

      {admissionError && <div className="canvas-alert-banner is-error" role="alert">{admissionError}</div>}
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
                  {active.error && <p className="session-error-note">{active.error}</p>}
                  <button type="button" className="button-primary" onClick={() => { setConfigureId(active.id); setShowQuickModal(true); }}>{active.status === 'error' ? 'Thử tạo lại' : 'Tạo đề từ yêu cầu'}</button>
                </div>}
                <ChatHistory messages={messages} onSuggestion={value => store.setDraft(active.id, value)} onEditMessage={message => store.setDraft(active.id, message.content)} onRetractMessage={message => { cancelTurn(); store.retractMessage(active.id, message.id); }} onBranchMessage={message => { const branchId = store.branchAtMessage(active.id, message.id); if (branchId) openManually(branchId); }} />
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
                    onOpenPdfPreview={() => setViewMode('pdf')}
                    onApprove={() => { void approve(); }}
                    onExportPdf={handleExportPdf}
                    onExportWord={handleExportWord}
                    onExportAnswer={handleExportAnswer}
                  />}
                  questions={liveQuestions}
                  passages={active.package?.passages}
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
          onStart={handleQuickStart}
          onClose={closeQuickModal}
        />
      )}
      {editor && <QuestionEditor question={editor.question} onClose={() => setEditor(null)}
        onVerify={examService.verifyQuestion && editor.question.examRevision !== undefined ? async () => {
          try {
            await examService.verifyQuestion!(editor.jobId, editor.question.id, editor.question.examRevision!);
            await store.refresh(editor.sessionId);
            setViewMode('review');
            setEditor(null);
          } catch (error) {
            await store.handleActionError(editor.sessionId, error);
            throw error;
          }
        } : undefined}
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
