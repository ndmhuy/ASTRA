import React, { useState } from 'react';
import type { ExamPackage, QuestionItem } from '../types/exam';
import { MathRenderer } from './MathRenderer';
import { EditQuestionModal } from './EditQuestionModal';
import { ExportModal } from './ExportModal';
import { 
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
  const [filterMode, setFilterMode] = useState<'ALL' | 'FLAGGED'>('ALL');
  const [editingQuestion, setEditingQuestion] = useState<QuestionItem | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [repairingId, setRepairingId] = useState<number | null>(null);

  const questions = examPackage.questions;
  const flaggedItems = questions.filter((q) => q.status === 'FLAGGED');
  const flaggedCount = flaggedItems.length;

  const displayQuestions = filterMode === 'FLAGGED' ? flaggedItems : questions;

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
    <div className="astra-container">
      {/* Top Action Header */}
      <div className="astra-review-top-bar">
        <button onClick={onBackToConfig} className="astra-simple-back-btn">
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          <span>Quay lại</span>
        </button>

        <button
          onClick={() => setIsExportOpen(true)}
          className="astra-big-print-btn"
        >
          <Printer className="w-5 h-5 mr-2" />
          <span>XUẤT BẢN WORD / IN ĐỀ</span>
        </button>
      </div>

      {/* Exam Header Card */}
      <div className="astra-exam-header-card">
        <div className="astra-exam-meta">
          Môn {examPackage.subject} · Lớp {examPackage.grade} · Thời gian: {examPackage.durationMinutes} phút
        </div>
        <h1 className="astra-exam-title">{examPackage.title}</h1>
        <p className="astra-exam-desc">
          Tổng số: <strong>{questions.length} câu trắc nghiệm</strong> · Đã kiểm duyệt: <strong>{questions.length - flaggedCount}/{questions.length} câu</strong>
        </p>

        {/* Filter Tabs */}
        <div className="astra-filter-pills">
          <button
            onClick={() => setFilterMode('ALL')}
            className={`astra-filter-pill ${filterMode === 'ALL' ? 'active' : ''}`}
          >
            Tất cả ({questions.length} câu)
          </button>
          <button
            onClick={() => setFilterMode('FLAGGED')}
            className={`astra-filter-pill ${filterMode === 'FLAGGED' ? 'active' : ''}`}
          >
            Câu cần lưu ý ({flaggedCount} câu) {flaggedCount > 0 && '⚠️'}
          </button>
        </div>
      </div>

      {/* Question List */}
      <div className="astra-questions-list">
        {displayQuestions.map((q) => {
          const isFlagged = q.status === 'FLAGGED';
          const isRepairing = repairingId === q.id;

          return (
            <div
              key={q.id}
              className={`astra-question-box ${isFlagged ? 'flagged' : ''}`}
            >
              {/* Question Stem */}
              <div className="astra-question-header">
                <div className="astra-question-text">
                  <span className="astra-q-label">Câu {q.id}:</span>
                  <MathRenderer content={q.stem} />
                </div>
                <button
                  onClick={() => setEditingQuestion(q)}
                  className="astra-edit-icon-btn"
                  title="Chỉnh sửa câu này"
                >
                  <Edit3 className="w-4 h-4 mr-1" />
                  <span>Sửa</span>
                </button>
              </div>

              {/* Choices (A, B, C, D) */}
              <div className="astra-choices-grid">
                {(['A', 'B', 'C', 'D'] as const).map((k) => {
                  const isCorrect = q.key === k;
                  return (
                    <div
                      key={k}
                      className={`astra-choice-item ${isCorrect ? 'correct' : ''}`}
                    >
                      <span className="astra-choice-key">{k}.</span>
                      <span className="flex-1">
                        <MathRenderer content={q.choices[k]} />
                      </span>
                      {isCorrect && (
                        <span className="astra-correct-tag">Đáp án đúng</span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Flagged Alert Box */}
              {isFlagged ? (
                <div className="astra-flagged-callout">
                  <div className="flex items-center gap-2 font-bold text-amber-900 mb-1">
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                    <span>Lưu ý từ hệ thống kiểm định:</span>
                  </div>
                  <p className="text-sm text-amber-800 mb-3">
                    {q.auditNotes || 'Phương án nhiễu có thể gây nhầm lẫn. Thầy/Cô kiểm tra lại trước khi in nhé.'}
                  </p>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleQuickApprove(q)}
                      className="astra-approve-btn"
                    >
                      <Check className="w-4 h-4 mr-1" />
                      Tôi đồng ý với câu này
                    </button>
                    <button
                      onClick={() => handleRegenerate(q.id)}
                      disabled={isRepairing}
                      className="astra-repair-btn"
                    >
                      <RefreshCw className={`w-4 h-4 mr-1 ${isRepairing ? 'animate-spin' : ''}`} />
                      {isRepairing ? 'Đang tạo lại...' : 'Đổi câu khác'}
                    </button>
                  </div>
                </div>
              ) : (
                /* Verified Question: Clean subtle explanation */
                <div className="astra-solution-footer">
                  <div>
                    <strong>Hướng dẫn giải:</strong> <MathRenderer content={q.explanation} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
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
