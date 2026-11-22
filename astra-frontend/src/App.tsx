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
    setViewMode('paper');
    store.setActiveSession(screen === 'workspace' ? activeId : null);
  }, [store, screen, activeId]);
  useEffect(() => () => { if (transitionTimer.current) clearTimeout(transitionTimer.current); }, []);
  const cancelTransition = () => { composerOrigin.current = null; if (transitionTimer.current) clearTimeout(transitionTimer.current); setLeavingStart(false); setRevealingWorkspace(false); };
  const openSession = (id: string) => { cancelTransition(); setActiveId(id); setScreen('workspace'); };
  const newExam = () => { cancelTransition(); setActiveId(null); setConfigureId(null); setLandingDraft(''); attachedFiles.current = []; setShowQuickModal(false); setScreen('start'); };
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
  const handleLandingSend = (content: string, options: { searchWeb: boolean; attachedFiles: File[] }) => {
    const id = configureId || store.create('custom');
    store.sendMessage(id, content);
    attachedFiles.current = options.attachedFiles;
    setLandingDraft(''); setConfigureId(id); setShowQuickModal(true);
  };
  const handleQuickStart = (params: ExamRequestParams) => {
    const id = configureId || store.create('template');
    const session = store.getSnapshot().find(item => item.id === id);
    const instructions = session?.messages.filter(message => message.role === 'user').map(message => message.content).join('\n');
    setShowQuickModal(false);
    revealSession(id);
    void store.generate(id, { ...params, uploadedFiles: [...params.uploadedFiles, ...attachedFiles.current.map(file => file.name)], prompt: instructions ? `${params.prompt}\n${instructions}` : params.prompt });
  };
  const handleSendMessage = (content: string) => { if (activeId) store.sendMessage(activeId, content); };
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
              </>
            ),
            right: (
              <>
                {active.error && <p role="alert">{active.error}</p>}
                {isGenerating && active.progress && (
                  <p role="status">
                    {formatProgressStatus(active.progress.statusMessage)} ({active.progress.percent}%)
                  </p>
                )}
                {!!active.package?.warnings?.length && <details><summary>Cảnh báo nguồn ({active.package.warnings.length})</summary>{active.package.warnings.map((warning, i) => <p key={i}>{warning.questionId}: {warning.message}</p>)}</details>}
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
            composer: <ModernChatBar onSend={handleSendMessage} disabled={isGenerating} draft={active.draft} onDraftChange={value => store.setDraft(active.id, value)} />,
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
