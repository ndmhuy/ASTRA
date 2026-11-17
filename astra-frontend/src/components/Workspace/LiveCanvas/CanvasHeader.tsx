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
  onExportWord?: () => void;
  onExportAnswer?: () => void;
  canApprove?: boolean;
  approving?: boolean;
  onApprove?: () => void;
}

export const CanvasHeader: React.FC<CanvasHeaderProps> = ({ examMeta, isGenerating, canExport = true, onExportWord, onExportAnswer, canApprove, approving, onApprove }) => (
  <header className="canvas-header">
    <div className="canvas-heading-copy">
      <div>
        <div className="canvas-title">{examMeta?.title || 'Bản xem trước đề thi'}</div>
        <div className="canvas-status" role="status">{isGenerating && examMeta ? `Đang soạn · ${examMeta.completedCount} / ${examMeta.totalCount} câu` : examMeta ? `${examMeta.totalCount} câu · ${examMeta.duration} phút` : 'Nội dung đề sẽ xuất hiện tại đây'}</div>
      </div>
    </div>
    {examMeta && !isGenerating && <div className="canvas-actions">
      {canApprove && <button className="button-primary" disabled={approving} onClick={onApprove}>Đã kiểm tra, phê duyệt bản này</button>}
      {canExport && <><button className="button-secondary" onClick={onExportAnswer}><FileCheck2 size={15} aria-hidden="true" />Tải đáp án JSON</button>
      <button className="button-primary" onClick={onExportWord}><Download size={15} aria-hidden="true" />Xuất LaTeX</button></>}
    </div>}
  </header>
);
