import React, { useState } from 'react';
import type { Subject, ExamType, ExamRequestParams } from '../types/exam';
import { Sparkles } from 'lucide-react';

interface ConfigViewProps {
  onStartGeneration: (params: ExamRequestParams) => void;
  isGenerating: boolean;
}

const SUBJECTS: Subject[] = [
  'Toán Học',
  'Vật Lý',
  'Hóa Học',
  'Sinh Học',
  'Tiếng Anh',
  'Lịch Sử',
  'Địa Lý'
];

interface ExamOption {
  type: ExamType;
  name: string;
  desc: string;
  items: number;
  duration: number;
  defaultPrompt: string;
}

const EXAM_OPTIONS: ExamOption[] = [
  {
    type: 'THPT_STANDARD',
    name: 'THPT Quốc Gia',
    desc: '40 câu · 50 phút · Chuẩn ma trận Bộ GD&ĐT',
    items: 40,
    duration: 50,
    defaultPrompt: 'Đề thi bám sát cấu trúc đề tham khảo tốt nghiệp THPT mới của Bộ GD&ĐT. Phân bổ cân đối 40 câu trắc nghiệm.'
  },
  {
    type: 'DGNL_DHQG',
    name: 'Đánh Giá Năng Lực',
    desc: '30 câu · 40 phút · ĐHQG TP.HCM / Hà Nội',
    items: 30,
    duration: 40,
    defaultPrompt: 'Đề thi Đánh giá năng lực chú trọng tư duy logic, xử lý số liệu và suy luận thực tế.'
  },
  {
    type: 'CUSTOM',
    name: 'Đề Kiểm Tra Tự Do',
    desc: 'Tùy chỉnh nội dung theo chương trình học',
    items: 25,
    duration: 45,
    defaultPrompt: 'Đề kiểm tra ôn tập học kỳ 1 theo chương trình GDPT mới.'
  }
];

export const ConfigView: React.FC<ConfigViewProps> = ({
  onStartGeneration,
  isGenerating
}) => {
  const [selectedSubject, setSelectedSubject] = useState<Subject>('Vật Lý');
  const [selectedExamType, setSelectedExamType] = useState<ExamType>('THPT_STANDARD');
  const [prompt, setPrompt] = useState<string>(EXAM_OPTIONS[0].defaultPrompt);

  const handleSelectExamOption = (opt: ExamOption) => {
    setSelectedExamType(opt.type);
    setPrompt(opt.defaultPrompt);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const currentOpt = EXAM_OPTIONS.find((o) => o.type === selectedExamType) || EXAM_OPTIONS[0];

    onStartGeneration({
      subject: selectedSubject,
      grade: 12,
      examType: selectedExamType,
      durationMinutes: currentOpt.duration,
      itemCount: currentOpt.items,
      prompt,
      uploadedFiles: []
    });
  };

  return (
    <div className="astra-container">
      {/* Page Title */}
      <div className="astra-title-area">
        <h1>Tạo Đề Thi Mới</h1>
        <p>Chọn môn, chọn định dạng và nhập nội dung đề thi Thầy/Cô mong muốn.</p>
      </div>

      <form onSubmit={handleSubmit} className="astra-form-card">
        {/* Step 1: Subject Selection */}
        <div className="astra-field-group">
          <label className="astra-label">1. Chọn môn học</label>
          <div className="astra-button-row">
            {SUBJECTS.map((sub) => {
              const active = selectedSubject === sub;
              return (
                <button
                  type="button"
                  key={sub}
                  onClick={() => setSelectedSubject(sub)}
                  className={`astra-choice-btn ${active ? 'active' : ''}`}
                >
                  {sub}
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 2: Exam Format (THPTQG / DGNL / Tự do) */}
        <div className="astra-field-group">
          <label className="astra-label">2. Chọn định dạng đề</label>
          <div className="astra-grid-3">
            {EXAM_OPTIONS.map((opt) => {
              const active = selectedExamType === opt.type;
              return (
                <div
                  key={opt.type}
                  onClick={() => handleSelectExamOption(opt)}
                  className={`astra-format-card ${active ? 'active' : ''}`}
                >
                  <div className="astra-format-title">{opt.name}</div>
                  <div className="astra-format-desc">{opt.desc}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step 3: Prompt Textarea */}
        <div className="astra-field-group">
          <label className="astra-label">3. Nội dung & Yêu cầu đề thi (Prompt)</label>
          <textarea
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Nhập yêu cầu đề thi... (Ví dụ: Tập trung ôn tập chương Dao động cơ và Sóng cơ, phân bổ 40% nhận biết, 30% thông hiểu, 30% vận dụng)"
            className="astra-input-textarea"
          />
        </div>

        {/* Big Action Button */}
        <div className="astra-submit-area">
          <button
            type="submit"
            disabled={isGenerating}
            className="astra-big-submit-btn"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            <span>{isGenerating ? 'ĐANG TẠO ĐỀ...' : 'BẮT ĐẦU TẠO ĐỀ THI'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
