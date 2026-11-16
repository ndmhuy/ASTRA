import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import welcomeIcon from './assets/navigation/welcome.svg';
import createIcon from './assets/navigation/create.svg';
import libraryIcon from './assets/navigation/library.svg';
import React, { useState, useEffect, useSyncExternalStore, useCallback, useLayoutEffect, useMemo, useRef } from 'react';
import { AstraWelcome } from './components/AstraWelcome';
import { AstraLogo } from './components/AstraLogo';
import { StationeryArt } from './components/StationeryArt';
import { OnboardingFork } from './components/OnboardingFork';
import { QuickPresetModal } from './components/QuickPresetModal';
import { WorkspaceLayout } from './components/Workspace/WorkspaceLayout';
import { ChatHistory } from './components/Workspace/ChatPane/ChatHistory';
import { ModernChatBar } from './components/Workspace/ChatPane/ModernChatBar';
import { CanvasHeader } from './components/Workspace/LiveCanvas/CanvasHeader';
import { ExamPaperView } from './components/Workspace/LiveCanvas/ExamPaperView';
import type { ExamRequestParams, QuestionItem } from './types/exam';
import { examService } from './services/examService';
import { ExamSessions } from './state/examSessions';
import { runAgentTurn } from './integration/agentController';
import type { AgentAction, ScreenContext, ScreenId } from './integration/agentProtocol';
import { UiExecutor, type UiCapabilityResult } from './integration/uiExecutor';
import './styles/workspace.css';
import './styles/classroom.css';
import './styles/studio.css';
import './styles/createVision.css';
import './styles/sidebar.css';
import './styles/classroomStudio.css';

const EMPTY_QUESTIONS: QuestionItem[] = [];

export const App: React.FC = () => {
  const [showWelcome, setShowWelcome] = useState(true);
  const finishWelcome = useCallback(() => setShowWelcome(false), []);
  const [homeTab, setHomeTab] = useState<'welcome' | 'create' | 'library'>('welcome');
  const [store] = useState(() => new ExamSessions(examService));
  const sessions = useSyncExternalStore(store.subscribe, store.getSnapshot);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [screen, setScreen] = useState<'onboarding' | 'workspace'>('onboarding');
  const [controlsCollapsed, setControlsCollapsed] = useState(false);
  const [showQuickModal, setShowQuickModal] = useState(false);
  const [configureId, setConfigureId] = useState<string | null>(null);
  const [uiStateVersion, setUiStateVersion] = useState(1);
  const closeQuickModal = useCallback(() => setShowQuickModal(false), []);
  const active = sessions.find(session => session.id === activeId);
  const messages = active?.messages || [];
  const liveQuestions = active?.questions || EMPTY_QUESTIONS;
  const examMeta = active?.meta || null;
  const isGenerating = active?.status === 'generating';
  const prevQuestionCount = active?.previousCount || 0;
  useEffect(() => () => store.dispose(), [store]);
  const bumpUiState = useCallback(() => setUiStateVersion(value => value + 1), []);
  const openSession = (id: string) => { setActiveId(id); setScreen('workspace'); bumpUiState(); };
  const handleProMode = () => openSession(store.create('custom'));
  const handleQuickStart = (params: ExamRequestParams) => {
    const id = configureId || store.create('template');
    const session = sessions.find(item => item.id === id);
    const instructions = session?.messages.filter(message => message.role === 'user').map(message => message.content).join('\n');
    setShowQuickModal(false);
    openSession(id);
    void store.generate(id, { ...params, prompt: instructions ? `${params.prompt}\n${instructions}` : params.prompt });
  };
  const contextRef = useRef<ScreenContext>({ screen_id: 'welcome', state_version: 1, workspace_session_id: null, selected_question_id: null, question_index_map: {}, available_actions: [] });
  const screenId: ScreenId = screen === 'workspace' ? 'workspace' : homeTab;
  const currentContext = useMemo<ScreenContext>(() => ({
    screen_id: screenId,
    state_version: uiStateVersion,
    workspace_session_id: screen === 'workspace' ? activeId : null,
    selected_question_id: null,
    question_index_map: Object.fromEntries(liveQuestions.map((question, index) => [String(index + 1), String(question.id)])),
    available_actions: ['ui.navigate', 'ui.session.create', 'ui.exam.open_setup', 'ui.sidebar.set_collapsed'],
  }), [activeId, liveQuestions, screen, screenId, uiStateVersion]);
  useLayoutEffect(() => { contextRef.current = currentContext; }, [currentContext]);
  const waitForCommit = useCallback(async (predicate: (context: ScreenContext) => boolean): Promise<ScreenContext> => {
    for (let attempt = 0; attempt < 60; attempt += 1) {
      await new Promise<void>(resolve => window.requestAnimationFrame(() => resolve()));
      if (predicate(contextRef.current)) return contextRef.current;
    }
    throw new Error('ACTION_NOT_OBSERVED');
  }, []);
  const handlersRef = useRef<Record<string, (action: AgentAction) => Promise<UiCapabilityResult>>>({});
  const currentHandlers = useMemo<Record<string, (action: AgentAction) => Promise<UiCapabilityResult>>>(() => ({
    'ui.navigate': async action => {
      const previousVersion = contextRef.current.state_version;
      const target = action.params.screen_id as ScreenId;
      const workspaceId = action.params.workspace_session_id as string | undefined;
      if (target === 'workspace') {
        if (!workspaceId || !store.getSnapshot().some(session => session.id === workspaceId)) throw new Error('SESSION_NOT_FOUND');
        setActiveId(workspaceId);
        setScreen('workspace');
      } else {
        setHomeTab(target);
        setScreen('onboarding');
      }
      bumpUiState();
      const observed = await waitForCommit(context => context.state_version > previousVersion && context.screen_id === target && (target !== 'workspace' || context.workspace_session_id === workspaceId));
      return { data: { screen_id: observed.screen_id, workspace_session_id: observed.workspace_session_id }, stateVersion: observed.state_version };
    },
    'ui.session.create': async action => {
      const previousVersion = contextRef.current.state_version;
      const mode = action.params.mode;
      if (mode !== 'template' && mode !== 'custom') throw new Error('INVALID_PARAMS');
      const createdId = store.create(mode);
      bumpUiState();
      const observed = await waitForCommit(context => context.state_version > previousVersion);
      return { data: { created_workspace_session_id: createdId, mode }, stateVersion: observed.state_version };
    },
    'ui.exam.open_setup': async action => {
      const previousVersion = contextRef.current.state_version;
      const workspaceId = action.params.workspace_session_id;
      if (typeof workspaceId !== 'string' || !store.getSnapshot().some(session => session.id === workspaceId)) throw new Error('SESSION_NOT_FOUND');
      setActiveId(workspaceId);
      setScreen('workspace');
      setConfigureId(workspaceId);
      setShowQuickModal(true);
      bumpUiState();
      const observed = await waitForCommit(context => context.state_version > previousVersion && context.screen_id === 'workspace' && context.workspace_session_id === workspaceId);
      return { data: { workspace_session_id: workspaceId, dialog_visible: true }, stateVersion: observed.state_version };
    },
    'ui.sidebar.set_collapsed': async action => {
      const previousVersion = contextRef.current.state_version;
      const collapsed = action.params.collapsed;
      if (typeof collapsed !== 'boolean') throw new Error('INVALID_PARAMS');
      setControlsCollapsed(collapsed);
      bumpUiState();
      const observed = await waitForCommit(context => context.state_version > previousVersion);
      return { data: { collapsed }, stateVersion: observed.state_version };
    },
  }), [bumpUiState, store, waitForCommit]);
  useLayoutEffect(() => { handlersRef.current = currentHandlers; }, [currentHandlers]);
  const executorRef = useRef<UiExecutor | null>(null);
  useEffect(() => {
    executorRef.current = new UiExecutor({
      'ui.navigate': action => handlersRef.current['ui.navigate'](action),
      'ui.session.create': action => handlersRef.current['ui.session.create'](action),
      'ui.exam.open_setup': action => handlersRef.current['ui.exam.open_setup'](action),
      'ui.sidebar.set_collapsed': action => handlersRef.current['ui.sidebar.set_collapsed'](action),
    }, () => contextRef.current);
    return () => { executorRef.current = null; };
  }, []);
  const handleSendMessage = (content: string) => {
    const executor = executorRef.current;
    if (activeId && executor) void runAgentTurn(activeId, content, { store, getContext: () => contextRef.current, executor });
  };
  const handleExportWord = () => { if (active?.jobId) void examService.downloadExport(active.jobId, 'STUDENT_EXAM', 'docx'); };
  const handleExportAnswer = () => { if (active?.jobId) void examService.downloadExport(active.jobId, 'TEACHER_KEY', 'docx'); };


  if (showWelcome) return <AstraWelcome onComplete={finishWelcome} />;

  return (
    <div className={`app-shell sidebar-mode ${screen === 'workspace' ? 'workspace-active create-mode' : homeTab === 'create' ? 'create-mode' : ''} ${controlsCollapsed ? 'controls-collapsed' : ''}`}>
      <header className="app-header">
        <button className="app-brand" aria-label="ASTRA · Màn hình chính" onClick={() => { setScreen('onboarding'); setHomeTab('welcome'); bumpUiState(); }}>
          <AstraLogo className="app-brand-logo" /><span>ASTRA</span>
        </button>
        <nav id="main-navigation" className="main-tabs" aria-label="Điều hướng chính">{([{id:'welcome',label:'Chào thầy cô',icon:welcomeIcon}, {id:'create',label:'Soạn đề',icon:createIcon}, {id:'library',label:'Tủ đề',icon:libraryIcon}] as const).map(tab => <button key={tab.id} aria-label={tab.label} title={tab.label} aria-current={(screen === 'workspace' ? tab.id === 'create' : homeTab === tab.id) ? 'page' : undefined} onClick={() => { setHomeTab(tab.id); setScreen('onboarding'); bumpUiState(); }}><img className="menu-illustration" src={tab.icon} alt="" aria-hidden="true" /><span>{tab.label}</span></button>)}</nav>
        <button className="sidebar-toggle" type="button" onClick={() => { setControlsCollapsed(value => !value); bumpUiState(); }} aria-label={controlsCollapsed ? 'Mở rộng menu' : 'Thu gọn menu'} aria-expanded={!controlsCollapsed} aria-controls="main-navigation" title={controlsCollapsed ? 'Mở rộng menu để xem tên các mục' : 'Thu gọn menu để có thêm không gian'}>
          {controlsCollapsed ? <PanelLeftOpen size={20} aria-hidden="true" /> : <PanelLeftClose size={20} aria-hidden="true" />}
          <span>{controlsCollapsed ? 'Mở rộng' : 'Thu gọn'}</span>
        </button>
        <div className="header-right"><span className="header-avatar" aria-label="Người dùng: Cùng thầy cô" title="Cùng thầy cô">GV</span><span className="header-session">Cùng thầy cô</span></div>
      </header>

      {/* Main content */}
      {screen === 'onboarding' && (
        <OnboardingFork
          tab={homeTab}
          onTabChange={setHomeTab}
          onQuickMode={() => { setConfigureId(null); setShowQuickModal(true); }}
          onProMode={handleProMode}
          sessions={sessions}
          onOpenSession={openSession}
          onDeleteSession={id => { store.remove(id); if (activeId === id) setActiveId(null); if (configureId === id) setConfigureId(null); }}
        />
      )}

      {screen === 'workspace' && active && (
        <WorkspaceLayout key={active.id}>
          {{
            left: (
              <>
                <div className="studio-chat-heading"><div><span className="studio-kicker">GÓC TRAO ĐỔI</span><h2>Cùng soạn đề</h2></div><StationeryArt kind="pencil" className="chat-heading-art" /></div>
                <div className="session-context"><strong>{active.title}</strong></div>
                {(active.status === 'draft' || active.status === 'error') && <div className="session-create-action">
                  {active.error && <p role="alert">{active.error}</p>}
                  <button className="button-primary" onClick={() => { setConfigureId(active.id); setShowQuickModal(true); }}>{active.status === 'error' ? 'Thử tạo lại' : 'Tạo đề từ yêu cầu'}</button>
                </div>}
                <ChatHistory messages={messages} onSuggestion={value => store.setDraft(active.id, value)} onEditMessage={message => store.setDraft(active.id, message.content)} onRetractMessage={message => store.retractMessage(active.id, message.id)} onBranchMessage={message => { const branchId = store.branchAtMessage(active.id, message.id); if (branchId) setActiveId(branchId); }} />
                {active.agentError && <p role="alert" className="agent-turn-error">{active.agentError}</p>}
              </>
            ),
            right: (
              <>
                <ExamPaperView
                  header={<CanvasHeader
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  canExport={active.status === 'complete'}
                  onExportWord={handleExportWord}
                  onExportAnswer={handleExportAnswer}
                />}
                  questions={liveQuestions}
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  latestQuestionCount={prevQuestionCount}
                />
              </>
            ),
            composer: <ModernChatBar onSend={handleSendMessage} disabled={active.agentPending} draft={active.draft} onDraftChange={value => store.setDraft(active.id, value)} />,
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
    </div>
  );
};

export default App;
