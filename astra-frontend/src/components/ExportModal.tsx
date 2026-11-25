import React, { useState } from 'react';
import { X, Download, FileText, CheckSquare, BarChart3, Check } from 'lucide-react';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: 'docx' | 'pdf') => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  onExport
}) => {
  const [exportType, setExportType] = useState<'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX'>('STUDENT_EXAM');
  const [format, setFormat] = useState<'docx' | 'pdf'>('docx');
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  if (!isOpen) return null;

  const handleDownload = () => {
    onExport(exportType, format);
    setDownloadSuccess(true);
    setTimeout(() => {
      setDownloadSuccess(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="astra-modal-backdrop">
      <div className="astra-modal-card max-w-md">
        {/* Header */}
        <div className="astra-modal-header">
          <div>
            <h3 className="text-base font-bold text-gray-900">
              Xuất Đề Thi & Barem Điểm
            </h3>
            <p className="text-xs text-gray-500">
              Định dạng chuẩn để in ấn hoặc đưa vào hệ thống trộn đề
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="astra-modal-body space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
              Chọn phiên bản xuất:
            </label>
            <div className="space-y-2">
              <div
                onClick={() => setExportType('STUDENT_EXAM')}
                className={`astra-export-option ${exportType === 'STUDENT_EXAM' ? 'selected' : ''}`}
              >
                <FileText className="w-5 h-5 text-indigo-600" />
                <div>
                  <div className="text-sm font-bold text-gray-900">Đề thi cho Học sinh</div>
                  <div className="text-xs text-gray-500">
                    Không hiển thị đáp án, căn chỉnh chuẩn font chữ để in trực tiếp.
                  </div>
                </div>
              </div>

              <div
                onClick={() => setExportType('TEACHER_KEY')}
                className={`astra-export-option ${exportType === 'TEACHER_KEY' ? 'selected' : ''}`}
              >
                <CheckSquare className="w-5 h-5 text-emerald-600" />
                <div>
                  <div className="text-sm font-bold text-gray-900">Đề thi kèm Đáp án & Lời giải</div>
                  <div className="text-xs text-gray-500">
                    Bao gồm đáp án in đậm, hướng dẫn giải chi tiết và nhật ký kiểm định.
                  </div>
                </div>
              </div>

              <div
                onClick={() => setExportType('MATRIX')}
                className={`astra-export-option ${exportType === 'MATRIX' ? 'selected' : ''}`}
              >
                <BarChart3 className="w-5 h-5 text-purple-600" />
                <div>
                  <div className="text-sm font-bold text-gray-900">Khung Ma Trận & Barem Điểm</div>
                  <div className="text-xs text-gray-500">
                    Bảng ma trận kiến thức phân bổ theo 4 mức độ nhận thức Bloom.
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
              Định dạng tệp:
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setFormat('docx')}
                className={`astra-format-pill ${format === 'docx' ? 'selected' : ''}`}
              >
                <span className="font-bold text-sm">Microsoft Word (.doc)</span>
                <span className="text-xs text-gray-500 block">Dễ dàng chỉnh sửa thêm</span>
              </button>
              <button
                type="button"
                onClick={() => setFormat('pdf')}
                className={`astra-format-pill ${format === 'pdf' ? 'selected' : ''}`}
              >
                <span className="font-bold text-sm">Văn bản PDF</span>
                <span className="text-xs text-gray-500 block">Khóa định dạng in ấn</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="astra-modal-footer">
          <button onClick={onClose} className="astra-secondary-btn">
            Đóng
          </button>
          <button
            onClick={handleDownload}
            disabled={downloadSuccess}
            className={`astra-primary-cta px-5 ${downloadSuccess ? 'bg-emerald-600 hover:bg-emerald-700' : ''}`}
          >
            {downloadSuccess ? (
              <>
                <Check className="w-4 h-4 mr-1.5" />
                Đang tải tệp...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-1.5" />
                Tải xuống ngay
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
