import React, { useEffect, useState } from 'react';
import type { QuestionItem } from '../../../types/exam';
import { MathRenderer } from '../../MathRenderer';

interface QuestionCardProps {
  question: QuestionItem;
  index: number;
  onEdit?: () => void;
  appearing?: boolean;
  review?: boolean;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({ question, index, onEdit, appearing = false, review = false }) => {
  const [visible, setVisible] = useState(!appearing);
  useEffect(() => {
    const frame = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(frame);
  }, []);
  const flagged = question.status === 'FLAGGED';
  return (
    <section className={`exam-question-card ${visible ? 'visible' : 'appearing'}`} aria-label={`Câu ${index + 1}`}>
      <div className="question-stem"><strong>Câu {index + 1}.</strong><MathRenderer content={question.stem} /></div>
      <div className="question-choices">
        {(['A', 'B', 'C', 'D'] as const).map(key => (
          <div key={key} className={`question-choice ${review && question.status === 'VERIFIED' && question.key === key ? 'correct' : ''}`}>
            <strong>{key}.</strong><MathRenderer content={question.choices[key]} />
            {review && question.status === 'VERIFIED' && question.key === key && <span className="answer-label">Đáp án</span>}
          </div>
        ))}
      </div>
      {review && (
        <details className={`question-review ${flagged ? 'flagged' : ''}`}>
          <summary>{flagged ? 'Cần xem xét · Xem ghi chú' : question.status === 'VERIFIED' ? 'Đã đối chiếu · Xem lời giải' : 'Chờ kiểm định · Xem đáp án dự kiến'}</summary>
          <div className="review-content">
            {flagged ? <>
              <p>Đáp án dự kiến: {question.key}{question.writerKey ? ` · Người soạn: ${question.writerKey}` : ''}{question.solverKey ? ` · Giải độc lập: ${question.solverKey}` : ''}</p>
              <p><MathRenderer content={question.auditNotes || 'Câu hỏi cần được kiểm tra trước khi sử dụng.'} /></p>
            </> : <p>Đáp án: {question.key}</p>}
            {question.explanation && <MathRenderer content={question.explanation} />}
            {onEdit && <button className="button-secondary" onClick={onEdit}>Sửa câu hỏi</button>}
          </div>
        </details>
      )}
    </section>
  );
};
