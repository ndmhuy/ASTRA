import React, { useState } from 'react';
import type { ExamPackage, QuestionItem } from '../types/exam';
import { MathRenderer } from './MathRenderer';
import { EditQuestionModal } from './EditQuestionModal';
import { ExportModal } from './ExportModal';
import { 
  CheckCircle, 
  AlertCircle, 
  Edit3, 
  Check, 
  RefreshCw,
  Printer,
  ArrowLeft
} from 'lucide-react';

interface ReviewViewProps {
  examPackage: ExamPackage;
  onUpdateQuestion: (question: QuestionItem) => void;
  onRegenerateQuestion: (questionId: number, instruction?: string) => Promise<QuestionItem>;
  onExport: (type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: 'docx' | 'pdf') => void;
  onBackToConfig: () => void;
}

export const ReviewView: React.FC<ReviewViewProps> = ({
  examPackage,
  onUpdateQuestion,
  onRegenerateQuestion,
  onExport,
  onBackToConfig
}) => {
  // Simple filter: All vs Only Flagged
  const [onlyFlagged, setOnlyFlagged] = useState(false);
  
  // Modals
  const [editingQuestion, setEditingQuestion] = useState<QuestionItem | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [repairingId, setRepairingId] = useState<number | null>(null);

  const questions = examPackage.questions;
  const flaggedItems = questions.filter((q) => q.status === 'FLAGGED');
  const flaggedCount = flaggedItems.length;

  const displayQuestions = onlyFlagged ? flaggedItems : questions;

  const handleQuickApprove = (question: QuestionItem) => {
    onUpdateQuestion({
      ...question,
      status: 'VERIFIED',
      auditNotes: 'Thầy/Cô đã kiểm tra và duyệt đạt.'
    });
  };

  const handleRegenerate = async (questionId: number) => {
    setRepairingId(questionId);
    try {
      await onRegenerateQuestion(questionId, 'Tái tạo câu hỏi tương đương, chuẩn mực đáp án.');
    } finally {
      setRepairingId(null);
    }
  };

  return (
    <div className="astra-simple-container">
      {/* Top Navigation Bar: Back & Print */}
      <div className="flex items-center justify-between mb-5">
        <button
          onClick={onBackToConfig}
          className="astra-back-link"
        >
          <ArrowLeft className="w-5 h-5 mr-1.5" />
          <span>Quay lại chỉnh sửa yêu cầu</span>
        </button>

        <button
          onClick={() => setIsExportOpen(true)}
          className="astra-hero-button sm:w-auto px-7 py-3.5 shadow-md flex items-center gap-2"
        >
          <Printer className="w-5 h-5" />
          <span>XUẤT BẢN WORD / IN ĐỀ</span>
        </button>
      </div>

      {/* Paper Header Card */}
      <div className="astra-clean-card mb-8">
        <div className="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-1.5">
          {examPackage.subject} · Lớp {examPackage.grade} · Đề số: {examPackage.examId}
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 leading-snug">
          {examPackage.title}
        </h1>
        <p className="text-base text-gray-600 mt-2">
          Thời gian làm bài: <strong>{examPackage.durationMinutes} phút</strong> · Tổng số: <strong>{questions.length} câu trắc nghiệm</strong>
        </p>

        {/* Friendly Triage Notice (Only if there are flagged items) */}
        {flaggedCount > 0 ? (
          <div className="astra-notice-banner mt-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-amber-600 flex-shrink-0" />
              <div className="text-sm sm:text-base text-amber-900 font-medium">
                Hệ thống phát hiện <strong>{flaggedCount} câu</strong> có thể gây phân vân cho học sinh. Thầy/Cô nên xem qua trước khi in nhé.
              </div>
            </div>

            <button
              onClick={() => setOnlyFlagged(!onlyFlagged)}
              className="astra-toggle-chip"
            >
              {onlyFlagged ? 'Xem lại toàn bộ 40 câu' : `Chỉ xem ${flaggedCount} câu cần lưu ý`}
            </button>
          </div>
        ) : (
          <div className="mt-5 pt-4 border-t border-gray-100 flex items-center gap-2.5 text-sm text-emerald-700 font-semibold">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
            Toàn bộ câu hỏi đều đạt chuẩn kiểm định độc lập và không có xung đột đáp án.
          </div>
        )}
      </div>

      {/* Clean Paper-like Question List */}
      <div className="space-y-6">
        {displayQuestions.map((q) => {
          const isFlagged = q.status === 'FLAGGED';
          const isRepairing = repairingId === q.id;

          return (
            <div
              key={q.id}
              className={`astra-paper-question ${isFlagged ? 'flagged' : ''}`}
            >
              {/* Question Stem */}
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="text-lg text-gray-900 leading-relaxed font-semibold">
                  <span className="text-indigo-900 font-bold mr-2 text-xl">Câu {q.id}:</span>
                  <MathRenderer content={q.stem} />
                </div>

                {/* Subtle Edit button */}
                <button
                  onClick={() => setEditingQuestion(q)}
                  className="astra-subtle-edit-btn"
                  title="Chỉnh sửa câu hỏi này"
                >
                  <Edit3 className="w-4 h-4 mr-1" />
                  <span>Sửa</span>
                </button>
              </div>

              {/* Choices in Clean Layout */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-base text-gray-800 my-4">
                {(['A', 'B', 'C', 'D'] as const).map((k) => {
                  const isCorrect = q.key === k;
                  return (
                    <div
                      key={k}
                      className={`astra-paper-choice ${isCorrect ? 'correct' : ''}`}
                    >
                      <span className="font-extrabold mr-2.5 text-gray-800 text-lg">{k}.</span>
                      <span className="flex-1"><MathRenderer content={q.choices[k]} /></span>
                      {isCorrect && (
                        <span className="ml-auto text-xs font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded">
                          Đáp án đúng
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* If Flagged: Show clear, friendly pedagogical guidance with 2 simple buttons */}
              {isFlagged ? (
                <div className="astra-flagged-box mt-4 p-4 rounded-xl bg-amber-50 border-2 border-amber-200">
                  <div className="text-sm font-bold text-amber-900 mb-1.5 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-amber-600" />
                    Lưu ý sư phạm từ hệ thống:
                  </div>
                  <div className="text-sm text-amber-800 mb-4 leading-relaxed font-medium">
                    {q.auditNotes || 'Phương án nhiễu có thể khiến học sinh nhầm lẫn công thức. Thầy/Cô kiểm tra lại đáp án nhé.'}
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      onClick={() => handleQuickApprove(q)}
                      className="astra-btn-approve"
                    >
                      <Check className="w-4 h-4 mr-1.5" />
                      Tôi đồng ý với câu hỏi này
                    </button>
                    <button
                      onClick={() => handleRegenerate(q.id)}
                      disabled={isRepairing}
                      className="astra-btn-repair"
                    >
                      <RefreshCw className={`w-4 h-4 mr-1.5 ${isRepairing ? 'animate-spin' : ''}`} />
                      {isRepairing ? 'Đang tạo câu mới...' : 'Đổi câu hỏi khác'}
                    </button>
                  </div>
                </div>
              ) : (
                /* Verified Question: Clean, subtle explanation */
                <div className="text-sm text-gray-600 mt-3 pt-3 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <strong className="text-gray-700">Hướng dẫn giải:</strong> <MathRenderer content={q.explanation} />
                  </div>
                  <span className="text-emerald-700 font-semibold text-xs whitespace-nowrap bg-emerald-50 px-2.5 py-1 rounded-full self-start sm:self-auto">
                    ✔ Chuẩn SGK
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Floating Bottom Print Action for easy reaching */}
      <div className="mt-10 text-center">
        <button
          onClick={() => setIsExportOpen(true)}
          className="astra-hero-button sm:w-auto px-10 py-4 shadow-lg inline-flex items-center gap-2 text-lg"
        >
          <Printer className="w-6 h-6" />
          <span>HOÀN TẤT & XUẤT FILE WORD</span>
        </button>
      </div>

      {/* Edit Modal */}
      {editingQuestion && (
        <EditQuestionModal
          question={editingQuestion}
          isOpen={true}
          onClose={() => setEditingQuestion(null)}
          onSave={(updated) => {
            onUpdateQuestion(updated);
            setEditingQuestion(null);
          }}
        />
      )}

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        onExport={onExport}
      />
    </div>
  );
};
