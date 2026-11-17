import React from 'react';
import { Download, FileCheck2 } from 'lucide-react';

interface ExamMeta {
  title: string;
  subject: string;
  duration: number;
  completedCount: number;
  totalCount: number;
}

interface CanvasHeaderProps {
  examMeta: ExamMeta | null;
  isGenerating: boolean;
  canExport?: boolean;
  canExportPdf?: boolean;
  onExportPdf?: () => void;
  onExportWord?: () => void;
  onExportAnswer?: () => void;
  showApprove?: boolean;
  canApprove?: boolean;
  approving?: boolean;
  onApprove?: () => void;
  onOpenPdfPreview?: () => void;
}

export const CanvasHeader: React.FC<CanvasHeaderProps> = ({
  examMeta,
  isGenerating,
  canExport = true,
  canExportPdf = true,
  onExportPdf,
  onExportWord,
  onExportAnswer,
  showApprove,
  canApprove,
  approving,
  onApprove,
  onOpenPdfPreview,
}) => {
  const displayApprove = showApprove ?? Boolean(canApprove);
  return (
    <header className="canvas-header">
      <div className="canvas-heading-copy">
        <div>
          <div className="canvas-title">{examMeta?.title || 'Bản xem trước đề thi'}</div>
          <div className="canvas-status" role="status">{isGenerating && examMeta ? `Đang soạn · ${examMeta.completedCount} / ${examMeta.totalCount} câu` : examMeta ? `${examMeta.totalCount} câu · ${examMeta.duration} phút` : 'Nội dung đề sẽ xuất hiện tại đây'}</div>
        </div>
      </div>
      {examMeta && !isGenerating && <div className="canvas-actions">
        {displayApprove && !canApprove && onOpenPdfPreview && (
          <button className="button-secondary" onClick={onOpenPdfPreview}>Mở xem trước PDF để duyệt</button>
        )}
        {displayApprove && (
          <button
            className="button-primary"
            disabled={!canApprove || approving}
            title={!canApprove ? 'Mở tab Xem trước PDF của bản hiện tại trước khi phê duyệt' : undefined}
            onClick={onApprove}
          >
            Đã kiểm tra, phê duyệt bản này
          </button>
        )}
        {canExport && <>
          <button
            className="button-primary"
            disabled={canExportPdf === false}
            title={canExportPdf === false ? 'Cần bản xem trước PDF sẵn sàng của phiên bản hiện tại' : undefined}
            onClick={onExportPdf}
          >
            <Download size={15} aria-hidden="true" />Xuất PDF
          </button>
          <button className="button-secondary" onClick={onExportWord}><Download size={15} aria-hidden="true" />Xuất LaTeX</button>
          <button className="button-secondary" onClick={onExportAnswer}><FileCheck2 size={15} aria-hidden="true" />Tải đáp án JSON</button>
        </>}
      </div>}
    </header>
  );
};
