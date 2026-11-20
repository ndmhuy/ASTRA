import React, { useEffect, useState } from 'react';
import { Image as ImageIcon } from 'lucide-react';
import type { QuestionItem } from '../../../types/exam';
import { MathRenderer } from '../../MathRenderer';

interface QuestionCardProps {
  question: QuestionItem;
  index: number;
  onEdit?: () => void;
  onOpenPdf?: () => void;
  appearing?: boolean;
  review?: boolean;
  expandedDetails?: boolean;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({ question, index, onEdit, onOpenPdf, appearing = false, review = false, expandedDetails }) => {
  const [visible, setVisible] = useState(!appearing);
  useEffect(() => {
    const frame = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(frame);
  }, []);
  const flagged = question.status === 'FLAGGED';
  return (
    <section className={`exam-question-card ${visible ? 'visible' : 'appearing'}`} aria-label={`Câu ${index + 1}`}>
      <div className="question-stem"><strong>Câu {question.stableId?.split('-')[1] || index + 1}.</strong><MathRenderer content={question.stem} /></div>
      {question.drawingLatex && !review && (
        <div className="question-figure-callout">
          <span className="question-figure-note">
            <ImageIcon size={14} aria-hidden="true" />
            Câu hỏi có hình vẽ minh họa trong bản in LaTeX/PDF.
          </span>
          {onOpenPdf && (
            <button type="button" className="question-figure-btn" onClick={onOpenPdf}>
              Xem hình trong bản PDF
            </button>
          )}
        </div>
      )}
      {question.drawingLatex && review && (
        <details open={expandedDetails} className="question-tikz-source">
          <summary>Mã nguồn hình vẽ TikZ (tham khảo kỹ thuật)</summary>
          <pre>{question.drawingLatex}</pre>
        </details>
      )}
      {(!question.questionType || question.questionType === 'mcq') && <div className="question-choices">
        {(['A', 'B', 'C', 'D'] as const).map(key => (
          <div key={key} className={`question-choice ${review && question.status === 'VERIFIED' && question.key === key ? 'correct' : ''}`}>
            <strong>{key}.</strong><MathRenderer content={question.choices[key]} />
            {review && question.status === 'VERIFIED' && question.key === key && <span className="answer-label">Đáp án</span>}
          </div>
        ))}
      </div>}
      {question.questionType === 'true_false' && question.statements?.map((statement, i) => <div key={i} className="question-choice">
        <strong>{'abcd'[i]})</strong><MathRenderer content={statement.text} />
        {review && <span>{statement.answer ? 'Đúng' : 'Sai'}</span>}
      </div>)}
      {question.questionType === 'short_answer' && <p>Đáp án: {review ? question.key : '□ □ □ □'}</p>}
      {review && (
        <details open={expandedDetails} className={`question-review ${flagged ? 'flagged' : ''}`}>
          <summary>{flagged ? 'Cần xem xét · Xem ghi chú' : question.status === 'VERIFIED' ? 'Đã đối chiếu · Xem lời giải' : 'Chờ kiểm định · Xem đáp án dự kiến'}</summary>
          <div className="review-content">
            {flagged ? <>
              <p>Đáp án dự kiến: {question.key}{question.writerKey ? ` · Người soạn: ${question.writerKey}` : ''}{question.solverKey ? ` · Giải độc lập: ${question.solverKey}` : ''}</p>
              <p><MathRenderer content={question.auditNotes || 'Câu hỏi cần được kiểm tra trước khi sử dụng.'} /></p>
            </> : <p>Đáp án: {question.key}</p>}
            {question.explanation && <MathRenderer content={question.explanation} />}
            {question.sourceReference && <p>Nguồn: {question.sourceReference}</p>}
            {onEdit && <button className="button-secondary" onClick={onEdit}>Sửa câu hỏi</button>}
          </div>
        </details>
      )}
    </section>
  );
};
