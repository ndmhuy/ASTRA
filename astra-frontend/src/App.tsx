import { House, NotebookPen, Library, Download, FileCheck } from 'lucide-react';
import React, { useState, useEffect, useSyncExternalStore, useCallback } from 'react';
import { AstraWelcome } from './components/AstraWelcome';
import { SchoolArt } from './components/SchoolArt';
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

export const App: React.FC = () => {
  const [showWelcome, setShowWelcome] = useState(true);
  const finishWelcome = useCallback(() => setShowWelcome(false), []);
  const [homeTab, setHomeTab] = useState<'welcome' | 'create' | 'library'>('welcome');
  const [store] = useState(() => new ExamSessions(examService));
  const sessions = useSyncExternalStore(store.subscribe, store.getSnapshot);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [screen, setScreen] = useState<'onboarding' | 'workspace'>('onboarding');
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
    <div className={`app-shell ${screen === 'workspace' ? 'workspace-active' : ''}`}>
      <header className="app-header">
        <button className="app-brand" aria-label="ASTRA · Màn hình chính" onClick={() => { setScreen('onboarding'); setHomeTab('welcome'); }}>
          <AstraLogo className="app-brand-logo" /><span>ASTRA</span>
        </button>
        <nav className="main-tabs" aria-label="Điều hướng chính">{([{id:'welcome',label:'Chào thầy cô',icon:House}, {id:'create',label:'Soạn đề',icon:NotebookPen}, {id:'library',label:'Tủ đề',icon:Library}] as const).map(tab => <button key={tab.id} aria-label={tab.label} title={tab.label} aria-current={(screen === 'workspace' ? tab.id === 'create' : homeTab === tab.id) ? 'page' : undefined} onClick={() => { setHomeTab(tab.id); setScreen('onboarding'); }}><tab.icon size={21} strokeWidth={1.7} aria-hidden="true" /><span>{tab.label}</span></button>)}</nav>
        {screen === 'workspace' && active?.status === 'complete' && <div className="rail-exports" aria-label="Xuất tài liệu">
          <button className="button-primary" onClick={handleExportWord}><Download size={18} aria-hidden="true" />Xuất Word</button>
          <button className="button-secondary" onClick={handleExportAnswer}><FileCheck size={18} aria-hidden="true" />Xuất đáp án</button>
        </div>}
        <div className="header-right"><span className="header-session">Cùng thầy cô, mỗi ngày.</span><span className="header-avatar" aria-label="Giáo viên">GV</span></div>
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
                <div className="studio-chat-heading"><h2>Cùng soạn đề</h2><span className="studio-heading-art" aria-hidden="true"><SchoolArt kind="book" /></span></div>
                <div className="session-context"><strong>{active.title}</strong></div>
                {(active.status === 'draft' || active.status === 'error') && <div className="session-create-action">
                  {active.error && <p role="alert">{active.error}</p>}
                  <button className="button-primary" onClick={() => { setConfigureId(active.id); setShowQuickModal(true); }}>{active.status === 'error' ? 'Thử tạo lại' : 'Tạo đề từ yêu cầu'}</button>
                </div>}
                <ChatHistory messages={messages} onSuggestion={value => store.setDraft(active.id, value)} />
                <ModernChatBar onSend={handleSendMessage} disabled={isGenerating} draft={active.draft} onDraftChange={value => store.setDraft(active.id, value)} />
              </>
            ),
            right: (
              <>
                <CanvasHeader
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  canExport={false}
                />
                <ExamPaperView
                  questions={liveQuestions}
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  latestQuestionCount={prevQuestionCount}
                />
              </>
            ),
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
