import React, { useEffect, useRef, useState } from 'react';
import type { QuestionItem } from '../../../types/exam';
import { MathRenderer } from '../../MathRenderer';

interface QuestionCardProps {
  question: QuestionItem;
  index: number;
  onEdit?: () => void;
  appearing?: boolean;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({ question, index, onEdit, appearing = false }) => {
  const [visible, setVisible] = useState(!appearing);
  const mountedRef = useRef(false);

  useEffect(() => {
    if (appearing && !mountedRef.current) {
      mountedRef.current = true;
      // Trigger fade-in on next frame
      requestAnimationFrame(() => {
        requestAnimationFrame(() => setVisible(true));
      });
    }
  }, [appearing]);

  const choiceKeys = ['A', 'B', 'C', 'D'] as const;

  return (
    <div
      className={`exam-question-card ${appearing ? (visible ? 'visible' : 'appearing') : 'visible'}`}
    >
      {/* Question header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 10 }}>
        <span
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: '#059669',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            flexShrink: 0,
            paddingTop: 2,
          }}
        >
          Câu {index + 1}:
        </span>
        <div style={{ fontSize: 14, color: '#0f172a', lineHeight: 1.6, flex: 1 }}>
          <MathRenderer content={question.stem} />
        </div>
      </div>

      {/* Choices */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {choiceKeys.map((key) => {
          const isCorrect = question.key === key;
          return (
            <div
              key={key}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8,
                padding: '6px 10px',
                borderRadius: 4,
                background: isCorrect ? '#ecfdf5' : 'transparent',
                border: isCorrect ? '1px solid #a7f3d0' : '1px solid transparent',
                transition: 'background 150ms ease',
              }}
            >
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: isCorrect ? '#059669' : '#64748b',
                  flexShrink: 0,
                  minWidth: 16,
                  paddingTop: 1,
                }}
              >
                {key}.
              </span>
              <span style={{ fontSize: 13, color: isCorrect ? '#065f46' : '#334155', lineHeight: 1.5 }}>
                <MathRenderer content={question.choices[key]} />
              </span>
            </div>
          );
        })}
      </div>

      {/* Flagged status */}
      {question.status === 'FLAGGED' && (
        <div
          style={{
            marginTop: 12,
            padding: '8px 12px',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: 4,
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
          }}
        >
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 2 }}>
              Cần xem xét
            </div>
            {question.auditNotes && (
              <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>{question.auditNotes}</div>
            )}
          </div>
          {onEdit && (
            <button
              onClick={onEdit}
              style={{
                padding: '4px 10px',
                fontSize: 12,
                fontWeight: 500,
                color: '#334155',
                background: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: 4,
                cursor: 'pointer',
                flexShrink: 0,
                whiteSpace: 'nowrap',
              }}
            >
              Sửa
            </button>
          )}
        </div>
      )}
    </div>
  );
};
