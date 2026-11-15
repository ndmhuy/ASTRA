import React from 'react';
import { Download, FileCheck2 } from 'lucide-react';
import clipboard from '../../../assets/navigation/library.svg';

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
}

export const CanvasHeader: React.FC<CanvasHeaderProps> = ({ examMeta, isGenerating, canExport = true, onExportWord, onExportAnswer }) => (
  <header className="canvas-header">
    <div className="canvas-heading-copy">
      <img src={clipboard} className="canvas-heading-art" alt="" aria-hidden="true" />
      <div>
        <div className="canvas-title">Bản xem trước đề thi</div>
        {examMeta && <div className="canvas-status" role="status">{isGenerating && examMeta ? `Đang soạn · ${examMeta.completedCount} / ${examMeta.totalCount} câu` : examMeta ? `${examMeta.totalCount} câu · ${examMeta.duration} phút` : ''}</div>}
      </div>
    </div>
    {examMeta && !isGenerating && canExport && <div className="canvas-actions">
      <button className="button-secondary" onClick={onExportAnswer}><FileCheck2 size={15} aria-hidden="true" />Xuất đáp án</button>
      <button className="button-primary" onClick={onExportWord}><Download size={15} aria-hidden="true" />Xuất Word</button>
    </div>}
  </header>
);
