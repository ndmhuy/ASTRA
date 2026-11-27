import React from 'react';
import { CheckCircle2, Eye, History, LoaderCircle, Undo2 } from 'lucide-react';

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
  showApprove?: boolean;
  canApprove?: boolean;
  approving?: boolean;
  onApprove?: () => void;
  onOpenPdfPreview?: () => void;
  onShowHistory?: () => void;
  onUndoRegeneration?: () => void;
  undoing?: boolean;
}

export const CanvasHeader: React.FC<CanvasHeaderProps> = ({
  examMeta,
  isGenerating,
  canExport = true,
  showApprove,
  canApprove,
  approving,
  onApprove,
  onOpenPdfPreview,
  onShowHistory,
  onUndoRegeneration,
  undoing,
}) => {
  const displayApprove = showApprove ?? Boolean(canApprove);
  return (
    <header className="canvas-header">
      <div className="canvas-heading-copy">
        <div className="canvas-title">{examMeta?.title || 'Bản xem trước đề thi'}</div>
        <div className="canvas-status" role="status">
          {isGenerating && examMeta
            ? `Đang soạn · ${examMeta.completedCount} / ${examMeta.totalCount} câu`
            : examMeta
              ? `${examMeta.totalCount} câu · ${examMeta.duration} phút`
              : 'Nội dung đề sẽ xuất hiện tại đây'}
        </div>
        {examMeta && !isGenerating && canExport && (
          <span className="canvas-approved-pill">
            <CheckCircle2 size={12} aria-hidden="true" />
            Đã duyệt
          </span>
        )}
      </div>
      {examMeta && !isGenerating && <div className="canvas-actions">
        {onUndoRegeneration && (
          <button type="button" className="button-secondary" title="Hoàn tác lần tạo lại câu vừa rồi"
            disabled={undoing} onClick={onUndoRegeneration}>
            <Undo2 size={14} aria-hidden="true" />{undoing ? 'Đang hoàn tác…' : 'Hoàn tác'}
          </button>
        )}
        {onShowHistory && (
          <button type="button" className="button-secondary" onClick={onShowHistory}>
            <History size={14} aria-hidden="true" />Lịch sử phiên bản
          </button>
        )}
        {displayApprove && !canApprove && onOpenPdfPreview && (
          <button type="button" className="button-primary" onClick={onOpenPdfPreview}>
            <Eye size={14} aria-hidden="true" />
            Mở xem trước PDF để duyệt
          </button>
        )}
        {displayApprove && (
          <button
            type="button"
            className={canApprove ? 'button-primary' : 'button-secondary'}
            disabled={!canApprove || approving}
            title={!canApprove ? 'Mở tab Xem trước PDF của bản hiện tại trước khi phê duyệt' : undefined}
            onClick={onApprove}
          >
            {approving && <LoaderCircle className="exam-status-spinner" size={14} aria-hidden="true" />}
            Đã kiểm tra, phê duyệt bản này
          </button>
        )}
      </div>}
    </header>
  );
};
