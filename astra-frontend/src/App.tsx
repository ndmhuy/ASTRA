import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { ConfigView } from './components/ConfigView';
import { StepperView } from './components/StepperView';
import { ReviewView } from './components/ReviewView';
import type { 
  ExamPackage, 
  ExamRequestParams, 
  GenerationProgress, 
  QuestionItem 
} from './types/exam';
import { examService } from './services/examService';

export const App: React.FC = () => {
  // Screen state: 'config' | 'stepper' | 'review'
  const [currentScreen, setCurrentScreen] = useState<'config' | 'stepper' | 'review'>('config');
  
  // Job and Progress State
  const [jobId, setJobId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState<GenerationProgress>({
    stage: 1,
    stageName: 'Khởi tạo',
    percent: 0,
    estimatedSecondsLeft: 60,
    completedItems: 0,
    totalItems: 40,
    statusMessage: 'Sẵn sàng khởi chạy...'
  });

  // Loaded Exam Package
  const [examPackage, setExamPackage] = useState<ExamPackage | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  // Clean up SSE/progress subscription on unmount
  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, []);

  // Handler: Start generation
  const handleStartGeneration = async (params: ExamRequestParams) => {
    setIsGenerating(true);
    setCurrentScreen('stepper');

    try {
      const { jobId: newJobId } = await examService.startGeneration(params);
      setJobId(newJobId);

      // Subscribe to live multi-agent events
      if (unsubscribeRef.current) unsubscribeRef.current();
      
      unsubscribeRef.current = examService.onProgress(newJobId, async (updatedProgress) => {
        setProgress(updatedProgress);

        // When all 5 stages finish, load the complete exam package
        if (updatedProgress.stage >= 5 && updatedProgress.percent >= 100) {
          setIsGenerating(false);
          const pkg = await examService.getExamPackage(newJobId);
          setExamPackage(pkg);
        }
      });
    } catch (err) {
      console.error('Generation initiation failed:', err);
      setIsGenerating(false);
      alert('Không thể kết nối với dịch vụ tạo đề. Vui lòng thử lại.');
      setCurrentScreen('config');
    }
  };

  // Handler: Update a single question manually
  const handleUpdateQuestion = async (updated: QuestionItem) => {
    if (!examPackage || !jobId) return;

    // Optimistic UI update
    const newQuestions = examPackage.questions.map((q) =>
      q.id === updated.id ? updated : q
    );
    setExamPackage({ ...examPackage, questions: newQuestions });

    try {
      await examService.updateQuestion(jobId, updated);
    } catch (err) {
      console.error('Failed to persist question edit:', err);
    }
  };

  // Handler: Single-question targeted AI regeneration
  const handleRegenerateQuestion = async (questionId: number, instruction?: string): Promise<QuestionItem> => {
    if (!examPackage || !jobId) {
      throw new Error('No active exam package');
    }

    const repaired = await examService.regenerateQuestion(jobId, questionId, instruction);

    const newQuestions = examPackage.questions.map((q) =>
      q.id === questionId ? repaired : q
    );
    setExamPackage({ ...examPackage, questions: newQuestions });
    return repaired;
  };

  // Handler: Document Export
  const handleExport = async (type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: 'docx' | 'pdf') => {
    if (!jobId) return;
    await examService.downloadExport(jobId, type, format);
  };

  // Handler: Cancel in-flight generation
  const handleCancelGeneration = () => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }
    setIsGenerating(false);
    setCurrentScreen('config');
  };

  return (
    <div className="astra-app-layout">
      <Navbar
        currentScreen={currentScreen}
        onNavigate={(screen) => setCurrentScreen(screen)}
        canNavigateToReview={examPackage !== null}
      />

      <main className="astra-main-content">
        {currentScreen === 'config' && (
          <ConfigView
            onStartGeneration={handleStartGeneration}
            isGenerating={isGenerating}
          />
        )}

        {currentScreen === 'stepper' && (
          <StepperView
            progress={progress}
            onViewResults={() => setCurrentScreen('review')}
            onCancel={handleCancelGeneration}
          />
        )}

        {currentScreen === 'review' && examPackage && (
          <ReviewView
            examPackage={examPackage}
            onUpdateQuestion={handleUpdateQuestion}
            onRegenerateQuestion={handleRegenerateQuestion}
            onExport={handleExport}
            onBackToConfig={() => setCurrentScreen('config')}
          />
        )}
      </main>

      {/* Global Accessibility / Status Bar */}
      <footer className="astra-footer">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center text-xs text-gray-500 gap-2">
          <div>
            <strong>Dự án ASTRA</strong> — Nhóm Trial & Success · Môn Tư Duy Tính Toán (CSC10014) · HCMUS APCS
          </div>
          <div className="flex items-center gap-4">
            <span>Mô hình kiểm định: Writer-Solver-Critic Loop</span>
            <span className="text-emerald-600 font-semibold flex items-center">
              ● Sẵn sàng (Mock/API Engine Active)
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
