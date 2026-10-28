import React, { useState } from 'react';
import type { Subject, ExamType, ExamRequestParams } from '../types/exam';
import { 
  Sparkles, 
  ChevronDown, 
  ChevronUp, 
  UploadCloud, 
  HelpCircle
} from 'lucide-react';

interface ConfigViewProps {
  onStartGeneration: (params: ExamRequestParams) => void;
  isGenerating: boolean;
}

const COMMON_SUBJECTS: Subject[] = [
  'Vật Lý',
  'Toán Học',
  'Hóa Học',
  'Sinh Học',
  'Tiếng Anh',
  'Lịch Sử',
  'Địa Lý'
];

export const ConfigView: React.FC<ConfigViewProps> = ({
  onStartGeneration,
  isGenerating
}) => {
  // Simple core state
  const [selectedSubject, setSelectedSubject] = useState<Subject>('Vật Lý');
  const [prompt, setPrompt] = useState<string>(
    'Đề ôn tập học kỳ bám sát cấu trúc đề thi Tốt nghiệp THPT mới. Cân đối kiến thức Dao động cơ, Sóng cơ và Dòng điện xoay chiều.'
  );

  // Hidden advanced options (collapsed by default)
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [grade, setGrade] = useState<number>(12);
  const examType: ExamType = 'THPT_STANDARD';
  const [itemCount, setItemCount] = useState<number>(40);
  const [durationMinutes, setDurationMinutes] = useState<number>(50);
  const [uploadedFiles] = useState<string[]>(['Phan_phoi_chuong_trinh_chuan.pdf']);

  const quickSuggestions = [
    'Bám sát cấu trúc đề tham khảo của Bộ GD&ĐT',
    'Tăng cường câu hỏi đồ thị và vận dụng thực tế',
    'Ôn tập trọng tâm chương 1 và chương 2'
  ];

  const handleApplySuggestion = (text: string) => {
    if (prompt.includes(text)) return;
    setPrompt((prev) => (prev ? `${prev}. ${text}` : text));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStartGeneration({
      subject: selectedSubject,
      grade,
      examType,
      durationMinutes,
      itemCount,
      prompt,
      uploadedFiles
    });
  };

  return (
    <div className="astra-simple-container">
      {/* Friendly Welcome Header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
          Chào Thầy/Cô, hôm nay mình muốn soạn đề thi gì?
        </h1>
        <p className="text-base text-gray-600 mt-2 max-w-xl mx-auto">
          Chỉ cần chọn môn và ghi chú nội dung mong muốn. ASTRA sẽ tự động đối chiếu SGK và thẩm định chính xác từng câu hỏi.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="astra-clean-card">
        {/* Row 1: Simple Subject Choice */}
        <div className="mb-6">
          <label className="block text-sm font-bold text-gray-800 uppercase tracking-wider mb-2.5">
            1. Chọn Môn Thi:
          </label>
          <div className="flex flex-wrap gap-2.5">
            {COMMON_SUBJECTS.map((sub) => {
              const isSelected = selectedSubject === sub;
              return (
                <button
                  type="button"
                  key={sub}
                  onClick={() => setSelectedSubject(sub)}
                  className={`astra-simple-subject-btn ${isSelected ? 'active' : ''}`}
                >
                  {sub}
                </button>
              );
            })}
          </div>
        </div>

        {/* Row 2: One-shot Prompt Area */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-bold text-gray-800 uppercase tracking-wider">
              2. Nội Dung & Lưu Ý Của Thầy/Cô:
            </label>
            <span className="text-xs text-gray-500 flex items-center">
              <HelpCircle className="w-3.5 h-3.5 mr-1 text-gray-400" />
              Có thể để nguyên nếu dùng đề chuẩn
            </span>
          </div>

          <textarea
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ví dụ: Đề ôn tập học kỳ 1, tập trung nhiều câu hỏi đồ thị sóng cơ, 40 câu hỏi..."
            className="astra-large-textarea"
          />

          {/* Quick Click Suggestions to reduce typing */}
          <div className="flex flex-wrap items-center gap-2 mt-2.5">
            <span className="text-xs text-gray-500 font-medium">Gợi ý nhanh:</span>
            {quickSuggestions.map((sug, idx) => (
              <button
                type="button"
                key={idx}
                onClick={() => handleApplySuggestion(sug)}
                className="astra-quick-chip"
              >
                + {sug}
              </button>
            ))}
          </div>
        </div>

        {/* Collapsible Advanced Settings (Default Closed) */}
        <div className="border-t border-gray-100 pt-4 mb-6">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs font-bold text-gray-600 hover:text-indigo-600 flex items-center gap-1.5 py-1"
          >
            {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            <span>{showAdvanced ? 'Thu gọn tùy chỉnh nâng cao' : 'Tùy chỉnh thêm (Số câu, thời gian, tải tệp ma trận...)'}</span>
          </button>

          {showAdvanced && (
            <div className="astra-advanced-panel mt-3 p-4 bg-gray-50 rounded-xl space-y-4 text-xs text-gray-700">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold mb-1">Khối lớp:</label>
                  <select
                    value={grade}
                    onChange={(e) => setGrade(Number(e.target.value))}
                    className="astra-select-simple"
                  >
                    <option value={12}>Lớp 12 (Chuẩn Tốt nghiệp)</option>
                    <option value={11}>Lớp 11</option>
                    <option value={10}>Lớp 10</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold mb-1">Số lượng câu hỏi:</label>
                  <input
                    type="number"
                    min="10"
                    max="60"
                    value={itemCount}
                    onChange={(e) => setItemCount(Number(e.target.value))}
                    className="astra-input-simple"
                  />
                </div>

                <div>
                  <label className="block font-semibold mb-1">Thời gian làm bài:</label>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      min="15"
                      max="120"
                      value={durationMinutes}
                      onChange={(e) => setDurationMinutes(Number(e.target.value))}
                      className="astra-input-simple"
                    />
                    <span className="text-gray-500">phút</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block font-semibold mb-1">Tài liệu cơ sở đính kèm:</label>
                <div className="flex items-center gap-2 p-2.5 bg-white border border-dashed border-gray-300 rounded-lg">
                  <UploadCloud className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-500">Đã nạp: {uploadedFiles.join(', ')}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Big, Clear, High-Contrast Action Button */}
        <div>
          <button
            type="submit"
            disabled={isGenerating}
            className="astra-hero-button"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            <span>{isGenerating ? 'HỆ THỐNG ĐANG XỬ LÝ...' : 'BẮT ĐẦU TẠO ĐỀ THI'}</span>
          </button>
          
          <div className="text-center text-xs text-gray-500 mt-2.5">
            Mặc định: <strong>Chuẩn 40 câu trắc nghiệm</strong> · Tự động đối chiếu SGK mới và thẩm định lời giải.
          </div>
        </div>
      </form>
    </div>
  );
};
