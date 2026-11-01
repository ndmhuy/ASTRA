import React, { useState, useEffect, useSyncExternalStore, useCallback } from 'react';
import { BookOpen } from 'lucide-react';
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: '#f4f5f2' }}>
      {/* Navbar */}
      <header
        style={{
          height: 64,
          background: '#ffffff',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          flexShrink: 0,
          gap: 16,
        }}
      >
        {/* Brand */}
        <button
          aria-label="ASTRA · Màn hình chính"
          style={{ border: 0, background: 'transparent', display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}
          onClick={() => setScreen('onboarding')}
        >
          <div
            style={{
              width: 30,
              height: 30,
              background: '#edf4ef',
              border: '1px solid #a7f3d0',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <BookOpen style={{ width: 16, height: 16, color: '#24634b' }} />
          </div>
          <span style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
            ASTRA
          </span>
        </button>

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* "Trở lại / Tạo đề mới" trong workspace */}
        {screen === 'workspace' && (
          <button
            onClick={() => {
              setScreen('onboarding');
              setShowQuickModal(false);
            }}
            style={{
              padding: '9px 18px',
              fontSize: 14,
              fontWeight: 600,
              color: '#334155',
              background: '#ffffff',
              border: '1.5px solid #cbd5e1',
              borderRadius: 6,
              cursor: 'pointer',
              transition: 'border-color 150ms ease, background 150ms ease',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = '#94a3b8';
              (e.currentTarget as HTMLButtonElement).style.background = '#f8fafc';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = '#cbd5e1';
              (e.currentTarget as HTMLButtonElement).style.background = '#ffffff';
            }}
          >
            ← Màn hình chính
          </button>
        )}
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
                  <div style={{ fontSize: 12, color: '#64748b' }}>Nhập yêu cầu để điều chỉnh đề thi</div>
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
