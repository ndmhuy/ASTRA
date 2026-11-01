import React from 'react';

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
  onExportWord?: () => void;
  onExportAnswer?: () => void;
}

export const CanvasHeader: React.FC<CanvasHeaderProps> = ({ examMeta, isGenerating, onExportWord, onExportAnswer }) => (
  <header className="canvas-header">
    <div><div className="canvas-title">{examMeta?.title || 'Bản xem trước đề thi'}</div>
      <div className="canvas-status" role="status">{isGenerating && examMeta ? `Đang soạn · ${examMeta.completedCount} / ${examMeta.totalCount} câu` : examMeta ? `${examMeta.totalCount} câu · ${examMeta.duration} phút` : 'Nội dung đề sẽ xuất hiện tại đây'}</div>
    </div>
    {examMeta && !isGenerating && <div className="canvas-actions">
      <button className="button-secondary" onClick={onExportAnswer}>Xuất đáp án</button>
      <button className="button-primary" onClick={onExportWord}>Xuất Word</button>
    </div>}
  </header>
);
