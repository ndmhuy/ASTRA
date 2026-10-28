import React, { useState } from 'react';
import type { Subject, ExamType, ExamRequestParams } from '../types/exam';
import { 
  Zap, 
  Sparkles, 
  UploadCloud, 
  FileText,
  Sliders,
  CheckCircle2,
  GraduationCap
} from 'lucide-react';

interface ConfigViewProps {
  onStartGeneration: (params: ExamRequestParams) => void;
  isGenerating: boolean;
}

const SUBJECT_LIST: Subject[] = [
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
  // Shared state
  const [selectedSubject, setSelectedSubject] = useState<Subject>('Vật Lý');
  const [examType, setExamType] = useState<ExamType>('THPT_STANDARD');
  const [grade, setGrade] = useState<number>(12);
  const [itemCount, setItemCount] = useState<number>(40);
  const [durationMinutes, setDurationMinutes] = useState<number>(50);

  // Custom prompt state for Right Panel (Tự soạn / Điều chỉnh thêm)
  const [prompt, setPrompt] = useState<string>(
    'Tập trung kiến thức học kỳ 1 theo chương trình GDPT mới. Đảm bảo câu hỏi có số liệu thực tế, tránh các đáp án rập khuôn.'
  );
  const [uploadedFiles] = useState<string[]>(['Phan_phoi_chuong_trinh_Vatly_12.pdf']);

  const handleSelectExamType = (type: ExamType) => {
    setExamType(type);
    if (type === 'THPT_STANDARD') {
      setItemCount(40);
      setDurationMinutes(50);
      setGrade(12);
    } else if (type === 'DGNL_DHQG') {
      setItemCount(30);
      setDurationMinutes(40);
      setGrade(12);
    } else if (type === 'MID_TERM') {
      setItemCount(25);
      setDurationMinutes(45);
    }
  };

  // 1-Click Fast Generation Handler (Left Panel)
  const handleFastGenerate = () => {
    onStartGeneration({
      subject: selectedSubject,
      grade,
      examType,
      durationMinutes,
      itemCount,
      prompt: `Đề chuẩn ${examType === 'DGNL_DHQG' ? 'ĐGNL ĐHQG' : 'Tốt Nghiệp THPT'} bám sát chuẩn ma trận Bộ GD&ĐT và bộ SGK mới. 100% trắc nghiệm.`,
      uploadedFiles: []
    });
  };

  // Custom Generation Handler (Right Panel)
  const handleCustomGenerate = (e: React.FormEvent) => {
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
    <div className="astra-desktop-workspace">
      {/* Top Banner Greeting - From Handwritten Sketch "Hi Anh ?" */}
      <div className="astra-workspace-header">
        <div>
          <div className="astra-greeting-pill">
            <span className="astra-pulse-dot"></span>
            Không gian làm việc giáo viên
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-1.5">
            Chào Thầy Anh! Thầy muốn tạo đề theo phương thức nào?
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Chọn <strong>Tạo đề nhanh</strong> theo chuẩn có sẵn hoặc <strong>Tự soạn & điều chỉnh</strong> với chatbot hỗ trợ.
          </p>
        </div>
      </div>

      {/* 2-COLUMN DESKTOP SPLIT LAYOUT (Directly matching paper draft) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7 mt-6 items-stretch">
        
        {/* ====================================================================
            LEFT PANEL: TẠO ĐỀ NHANH (ĐỀ TN / ĐGNL) - BỘ SGK
            ==================================================================== */}
        <div className="lg:col-span-6 flex flex-col">
          <div className="astra-panel astra-fast-panel flex-1 flex flex-col justify-between">
            <div>
              {/* Panel Header */}
              <div className="flex items-center justify-between pb-4 border-b border-emerald-100 mb-5">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-700">
                    <Zap className="w-5 h-5 fill-emerald-600 text-emerald-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">
                      Tạo Đề Nhanh (Đề TN / ĐGNL)
                    </h2>
                    <span className="text-xs text-emerald-700 font-semibold">
                      Chuẩn Bộ SGK & Khung ma trận GDPT
                    </span>
                  </div>
                </div>
                <span className="astra-tag-green">1-Click Nhanh</span>
              </div>

              {/* 1. Chọn loại đề thi */}
              <div className="mb-5">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                  1. Chọn định dạng đề chuẩn:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  <div
                    onClick={() => handleSelectExamType('THPT_STANDARD')}
                    className={`astra-type-card ${examType === 'THPT_STANDARD' ? 'selected' : ''}`}
                  >
                    <div className="font-extrabold text-sm text-gray-900">THPT Quốc Gia</div>
                    <div className="text-xs text-gray-500 mt-0.5">40 câu · 50 phút</div>
                    <div className="text-xs text-emerald-700 font-semibold mt-1">100% Trắc nghiệm</div>
                  </div>

                  <div
                    onClick={() => handleSelectExamType('DGNL_DHQG')}
                    className={`astra-type-card ${examType === 'DGNL_DHQG' ? 'selected' : ''}`}
                  >
                    <div className="font-extrabold text-sm text-gray-900">ĐGNL ĐHQG</div>
                    <div className="text-xs text-gray-500 mt-0.5">30 câu · 40 phút</div>
                    <div className="text-xs text-indigo-700 font-semibold mt-1">Tư duy logic</div>
                  </div>

                  <div
                    onClick={() => handleSelectExamType('MID_TERM')}
                    className={`astra-type-card ${examType === 'MID_TERM' ? 'selected' : ''}`}
                  >
                    <div className="font-extrabold text-sm text-gray-900">Đề Giữa Kỳ</div>
                    <div className="text-xs text-gray-500 mt-0.5">25 câu · 45 phút</div>
                    <div className="text-xs text-amber-700 font-semibold mt-1">Theo chương</div>
                  </div>
                </div>
              </div>

              {/* 2. Chọn Môn học */}
              <div className="mb-6">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                  2. Chọn môn học:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {SUBJECT_LIST.map((sub) => {
                    const isSelected = selectedSubject === sub;
                    return (
                      <button
                        type="button"
                        key={sub}
                        onClick={() => setSelectedSubject(sub)}
                        className={`astra-subject-cell ${isSelected ? 'active' : ''}`}
                      >
                        {isSelected && <CheckCircle2 className="w-3.5 h-3.5 inline mr-1 text-emerald-600" />}
                        {sub}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Thông tin ma trận mặc định */}
              <div className="p-3.5 bg-emerald-50/60 rounded-xl border border-emerald-100 text-xs text-emerald-900 space-y-1 mb-6">
                <div className="font-bold flex items-center gap-1.5">
                  <GraduationCap className="w-4 h-4 text-emerald-700" />
                  Cơ sở dữ liệu tự động neo chuẩn:
                </div>
                <div>• SGK Kết Nối Tri Thức, Cánh Diều, Chân Trời Sáng Tạo.</div>
                <div>• Phân bổ nhận thức Bloom: <strong>40% Biết · 30% Hiểu · 20% Vận dụng · 10% VDC</strong>.</div>
                <div>• Blind Solver tự động kiểm thử đáp án độc lập trước khi xuất xưởng.</div>
              </div>
            </div>

            {/* Nút to màu Baby Green */}
            <div>
              <button
                type="button"
                onClick={handleFastGenerate}
                disabled={isGenerating}
                className="astra-btn-baby-green"
              >
                <Zap className="w-5 h-5 mr-2 fill-current" />
                <span>{isGenerating ? 'ĐANG TẠO ĐỀ NHANH...' : `TẠO ĐỀ NHANH: ${selectedSubject.toUpperCase()}`}</span>
              </button>
              <div className="text-center text-xs text-gray-500 mt-2">
                Không cần cấu hình phức tạp · Tự động chuẩn hóa form và barem
              </div>
            </div>
          </div>
        </div>

        {/* ====================================================================
            RIGHT PANEL: TỰ SOẠN & ĐIỀU CHỈNH THÊM (Chatbot Baseline)
            ==================================================================== */}
        <div className="lg:col-span-6 flex flex-col">
          <form 
            onSubmit={handleCustomGenerate}
            className="astra-panel astra-custom-panel flex-1 flex flex-col justify-between"
          >
            <div>
              {/* Panel Header */}
              <div className="flex items-center justify-between pb-4 border-b border-gray-100 mb-5">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-700">
                    <Sliders className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">
                      Tự Soạn & Điều Chỉnh Thêm
                    </h2>
                    <span className="text-xs text-gray-500 font-semibold">
                      Tùy biến nội dung · Trợ lý Chatbot tương tác
                    </span>
                  </div>
                </div>
                <span className="astra-tag-indigo">Tự Do Tinh Chỉnh</span>
              </div>

              {/* Khung nhập yêu cầu chi tiết */}
              <div className="mb-4">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                  Lưu ý cụ thể cho Đề thi (Prompt):
                </label>
                <textarea
                  rows={4}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Ví dụ: Đề thi học kỳ gồm 40 câu. Tập trung 15 câu đồ thị dao động và sóng cơ, tăng cường các câu hỏi liên hệ thực tế đời sống..."
                  className="astra-textarea-desktop"
                />
              </div>

              {/* Các thông số tinh chỉnh */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-xs font-bold text-gray-600 mb-1">Số câu hỏi:</label>
                  <input
                    type="number"
                    min="10"
                    max="60"
                    value={itemCount}
                    onChange={(e) => setItemCount(Number(e.target.value))}
                    className="astra-input-desktop"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-600 mb-1">Thời gian làm bài:</label>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      min="15"
                      max="120"
                      value={durationMinutes}
                      onChange={(e) => setDurationMinutes(Number(e.target.value))}
                      className="astra-input-desktop"
                    />
                    <span className="text-xs text-gray-500">phút</span>
                  </div>
                </div>
              </div>

              {/* File đính kèm */}
              <div className="mb-5">
                <label className="block text-xs font-bold text-gray-600 mb-1">
                  Đính kèm ma trận / Đề mẫu riêng (nếu có):
                </label>
                <div className="p-3 bg-gray-50 border border-dashed border-gray-300 rounded-xl flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <FileText className="w-4 h-4 text-indigo-600" />
                    <span>{uploadedFiles[0] || 'Kéo thả file .docx, .pdf vào đây'}</span>
                  </div>
                  <UploadCloud className="w-4 h-4 text-gray-400 cursor-pointer hover:text-indigo-600" />
                </div>
              </div>
            </div>

            {/* Nút Tự Soạn */}
            <div>
              <button
                type="submit"
                disabled={isGenerating}
                className="astra-btn-indigo"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                <span>{isGenerating ? 'ĐANG KHỞI CHẠY...' : 'TẠO ĐỀ THEO YÊU CẦU RIÊNG'}</span>
              </button>
              <div className="text-center text-xs text-gray-500 mt-2">
                Hệ thống sẽ tổng hợp ma trận riêng và đối chiếu với giáo án của Thầy/Cô
              </div>
            </div>
          </form>
        </div>

      </div>
    </div>
  );
};
