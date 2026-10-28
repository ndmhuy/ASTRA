import React, { useState } from 'react';
import type { Subject, ExamType, ExamRequestParams } from '../types/exam';
import { 
  Sparkles, 
  ChevronDown, 
  ChevronUp, 
  UploadCloud, 
  FileText,
  HelpCircle,
  Zap,
  CheckCircle2
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

interface QuickPreset {
  id: ExamType;
  label: string;
  badge: string;
  items: number;
  duration: number;
  promptTemplate: string;
}

const PRESETS: QuickPreset[] = [
  {
    id: 'THPT_STANDARD',
    label: 'Chuẩn THPT Quốc Gia',
    badge: 'Bộ GD&ĐT',
    items: 40,
    duration: 50,
    promptTemplate: 'Đề thi chuẩn Tốt nghiệp THPT bám sát cấu trúc đề tham khảo của Bộ GD&ĐT. Phân bổ cân đối theo ma trận 40 câu trắc nghiệm.'
  },
  {
    id: 'DGNL_DHQG',
    label: 'ĐGNL ĐHQG',
    badge: 'Tư duy logic',
    items: 30,
    duration: 40,
    promptTemplate: 'Đề thi Đánh giá năng lực tích hợp, chú trọng tư duy logic, phân tích số liệu thực tiễn và đọc hiểu biểu đồ.'
  },
  {
    id: 'MID_TERM',
    label: 'Đề Giữa Kỳ / 1 Tiết',
    badge: 'Theo phân phối',
    items: 25,
    duration: 45,
    promptTemplate: 'Đề kiểm tra giữa kỳ tập trung các nội dung kiến thức trọng tâm của học kỳ 1 theo chương trình GDPT mới.'
  }
];

export const ConfigView: React.FC<ConfigViewProps> = ({
  onStartGeneration,
  isGenerating
}) => {
  // Core state - Prompt is the primary driver
  const [selectedSubject, setSelectedSubject] = useState<Subject>('Vật Lý');
  const [prompt, setPrompt] = useState<string>(
    'Đề ôn tập bám sát chương trình Giáo dục phổ thông mới. Tập trung cân đối các chủ đề Dao động cơ, Sóng cơ, Dòng điện xoay chiều. Đảm bảo các phương án nhiễu phản ánh đúng sai lầm thường gặp của học sinh.'
  );

  // Quick preset state
  const [activePreset, setActivePreset] = useState<ExamType>('THPT_STANDARD');

  // Secondary fine-tuning options
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [grade, setGrade] = useState<number>(12);
  const [itemCount, setItemCount] = useState<number>(40);
  const [durationMinutes, setDurationMinutes] = useState<number>(50);
  const [uploadedFiles] = useState<string[]>(['Phan_phoi_chuong_trinh_chuan.pdf']);

  // Handle Quick Preset Selection
  const handleApplyPreset = (preset: QuickPreset) => {
    setActivePreset(preset.id);
    setItemCount(preset.items);
    setDurationMinutes(preset.duration);
    setPrompt(preset.promptTemplate);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStartGeneration({
      subject: selectedSubject,
      grade,
      examType: activePreset,
      durationMinutes,
      itemCount,
      prompt,
      uploadedFiles
    });
  };

  return (
    <div className="astra-workspace-container">
      {/* Friendly Header */}
      <div className="text-center mb-7">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
          Soạn Đề Thi Bằng Trợ Lý Trí Tuệ Nhân Tạo
        </h1>
        <p className="text-sm sm:text-base text-gray-600 mt-2 max-w-2xl mx-auto">
          Mô tả nội dung đề thi Thầy/Cô mong muốn bằng câu lệnh thông thường. Hệ thống sẽ tự động đối chiếu SGK, phân bổ ma trận và kiểm duyệt đáp án độc lập.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="astra-main-form-card">
        
        {/* ==================================================================
            QUICK PRESET BOX: Gói gọn trong 1 box chuyên dụng, không lấn lướt
            ================================================================== */}
        <div className="astra-quick-preset-box mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2.5 border-b border-emerald-100">
            <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-emerald-600 fill-emerald-600" />
              Chọn nhanh mẫu đề chuẩn (Tự động điền cấu hình):
            </span>
            <span className="text-xs text-gray-400 italic">
              Có thể điều chỉnh lại nội dung prompt bên dưới
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
            {PRESETS.map((p) => {
              const isSelected = activePreset === p.id;
              return (
                <button
                  type="button"
                  key={p.id}
                  onClick={() => handleApplyPreset(p)}
                  className={`astra-preset-pill-btn ${isSelected ? 'selected' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-gray-900">{p.label}</span>
                    <span className="astra-preset-badge">{p.badge}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 flex items-center justify-between">
                    <span>{p.items} câu hỏi · {p.duration} phút</span>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-600 inline" />}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* ==================================================================
            CORE SECTION 1: CHỌN MÔN THI
            ================================================================== */}
        <div className="mb-6">
          <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2.5">
            1. Chọn môn học:
          </label>
          <div className="flex flex-wrap gap-2">
            {COMMON_SUBJECTS.map((sub) => {
              const isSelected = selectedSubject === sub;
              return (
                <button
                  type="button"
                  key={sub}
                  onClick={() => setSelectedSubject(sub)}
                  className={`astra-subject-btn ${isSelected ? 'active' : ''}`}
                >
                  {sub}
                </button>
              );
            })}
          </div>
        </div>

        {/* ==================================================================
            CORE SECTION 2: TÍNH NĂNG TẠO ĐỀ TỪ PROMPT (HERO CENTERPIECE)
            ================================================================== */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-bold text-gray-800 uppercase tracking-wider">
              2. Mô tả yêu cầu tạo đề (Prompt chính):
            </label>
            <span className="text-xs text-gray-500 flex items-center">
              <HelpCircle className="w-3.5 h-3.5 mr-1 text-gray-400" />
              Ghi rõ chuyên đề, số câu hoặc dạng bài mong muốn
            </span>
          </div>

          <textarea
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ví dụ: Soạn đề ôn tập học kỳ môn Vật lý lớp 12. Tập trung vào dao động cơ và sóng cơ. Cho 5 câu vận dụng cao về đồ thị dao động, tránh các câu hỏi tính toán mẹo vặt quá phức tạp..."
            className="astra-hero-textarea"
          />

          <div className="flex flex-wrap items-center gap-2 mt-2.5">
            <span className="text-xs text-gray-500 font-medium">Chèn nhanh:</span>
            {[
              '+ Thêm 5 câu đồ thị thực tế',
              '+ Bám sát đề minh họa mới nhất',
              '+ Cân đối 4 mức độ nhận thức Bloom'
            ].map((chip, idx) => (
              <button
                type="button"
                key={idx}
                onClick={() => setPrompt((prev) => `${prev} ${chip.replace('+', '').trim()}.`)}
                className="astra-prompt-quick-chip"
              >
                {chip}
              </button>
            ))}
          </div>
        </div>

        {/* ==================================================================
            COLLAPSIBLE ADVANCED SETTINGS: Rút gọn ngăn nắp, không chồng lấn
            ================================================================== */}
        <div className="border-t border-gray-100 pt-4 mb-7">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs font-bold text-gray-600 hover:text-emerald-700 flex items-center gap-1.5 py-1"
          >
            {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            <span>{showAdvanced ? 'Thu gọn thông số kỹ thuật' : 'Tùy chỉnh thông số chi tiết (Khối lớp, thời gian, file tài liệu...)'}</span>
          </button>

          {showAdvanced && (
            <div className="astra-advanced-box mt-3 p-4 bg-gray-50 rounded-xl space-y-3.5 text-xs text-gray-700">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold mb-1">Khối lớp:</label>
                  <select
                    value={grade}
                    onChange={(e) => setGrade(Number(e.target.value))}
                    className="astra-clean-input"
                  >
                    <option value={12}>Lớp 12</option>
                    <option value={11}>Lớp 11</option>
                    <option value={10}>Lớp 10</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold mb-1">Tổng số câu hỏi:</label>
                  <input
                    type="number"
                    min="10"
                    max="60"
                    value={itemCount}
                    onChange={(e) => setItemCount(Number(e.target.value))}
                    className="astra-clean-input"
                  />
                </div>

                <div>
                  <label className="block font-semibold mb-1">Thời gian làm bài:</label>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      min="15"
                      max="120"
                      value={durationMinutes}
                      onChange={(e) => setDurationMinutes(Number(e.target.value))}
                      className="astra-clean-input"
                    />
                    <span className="text-gray-500">phút</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block font-semibold mb-1">Tài liệu tham khảo đính kèm (RAG):</label>
                <div className="p-2.5 bg-white border border-dashed border-gray-300 rounded-lg flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-emerald-600" />
                    <span>{uploadedFiles[0] || 'Chưa tải file'}</span>
                  </div>
                  <UploadCloud className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ==================================================================
            PRIMARY CALL TO ACTION BUTTON
            ================================================================== */}
        <div>
          <button
            type="submit"
            disabled={isGenerating}
            className="astra-primary-generate-btn"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            <span>{isGenerating ? 'HỆ THỐNG ĐANG TẠO VÀ KIỂM ĐỊNH...' : `BẮT ĐẦU TẠO ĐỀ ${selectedSubject.toUpperCase()}`}</span>
          </button>
          
          <div className="text-center text-xs text-gray-500 mt-2.5">
            Tác tử sẽ tự động phân rã yêu cầu, tra cứu SGK và kiểm tra đáp án độc lập trước khi gửi Thầy/Cô.
          </div>
        </div>

      </form>
    </div>
  );
};
