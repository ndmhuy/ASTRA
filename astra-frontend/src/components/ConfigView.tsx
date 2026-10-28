import React, { useState } from 'react';
import type { Subject, ExamType, ExamRequestParams } from '../types/exam';
import { Sparkles, ChevronDown, Check } from 'lucide-react';

interface ConfigViewProps {
  onStartGeneration: (params: ExamRequestParams) => void;
  isGenerating: boolean;
}

const SUBJECTS: Subject[] = [
  'Tổng hợp',
  'Toán Học',
  'Vật Lý',
  'Hóa Học',
  'Sinh Học',
  'Tiếng Anh',
  'Lịch Sử',
  'Địa Lý'
];

interface FormatOption {
  type: ExamType;
  label: string;
  badge: string;
  items: number;
  duration: number;
  note: string;
}

const FORMAT_OPTIONS: FormatOption[] = [
  {
    type: 'CUSTOM',
    label: 'Đề Tự Do (Mặc định)',
    badge: 'Tùy biến',
    items: 40,
    duration: 50,
    note: 'Tự do chọn môn học và mô tả bất kỳ yêu cầu nào'
  },
  {
    type: 'THPT_STANDARD',
    label: 'THPTQG (Tốt Nghiệp THPT)',
    badge: 'Bộ GD&ĐT',
    items: 40,
    duration: 50,
    note: 'Chuẩn cấu trúc 40 câu trắc nghiệm'
  },
  {
    type: 'DGNL_DHQG',
    label: 'DGNL (Đánh Giá Năng Lực)',
    badge: 'ĐHQG',
    items: 30,
    duration: 40,
    note: 'Tư duy logic & giải quyết vấn đề thực tế'
  }
];

export const ConfigView: React.FC<ConfigViewProps> = ({
  onStartGeneration,
  isGenerating
}) => {
  // 1. Exam Format (Default is 'CUSTOM' - Đề tự do)
  const [selectedFormat, setSelectedFormat] = useState<ExamType>('CUSTOM');
  const [isFormatDropdownOpen, setIsFormatDropdownOpen] = useState(false);

  // 2. Subject (Has 'Tổng hợp', auto-switches to 'Tổng hợp' if THPTQG or DGNL)
  const [selectedSubject, setSelectedSubject] = useState<Subject>('Vật Lý');

  // 3. Prompt (Hero Center-Right)
  const [prompt, setPrompt] = useState<string>(
    'Đề ôn tập bám sát chương trình Giáo dục phổ thông mới. Tập trung cân đối các chủ đề Dao động cơ, Sóng cơ và Dòng điện xoay chiều. Đảm bảo các phương án nhiễu phản ánh đúng sai lầm thường gặp của học sinh.'
  );

  // Switch format handler with auto-subject rule
  const handleSelectFormat = (format: FormatOption) => {
    setSelectedFormat(format.type);
    setIsFormatDropdownOpen(false);

    // Rule: When THPTQG or DGNL is chosen, auto-switch subject to "Tổng hợp"
    if (format.type === 'THPT_STANDARD' || format.type === 'DGNL_DHQG') {
      setSelectedSubject('Tổng hợp');
    }
  };

  const currentFormatObj = FORMAT_OPTIONS.find((f) => f.type === selectedFormat) || FORMAT_OPTIONS[0];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStartGeneration({
      subject: selectedSubject,
      grade: 12,
      examType: selectedFormat,
      durationMinutes: currentFormatObj.duration,
      itemCount: currentFormatObj.items,
      prompt,
      uploadedFiles: []
    });
  };

  return (
    <div className="astra-workspace-wrapper">
      {/* Page Header */}
      <div className="text-center mb-6">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
          Hệ Thống Tạo & Thẩm Định Đề Thi ASTRA
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Chọn định dạng và nhập mô tả yêu cầu để bắt đầu luồng tác tử tạo đề.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="astra-main-grid-card">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* ==================================================================
              CỘT TRÁI (~40%): ĐỊNH DẠNG ĐỀ, MÔN HỌC, NÚT TẠO ĐỀ
              ================================================================== */}
          <div className="lg:col-span-5 space-y-6">
            
            {/* 1. Chọn định dạng đề (Ô to, dễ nhìn, click sổ list) */}
            <div>
              <label className="block text-xs font-bold text-gray-800 uppercase tracking-wider mb-2">
                1. Định dạng đề thi:
              </label>

              <div className="relative">
                <button
                  type="button"
                  onClick={() => setIsFormatDropdownOpen(!isFormatDropdownOpen)}
                  className="astra-big-format-selector"
                >
                  <div>
                    <div className="text-xs text-emerald-700 font-bold uppercase tracking-wider">
                      {currentFormatObj.badge}
                    </div>
                    <div className="text-base font-extrabold text-gray-900 mt-0.5">
                      {currentFormatObj.label}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {currentFormatObj.note}
                    </div>
                  </div>
                  <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isFormatDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown List */}
                {isFormatDropdownOpen && (
                  <div className="astra-format-dropdown-menu">
                    {FORMAT_OPTIONS.map((f) => {
                      const isSelected = selectedFormat === f.type;
                      return (
                        <div
                          key={f.type}
                          onClick={() => handleSelectFormat(f)}
                          className={`astra-dropdown-item ${isSelected ? 'selected' : ''}`}
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-sm text-gray-900">{f.label}</span>
                              <span className="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 font-bold">{f.badge}</span>
                            </div>
                            <div className="text-xs text-gray-500 mt-0.5">{f.note}</div>
                          </div>
                          {isSelected && <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* 2. Chọn môn học (Có option 'Tổng hợp', auto 'Tổng hợp' với THPTQG & DGNL) */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-bold text-gray-800 uppercase tracking-wider">
                  2. Chọn môn học:
                </label>
                {(selectedFormat === 'THPT_STANDARD' || selectedFormat === 'DGNL_DHQG') && (
                  <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded">
                    Auto: Tổng hợp
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {SUBJECTS.map((sub) => {
                  const isSelected = selectedSubject === sub;
                  return (
                    <button
                      type="button"
                      key={sub}
                      onClick={() => setSelectedSubject(sub)}
                      className={`astra-subject-pill-btn ${isSelected ? 'selected' : ''}`}
                    >
                      {sub}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 3. Nút Bắt đầu tạo đề thi (Di chuyển lên qua trái gần ngang hàng với ô prompt) */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isGenerating}
                className="astra-hero-action-button"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                <span>{isGenerating ? 'ĐANG TẠO ĐỀ...' : 'BẮT ĐẦU TẠO ĐỀ THI'}</span>
              </button>
              
              <div className="text-center text-xs text-gray-500 mt-2 font-medium">
                Tự động kiểm định đáp án và chuẩn hóa ma trận
              </div>
            </div>

          </div>

          {/* ==================================================================
              CỘT PHẢI (~60%): Ô PROMPT TO Ở TRUNG TÂM - LỆCH PHẢI 1 CHÚT
              ================================================================== */}
          <div className="lg:col-span-7 flex flex-col h-full">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-bold text-gray-800 uppercase tracking-wider">
                3. Nội dung & Yêu cầu đề thi (Prompt chính):
              </label>
              <span className="text-xs text-gray-400">
                Nhập tự do mọi yêu cầu Thầy/Cô mong muốn
              </span>
            </div>

            <div className="flex-1 flex flex-col">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ví dụ: Soạn đề ôn tập học kỳ 1 môn Vật lý lớp 12. Tập trung cân đối các chủ đề Dao động cơ, Sóng cơ và Dòng điện xoay chiều. Đảm bảo các phương án nhiễu phản ánh đúng sai lầm thường gặp của học sinh..."
                className="astra-large-center-prompt"
              />

              {/* Quick suggestion tags below prompt */}
              <div className="flex flex-wrap items-center gap-2 mt-3">
                <span className="text-xs text-gray-500 font-semibold">Gợi ý chèn:</span>
                {[
                  '+ Tăng cường câu hỏi đồ thị thực tế',
                  '+ Bám sát đề minh họa mới nhất',
                  '+ 40% Biết · 30% Hiểu · 20% Vận dụng · 10% VDC'
                ].map((sug, idx) => (
                  <button
                    type="button"
                    key={idx}
                    onClick={() => setPrompt((prev) => `${prev} ${sug.replace('+', '').trim()}.`)}
                    className="astra-tag-chip"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>
          </div>

        </div>
      </form>
    </div>
  );
};
