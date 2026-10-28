import React from 'react';
import type { GenerationProgress } from '../types/exam';
import { MathRenderer } from './MathRenderer';
import { 
  CheckCircle2, 
  Loader2, 
  Clock, 
  ChevronRight
} from 'lucide-react';

interface StepperViewProps {
  progress: GenerationProgress;
  onViewResults: () => void;
  onCancel: () => void;
}

export const StepperView: React.FC<StepperViewProps> = ({
  progress,
  onViewResults,
  onCancel
}) => {
  const isFinished = progress.stage >= 5 && progress.percent >= 100;

  // Teacher-friendly stages in plain language (No AI jargon)
  const teacherSteps = [
    { num: 1, title: 'Chuẩn hóa ma trận đề thi', desc: 'Phân bổ tỷ lệ Nhận biết, Thông hiểu và Vận dụng.' },
    { num: 2, title: 'Tra cứu SGK & cơ sở kiến thức', desc: 'Đảm bảo nội dung nằm đúng chương trình GDPT mới.' },
    { num: 3, title: 'Soạn thảo & Giải đối chiếu', desc: 'Hệ thống tự giải lại độc lập để đảm bảo không lệch đáp án.' },
    { num: 4, title: 'Thẩm định sư phạm & Bẫy sai', desc: 'Kiểm tra độ rõ nghĩa của câu hỏi và các phương án nhiễu.' },
    { num: 5, title: 'Hoàn tất hồ sơ đề thi', desc: 'Chuẩn bị bản in và bảng barem điểm hoàn chỉnh.' }
  ];

  return (
    <div className="astra-simple-container">
      {/* Calm Status Box */}
      <div className="astra-clean-card mb-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
          <div>
            <span className="astra-status-pill">
              <span className="astra-pulse-dot"></span>
              Đang tự động kiểm định đề thi
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">
              {progress.stageName || 'Hệ thống đang tiến hành soạn và duyệt đề...'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Thầy/Cô vui lòng đợi trong giây lát. Hệ thống đang rà soát tính chính xác của từng câu hỏi.
            </p>
          </div>

          <div className="astra-timer-pill">
            <Clock className="w-4 h-4 text-emerald-600" />
            <span className="text-sm font-semibold text-gray-800">
              {isFinished ? 'Đã hoàn tất!' : `Còn ~${progress.estimatedSecondsLeft} giây`}
            </span>
          </div>
        </div>

        {/* Soft Progress Bar */}
        <div className="astra-soft-progress-track">
          <div 
            className="astra-soft-progress-fill"
            style={{ width: `${Math.min(100, Math.max(8, progress.percent))}%` }}
          ></div>
        </div>

        <div className="flex justify-between items-center text-xs text-gray-500 mt-2">
          <span>Tiến độ: {progress.percent}%</span>
          <span>Đã kiểm định: {progress.completedItems} / {progress.totalItems} câu</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Left: 5 Simple Step Checklist */}
        <div className="md:col-span-6 space-y-2.5">
          <h3 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">
            Các bước kiểm định:
          </h3>

          <div className="astra-clean-card p-4 space-y-3">
            {teacherSteps.map((st) => {
              const isPast = progress.stage > st.num || isFinished;
              const isCurrent = progress.stage === st.num && !isFinished;

              return (
                <div key={st.num} className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {isPast ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    ) : isCurrent ? (
                      <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-gray-300 flex items-center justify-center text-xs text-gray-400 font-bold">
                        {st.num}
                      </div>
                    )}
                  </div>
                  <div>
                    <div className={`text-sm font-bold ${isCurrent ? 'text-indigo-900' : isPast ? 'text-gray-900' : 'text-gray-400'}`}>
                      {st.title}
                    </div>
                    <div className="text-xs text-gray-500">
                      {st.desc}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="pt-2">
            {!isFinished && (
              <button
                onClick={onCancel}
                className="text-xs text-gray-400 hover:text-red-600 hover:underline"
              >
                Hủy bỏ quá trình này
              </button>
            )}
          </div>
        </div>

        {/* Right: Live Preview */}
        <div className="md:col-span-6">
          <h3 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">
            Xem trước câu hỏi vừa duyệt:
          </h3>

          <div className="astra-clean-card p-5">
            {progress.latestItemPreview ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                  <span className="text-xs font-bold text-gray-700">
                    Câu #{progress.latestItemPreview.id} ({progress.latestItemPreview.topic})
                  </span>
                  <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                    ✔ Đạt yêu cầu
                  </span>
                </div>

                <div className="text-sm text-gray-800 font-medium leading-relaxed">
                  <MathRenderer content={progress.latestItemPreview.stem} />
                </div>

                <div className="space-y-1 text-xs text-gray-700 pt-1">
                  {Object.entries(progress.latestItemPreview.choices).map(([key, val]) => (
                    <div 
                      key={key} 
                      className={`p-1.5 rounded ${key === progress.latestItemPreview?.key ? 'bg-emerald-50 font-bold text-emerald-900' : ''}`}
                    >
                      <span className="mr-1">{key}.</span>
                      <MathRenderer content={val} />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="py-10 text-center text-gray-400 text-sm">
                <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
                Đang nạp câu hỏi...
              </div>
            )}
          </div>

          {/* Prominent Next Button when Finished */}
          {isFinished && (
            <div className="mt-4">
              <button
                onClick={onViewResults}
                className="astra-hero-button"
              >
                <span>XEM & IN ĐỀ THI NGAY</span>
                <ChevronRight className="w-5 h-5 ml-2" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
