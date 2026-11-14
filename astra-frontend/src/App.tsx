import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import welcomeIcon from './assets/navigation/welcome.svg';
import createIcon from './assets/navigation/create.svg';
import libraryIcon from './assets/navigation/library.svg';
import React, { useState, useEffect, useSyncExternalStore, useCallback } from 'react';
import { AstraWelcome } from './components/AstraWelcome';
import { AstraLogo } from './components/AstraLogo';
import { OnboardingFork } from './components/OnboardingFork';
import { QuickPresetModal } from './components/QuickPresetModal';
import { WorkspaceLayout } from './components/Workspace/WorkspaceLayout';
import { ChatHistory } from './components/Workspace/ChatPane/ChatHistory';
import { ModernChatBar } from './components/Workspace/ChatPane/ModernChatBar';
import { CanvasHeader } from './components/Workspace/LiveCanvas/CanvasHeader';
import { ExamPaperView } from './components/Workspace/LiveCanvas/ExamPaperView';
import type { ExamRequestParams } from './types/exam';
import { examService } from './services/examService';
import { ExamSessions } from './state/examSessions';
import './styles/workspace.css';
import './styles/classroom.css';
import './styles/studio.css';
import './styles/createVision.css';
import './styles/sidebar.css';

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
  const closeQuickModal = useCallback(() => setShowQuickModal(false), []);
  const active = sessions.find(session => session.id === activeId);
  const messages = active?.messages || [];
  const liveQuestions = active?.questions || [];
  const examMeta = active?.meta || null;
  const isGenerating = active?.status === 'generating';
  const prevQuestionCount = active?.previousCount || 0;
  useEffect(() => () => store.dispose(), [store]);
  const openSession = (id: string) => { setActiveId(id); setScreen('workspace'); };
  const handleProMode = () => openSession(store.create('custom'));
  const handleQuickStart = (params: ExamRequestParams) => {
    const id = configureId || store.create('template');
    const session = sessions.find(item => item.id === id);
    const instructions = session?.messages.filter(message => message.role === 'user').map(message => message.content).join('\n');
    setShowQuickModal(false);
    openSession(id);
    void store.generate(id, { ...params, prompt: instructions ? `${params.prompt}\n${instructions}` : params.prompt });
  };
  const handleSendMessage = (content: string) => { if (activeId) store.sendMessage(activeId, content); };
  const handleExportWord = () => { if (active?.jobId) void examService.downloadExport(active.jobId, 'STUDENT_EXAM', 'docx'); };
  const handleExportAnswer = () => { if (active?.jobId) void examService.downloadExport(active.jobId, 'TEACHER_KEY', 'docx'); };


  if (showWelcome) return <AstraWelcome onComplete={finishWelcome} />;

  return (
    <div className={`app-shell sidebar-mode ${screen === 'workspace' ? 'workspace-active create-mode' : homeTab === 'create' ? 'create-mode' : ''} ${controlsCollapsed ? 'controls-collapsed' : ''}`}>
      <header className="app-header">
        <button className="app-brand" aria-label="ASTRA · Màn hình chính" onClick={() => { setScreen('onboarding'); setHomeTab('welcome'); }}>
          <AstraLogo className="app-brand-logo" /><span>ASTRA</span>
        </button>
        <nav id="main-navigation" className="main-tabs" aria-label="Điều hướng chính">{([{id:'welcome',label:'Chào thầy cô',icon:welcomeIcon}, {id:'create',label:'Soạn đề',icon:createIcon}, {id:'library',label:'Tủ đề',icon:libraryIcon}] as const).map(tab => <button key={tab.id} aria-label={tab.label} title={tab.label} aria-current={(screen === 'workspace' ? tab.id === 'create' : homeTab === tab.id) ? 'page' : undefined} onClick={() => { setHomeTab(tab.id); setScreen('onboarding'); }}><img className="menu-illustration" src={tab.icon} alt="" aria-hidden="true" /><span>{tab.label}</span></button>)}</nav>
        <button className="sidebar-toggle" type="button" onClick={() => setControlsCollapsed(value => !value)} aria-label={controlsCollapsed ? 'Mở rộng menu' : 'Thu gọn menu'} aria-expanded={!controlsCollapsed} aria-controls="main-navigation" title={controlsCollapsed ? 'Mở rộng menu để xem tên các mục' : 'Thu gọn menu để có thêm không gian'}>
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
                <CanvasHeader
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  canExport={active.status === 'complete'}
                  onExportWord={handleExportWord}
                  onExportAnswer={handleExportAnswer}
                />
                <ExamPaperView
                  questions={liveQuestions}
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  latestQuestionCount={prevQuestionCount}
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
    </div>
  );
};

export default App;
