import React, { useState } from 'react';
import type { QuestionItem } from '../types/exam';
import { MathRenderer } from './MathRenderer';
import { X, Check, Eye } from 'lucide-react';

interface EditQuestionModalProps {
  question: QuestionItem;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updated: QuestionItem) => void;
}

export const EditQuestionModal: React.FC<EditQuestionModalProps> = ({
  question,
  isOpen,
  onClose,
  onSave
}) => {
  const [stem, setStem] = useState(question.stem);
  const [choices, setChoices] = useState({ ...question.choices });
  const [key, setKey] = useState(question.key);
  const [explanation, setExplanation] = useState(question.explanation);
  const [showPreview, setShowPreview] = useState(false);

  if (!isOpen) return null;

  const handleChoiceChange = (k: 'A' | 'B' | 'C' | 'D', value: string) => {
    setChoices((prev) => ({ ...prev, [k]: value }));
  };

  const handleSave = () => {
    onSave({
      ...question,
      stem,
      choices,
      key,
      explanation,
      status: 'VERIFIED', // Teacher manual review marks it verified
      auditNotes: `Giáo viên đã trực tiếp chỉnh sửa và phê duyệt lúc ${new Date().toLocaleTimeString('vi-VN')}.`
    });
    onClose();
  };

  return (
    <div className="astra-modal-backdrop">
      <div className="astra-modal-card">
        {/* Header */}
        <div className="astra-modal-header">
          <div>
            <h3 className="text-base font-bold text-gray-900">
              Chỉnh sửa Câu #{question.id} ({question.topic})
            </h3>
            <p className="text-xs text-gray-500">
              Mức độ: {question.level} · Can thiệp trực tiếp bởi Giáo viên
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="astra-modal-body space-y-4">
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="text-xs font-semibold text-indigo-600 flex items-center hover:underline"
            >
              <Eye className="w-3.5 h-3.5 mr-1" />
              {showPreview ? 'Ẩn xem trước công thức' : 'Bật xem trước công thức (KaTeX)'}
            </button>
          </div>

          {/* Question Stem */}
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">
              Nội dung câu hỏi (hỗ trợ LaTeX kẹp giữa dấu $...$):
            </label>
            <textarea
              rows={3}
              value={stem}
              onChange={(e) => setStem(e.target.value)}
              className="astra-textarea font-mono text-sm"
            />
            {showPreview && (
              <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-sm text-gray-800">
                <span className="font-semibold text-xs text-gray-500 block mb-1">Hiển thị trước:</span>
                <MathRenderer content={stem} />
              </div>
            )}
          </div>

          {/* Choices A, B, C, D */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(['A', 'B', 'C', 'D'] as const).map((k) => (
              <div key={k} className="astra-choice-edit-box">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-gray-700">Phương án {k}:</span>
                  <label className="text-xs flex items-center text-gray-600 cursor-pointer">
                    <input
                      type="radio"
                      name="correctKey"
                      checked={key === k}
                      onChange={() => setKey(k)}
                      className="mr-1 text-indigo-600"
                    />
                    Đặt làm đáp án đúng
                  </label>
                </div>
                <input
                  type="text"
                  value={choices[k]}
                  onChange={(e) => handleChoiceChange(k, e.target.value)}
                  className="astra-text-input text-xs font-mono"
                />
                {showPreview && (
                  <div className="text-xs text-gray-700 mt-1 pl-1">
                    <MathRenderer content={choices[k]} />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Explanation */}
          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">
              Lời giải chi tiết & Barem:
            </label>
            <textarea
              rows={2}
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              className="astra-textarea text-xs"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="astra-modal-footer">
          <button onClick={onClose} className="astra-secondary-btn">
            Hủy bỏ
          </button>
          <button onClick={handleSave} className="astra-primary-cta px-5">
            <Check className="w-4 h-4 mr-1.5" />
            Lưu thay đổi & Xác thực
          </button>
        </div>
      </div>
    </div>
  );
};
