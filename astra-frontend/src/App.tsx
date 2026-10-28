import React, { useState, useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';
import { OnboardingFork } from './components/OnboardingFork';
import { QuickPresetModal } from './components/QuickPresetModal';
import { WorkspaceLayout } from './components/Workspace/WorkspaceLayout';
import { ChatHistory } from './components/Workspace/ChatPane/ChatHistory';
import { ModernChatBar } from './components/Workspace/ChatPane/ModernChatBar';
import { CanvasHeader } from './components/Workspace/LiveCanvas/CanvasHeader';
import { ExamPaperView } from './components/Workspace/LiveCanvas/ExamPaperView';
import type {
  ExamPackage,
  ExamRequestParams,
  QuestionItem,
  ChatMessage,
} from './types/exam';
import { examService } from './services/examService';
import './styles/workspace.css';

type AppScreen = 'onboarding' | 'workspace';

interface ExamMeta {
  title: string;
  subject: string;
  duration: number;
  completedCount: number;
  totalCount: number;
}

export const App: React.FC = () => {
  const [screen, setScreen] = useState<AppScreen>('onboarding');
  const [showQuickModal, setShowQuickModal] = useState(false);

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [liveQuestions, setLiveQuestions] = useState<QuestionItem[]>([]);
  const [examMeta, setExamMeta] = useState<ExamMeta | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [_examPackage, setExamPackage] = useState<ExamPackage | null>(null);
  // Track how many questions existed before the latest batch (for fade-in)
  const [prevQuestionCount, setPrevQuestionCount] = useState(0);

  const jobIdRef = useRef<string | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) unsubscribeRef.current();
    };
  }, []);

  // ── Generation logic ──────────────────────────────────────────────────────

  const startGeneration = async (params: ExamRequestParams) => {
    setIsGenerating(true);
    setLiveQuestions([]);
    setPrevQuestionCount(0);
    setExamPackage(null);
    setExamMeta({
      title: `Đề thi ${params.subject}`,
      subject: params.subject,
      duration: params.durationMinutes,
      completedCount: 0,
      totalCount: params.itemCount,
    });

    // System message
    const sysMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'system',
      content: `Bắt đầu tạo đề ${params.examType} môn ${params.subject} — ${params.itemCount} câu, ${params.durationMinutes} phút.`,
      timestamp: new Date().toISOString(),
    };
    setMessages([sysMsg]);

    try {
      const { jobId } = await examService.startGeneration(params);
      jobIdRef.current = jobId;

      if (unsubscribeRef.current) unsubscribeRef.current();
      unsubscribeRef.current = examService.onProgress(jobId, async (prog) => {
        // Update meta
        setExamMeta((prev) => prev ? { ...prev, completedCount: prog.completedItems } : prev);

        // Append new question preview
        if (prog.latestItemPreview) {
          setLiveQuestions((prev) => {
            const alreadyExists = prev.some((q) => q.id === prog.latestItemPreview!.id);
            if (alreadyExists) return prev;
            setPrevQuestionCount(prev.length);
            return [...prev, prog.latestItemPreview!];
          });
        }

        // Generation complete
        if (prog.stage >= 5 && prog.percent >= 100) {
          setIsGenerating(false);
          const pkg = await examService.getExamPackage(jobId);
          setExamPackage(pkg);
          setLiveQuestions(pkg.questions);
          setExamMeta({
            title: pkg.title,
            subject: pkg.subject,
            duration: pkg.durationMinutes,
            completedCount: pkg.questions.length,
            totalCount: pkg.questions.length,
          });

          const doneMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: `Đã hoàn thành ${pkg.questions.length} câu hỏi. Bạn có thể xem đề thi ở bên phải, xuất file hoặc yêu cầu chỉnh sửa.`,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, doneMsg]);
        }
      });
    } catch (err) {
      console.error('Generation failed:', err);
      setIsGenerating(false);
      const errMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Không thể kết nối với dịch vụ tạo đề. Vui lòng thử lại.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    }
  };

  // ── Start fresh (xoá state cũ, bắt đầu phiên hoàn toàn mới) ─────────────

  const handleStartFresh = () => {
    if (unsubscribeRef.current) { unsubscribeRef.current(); unsubscribeRef.current = null; }
    jobIdRef.current = null;
    setIsGenerating(false);
    setLiveQuestions([]);
    setPrevQuestionCount(0);
    setExamPackage(null);
    setExamMeta(null);
    setMessages([]);
  };

  // ── Quick preset submit ───────────────────────────────────────────────────

  const handleQuickStart = (params: ExamRequestParams) => {
    handleStartFresh();          // xoá state cũ trước khi tạo mới
    setShowQuickModal(false);
    setScreen('workspace');
    startGeneration(params);
  };

  // ── Pro mode — KHÔNG xoá state, chỉ chuyển màn hình ─────────────────────

  const handleProMode = () => {
    setScreen('workspace');
    // Nếu chưa có session nào, khởi tạo blank workspace (không gửi generation)
    // State hiện có (messages, liveQuestions) được GIỮ NGUYÊN
  };

  // ── Chat send ─────────────────────────────────────────────────────────────

  const handleSendMessage = (content: string, _opts: { searchWeb: boolean; attachedFiles: File[] }) => {
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // Simple mock response
    setTimeout(() => {
      const replyMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Đã nhận yêu cầu của bạn. Nếu bạn muốn chỉnh sửa câu hỏi cụ thể, hãy cho biết số câu và hướng thay đổi.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, replyMsg]);
    }, 800);
  };

  // ── Export ────────────────────────────────────────────────────────────────

  const handleExportWord = () => {
    if (!jobIdRef.current) return;
    examService.downloadExport(jobIdRef.current, 'STUDENT_EXAM', 'docx');
  };

  const handleExportAnswer = () => {
    if (!jobIdRef.current) return;
    examService.downloadExport(jobIdRef.current, 'TEACHER_KEY', 'docx');
  };

  // ── Render ────────────────────────────────────────────────────────────────

  const hasActiveSession = liveQuestions.length > 0 || messages.length > 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: '#fafbfa' }}>
      {/* Navbar */}
      <header
        style={{
          height: 58,
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
        <div
          style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}
          onClick={() => setScreen('onboarding')}
        >
          <div
            style={{
              width: 30,
              height: 30,
              background: '#ecfdf5',
              border: '1px solid #a7f3d0',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Sparkles style={{ width: 16, height: 16, color: '#059669' }} />
          </div>
          <span style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
            ASTRA
          </span>
        </div>

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
          onQuickMode={() => { handleStartFresh(); setShowQuickModal(true); }}
          onProMode={handleProMode}
          hasActiveSession={hasActiveSession}
          onResumeSession={() => setScreen('workspace')}
        />
      )}

      {screen === 'workspace' && (
        <WorkspaceLayout>
          {{
            left: (
              <>
                {/* Chat pane header */}
                <div
                  style={{
                    padding: '12px 16px',
                    borderBottom: '1px solid #e2e8f0',
                    flexShrink: 0,
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>Trợ lý soạn đề</div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Nhập yêu cầu để điều chỉnh đề thi</div>
                </div>

                <ChatHistory messages={messages} />
                <ModernChatBar onSend={handleSendMessage} disabled={isGenerating} />
              </>
            ),
            right: (
              <>
                <CanvasHeader
                  examMeta={examMeta}
                  isGenerating={isGenerating}
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
          onStart={handleQuickStart}
          onClose={() => setShowQuickModal(false)}
        />
      )}
    </div>
  );
};

export default App;
