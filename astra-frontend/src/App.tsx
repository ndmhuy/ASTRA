import React, { useState, useEffect, useSyncExternalStore, useCallback } from 'react';
import { AstraLogo } from './components/AstraLogo';
import { AstraWelcome } from './components/AstraWelcome';
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

export const App: React.FC = () => {
  const [showWelcome, setShowWelcome] = useState(true);
  const finishWelcome = useCallback(() => setShowWelcome(false), []);
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
    <div className="app-shell">
      <header className="app-header">
        <button className="app-brand" aria-label="ASTRA · Màn hình chính" onClick={() => setScreen('onboarding')}>
          <AstraLogo className="app-brand-logo" /><span>ASTRA</span>
        </button>
        <div className="header-context">{screen === 'workspace' ? 'Soạn đề thi' : 'Công cụ soạn đề cho giáo viên'}</div>
        <div className="header-right">{screen === 'workspace' ? <button className="header-back" onClick={() => { setScreen('onboarding'); setShowQuickModal(false); }}>← Thư viện đề thi</button> : <span className="header-session">Dành cho giáo viên</span>}<span className="header-avatar" aria-label="Giáo viên">GV</span></div>
      </header>

      {/* Main content */}
      {screen === 'onboarding' && (
        <OnboardingFork
          onQuickMode={() => { setConfigureId(null); setShowQuickModal(true); }}
          onProMode={handleProMode}
          sessions={sessions}
          onOpenSession={openSession}
        />
      )}

      {screen === 'workspace' && active && (
        <WorkspaceLayout key={active.id}>
          {{
            left: (
              <>
                {/* Chat pane header */}
                <div
                  style={{
                    padding: '12px 24px',
                    minHeight: 68,
                    borderBottom: '1px solid #e2e8f0',
                    flexShrink: 0,
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>Trợ lý soạn đề</div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Mô tả đề muốn tạo hoặc yêu cầu sửa câu hỏi</div>
                </div>

                <div className="session-context"><strong>{active.title}</strong><span>{active.mode === 'template' ? 'Từ mẫu' : 'Theo yêu cầu'}</span></div>
                {(active.status === 'draft' || active.status === 'error') && <div className="session-create-action">
                  {active.error && <p role="alert">{active.error}</p>}
                  <button className="button-primary" onClick={() => { setConfigureId(active.id); setShowQuickModal(true); }}>{active.status === 'error' ? 'Thử tạo lại' : 'Tạo đề từ yêu cầu'}</button>
                </div>}
                <ChatHistory messages={messages} />
                <ModernChatBar onSend={handleSendMessage} disabled={isGenerating} draft={active.draft} onDraftChange={value => store.setDraft(active.id, value)} />
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
