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
  ArrowLeft,
  Filter
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

  const scrollToQuestion = (id: number) => {
    const el = document.getElementById(`question-card-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className="astra-desktop-workspace">
      {/* Top Bar Navigation */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <button
          onClick={onBackToConfig}
          className="astra-back-link"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          <span>Quay lại trang tạo đề</span>
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsExportOpen(true)}
            className="astra-btn-baby-green px-6 py-3 shadow-md flex items-center gap-2"
          >
            <Printer className="w-5 h-5" />
            <span>XUẤT BẢN WORD / IN ĐỀ</span>
          </button>
        </div>
      </div>

      {/* Desktop Horizontal 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7 items-start">
        
        {/* ====================================================================
            LEFT SIDEBAR: BẢNG ĐIỀU HƯỚNG CÂU HỎI & THỐNG KÊ (STICKY)
            ==================================================================== */}
        <div className="lg:col-span-4 sticky top-24 space-y-4">
          <div className="astra-panel p-5">
            <div className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-1">
              {examPackage.subject} · Lớp {examPackage.grade}
            </div>
            <h2 className="text-lg font-extrabold text-gray-900 leading-snug">
              {examPackage.title}
            </h2>
            <div className="text-xs text-gray-500 mt-1 mb-4">
              Thời gian: <strong>{examPackage.durationMinutes} phút</strong> · Mã: {examPackage.examId}
            </div>

            {/* Thống kê nhanh */}
            <div className="grid grid-cols-2 gap-2 pb-4 mb-4 border-b border-gray-100">
              <div className="p-2.5 bg-emerald-50 rounded-xl text-center">
                <div className="text-xs text-emerald-700 font-semibold">Đã kiểm duyệt</div>
                <div className="text-lg font-extrabold text-emerald-800">
                  {questions.length - flaggedCount} / {questions.length}
                </div>
              </div>
              <div className={`p-2.5 rounded-xl text-center ${flaggedCount > 0 ? 'bg-amber-50 text-amber-800' : 'bg-gray-50 text-gray-600'}`}>
                <div className="text-xs font-semibold">Cần lưu ý</div>
                <div className="text-lg font-extrabold">
                  {flaggedCount} câu {flaggedCount > 0 && '⚠️'}
                </div>
              </div>
            </div>

            {/* Lọc câu hỏi */}
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                Mục lục câu hỏi ({questions.length} câu):
              </span>
              {flaggedCount > 0 && (
                <button
                  onClick={() => setOnlyFlagged(!onlyFlagged)}
                  className={`text-xs font-bold px-2.5 py-1 rounded-full border transition-all ${onlyFlagged ? 'bg-amber-500 text-white border-amber-500' : 'bg-amber-50 text-amber-800 border-amber-200'}`}
                >
                  <Filter className="w-3 h-3 inline mr-1" />
                  {onlyFlagged ? 'Hiện tất cả' : 'Chỉ xem cờ'}
                </button>
              )}
            </div>

            {/* Ma trận các ô số câu để nhảy nhanh */}
            <div className="grid grid-cols-5 gap-2 max-h-60 overflow-y-auto p-1">
              {questions.map((q) => {
                const isFlagged = q.status === 'FLAGGED';
                return (
                  <button
                    key={q.id}
                    onClick={() => scrollToQuestion(q.id)}
                    className={`astra-nav-number-cell ${isFlagged ? 'flagged' : 'verified'}`}
                    title={`Câu ${q.id}: ${q.topic} - ${isFlagged ? 'Cần kiểm tra' : 'Đã duyệt'}`}
                  >
                    <span>{q.id}</span>
                    {isFlagged ? (
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 ml-1"></span>
                    ) : (
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 ml-1"></span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="mt-5 pt-3 border-t border-gray-100">
              <button
                onClick={() => setIsExportOpen(true)}
                className="w-full astra-btn-baby-green py-2.5 text-sm"
              >
                <Printer className="w-4 h-4 mr-1.5" />
                <span>In đề ngay (.doc / .pdf)</span>
              </button>
            </div>
          </div>
        </div>

        {/* ====================================================================
            RIGHT MAIN AREA: NỘI DUNG ĐỀ THI DẠNG TRANG IN CHUẨN
            ==================================================================== */}
        <div className="lg:col-span-8 space-y-5">
          {flaggedCount > 0 && !onlyFlagged && (
            <div className="p-4 bg-amber-50 border-2 border-amber-200 rounded-2xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <div className="text-sm text-amber-900 font-medium">
                  Có <strong>{flaggedCount} câu</strong> được đánh dấu cần xem xét (đã tô viền vàng bên dưới).
                </div>
              </div>
              <button
                onClick={() => setOnlyFlagged(true)}
                className="text-xs font-bold text-amber-800 bg-white border border-amber-300 px-3 py-1.5 rounded-lg hover:bg-amber-100"
              >
                Lọc ra để xem
              </button>
            </div>
          )}

          {displayQuestions.map((q) => {
            const isFlagged = q.status === 'FLAGGED';
            const isRepairing = repairingId === q.id;

            return (
              <div
                key={q.id}
                id={`question-card-${q.id}`}
                className={`astra-paper-question ${isFlagged ? 'flagged' : ''}`}
              >
                {/* Header câu hỏi */}
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="text-base text-gray-900 leading-relaxed font-semibold">
                    <span className="text-emerald-900 font-extrabold mr-2 text-lg">Câu {q.id}:</span>
                    <MathRenderer content={q.stem} />
                  </div>

                  <button
                    onClick={() => setEditingQuestion(q)}
                    className="astra-subtle-edit-btn"
                    title="Chỉnh sửa câu hỏi này"
                  >
                    <Edit3 className="w-3.5 h-3.5 mr-1" />
                    <span>Sửa</span>
                  </button>
                </div>

                {/* 4 phương án A, B, C, D */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-gray-800 my-3">
                  {(['A', 'B', 'C', 'D'] as const).map((k) => {
                    const isCorrect = q.key === k;
                    return (
                      <div
                        key={k}
                        className={`astra-paper-choice ${isCorrect ? 'correct' : ''}`}
                      >
                        <span className="font-extrabold mr-2 text-gray-800 text-base">{k}.</span>
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

                {/* Khung cảnh báo nếu có cờ */}
                {isFlagged ? (
                  <div className="astra-flagged-box mt-3.5 p-4 rounded-xl bg-amber-50 border-2 border-amber-200">
                    <div className="text-xs font-bold text-amber-900 mb-1 flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4 text-amber-600" />
                      Lưu ý từ hệ thống thẩm định:
                    </div>
                    <div className="text-xs sm:text-sm text-amber-800 mb-3 leading-relaxed font-medium">
                      {q.auditNotes || 'Phương án nhiễu có thể gây phân vân cho học sinh. Thầy/Cô kiểm tra lại nhé.'}
                    </div>

                    <div className="flex flex-wrap items-center gap-2.5">
                      <button
                        onClick={() => handleQuickApprove(q)}
                        className="astra-btn-approve text-xs py-2 px-3.5"
                      >
                        <Check className="w-3.5 h-3.5 mr-1" />
                        Tôi đồng ý với câu hỏi này
                      </button>
                      <button
                        onClick={() => handleRegenerate(q.id)}
                        disabled={isRepairing}
                        className="astra-btn-repair text-xs py-2 px-3.5"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 mr-1 ${isRepairing ? 'animate-spin' : ''}`} />
                        {isRepairing ? 'Đang tạo câu mới...' : 'Đổi câu hỏi khác'}
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Câu đã đạt: Hướng dẫn giải nhẹ nhàng */
                  <div className="text-xs text-gray-600 mt-2.5 pt-2.5 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <strong className="text-gray-700">Hướng dẫn giải:</strong> <MathRenderer content={q.explanation} />
                    </div>
                    <span className="text-emerald-700 font-semibold text-xs whitespace-nowrap bg-emerald-50 px-2 py-0.5 rounded-full">
                      ✔ Chuẩn SGK
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

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
