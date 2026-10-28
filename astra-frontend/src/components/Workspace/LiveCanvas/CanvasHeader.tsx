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

export const CanvasHeader: React.FC<CanvasHeaderProps> = ({
  examMeta,
  isGenerating,
  onExportWord,
  onExportAnswer,
}) => {
  const btnStyle: React.CSSProperties = {
    padding: '5px 12px',
    fontSize: 12,
    fontWeight: 500,
    color: '#334155',
    background: '#ffffff',
    border: '1px solid #cbd5e1',
    borderRadius: 4,
    cursor: 'pointer',
    transition: 'border-color 120ms ease, background 120ms ease',
    whiteSpace: 'nowrap',
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 20px',
        borderBottom: '1px solid #e2e8f0',
        background: '#ffffff',
        flexShrink: 0,
        minHeight: 46,
        gap: 12,
      }}
    >
      {/* Status / Title */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {isGenerating && examMeta ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span
              style={{
                display: 'inline-block',
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: '#059669',
                flexShrink: 0,
              }}
            />
            <span style={{ fontSize: 13, fontWeight: 600, color: '#059669', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              ĐANG TẠO:
            </span>
            <span style={{ fontSize: 13, color: '#334155', fontWeight: 500 }}>
              {examMeta.completedCount} / {examMeta.totalCount} câu hoàn thành
            </span>
          </div>
        ) : examMeta ? (
          <div style={{ fontSize: 14, fontWeight: 600, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {examMeta.title || `Đề thi ${examMeta.subject}`}
          </div>
        ) : (
          <div style={{ fontSize: 13, color: '#94a3b8' }}>Bản xem trước đề thi</div>
        )}
      </div>

      {/* Action Buttons */}
      {examMeta && !isGenerating && (
        <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
          <button style={btnStyle} onClick={onExportWord}>
            Xuất Word
          </button>
          <button style={btnStyle} onClick={onExportAnswer}>
            Xuất Đáp Án
          </button>
        </div>
      )}
    </div>
  );
};
