import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, Pencil } from 'lucide-react';
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
    <section className={`exam-question-card ${visible ? 'visible' : 'appearing'} ${flagged ? 'is-flagged' : ''}`} aria-label={`Câu ${index + 1}`}>
      <div className="question-card-top">
        <div className="question-stem"><strong>Câu {question.stableId?.split('-')[1] || index + 1}.</strong><MathRenderer content={question.stem} /></div>
        {onEdit && (
          <button
            type="button"
            className="question-quick-edit-btn"
            aria-label={`Chỉnh sửa câu ${index + 1}`}
            title="Chỉnh sửa hoặc tạo lại câu hỏi này"
            onClick={onEdit}
          >
            <Pencil size={12} aria-hidden="true" />
            <span>Chỉnh sửa</span>
          </button>
        )}
      </div>
      {question.drawingLatex && <details className="question-drawing-details"><summary>Hình minh họa (xem trực quan ở mục Xem trước PDF)</summary><pre>{question.drawingLatex}</pre></details>}
      {(!question.questionType || question.questionType === 'mcq') && <div className="question-choices">
        {(['A', 'B', 'C', 'D'] as const).map(key => (
          <div key={key} className={`question-choice ${review && question.status === 'VERIFIED' && question.key === key ? 'correct' : ''}`}>
            <strong className="choice-key-badge">{key}.</strong><MathRenderer content={question.choices[key]} />
            {review && question.status === 'VERIFIED' && question.key === key && (
              <span className="answer-label">
                <CheckCircle2 size={12} aria-hidden="true" />
                Đáp án
              </span>
            )}
          </div>
        ))}
      </div>}
      {question.questionType === 'true_false' && (
        <div className="question-tf-list">
          {question.statements?.map((statement, i) => (
            <div key={i} className="question-choice question-tf-row">
              <strong>{'abcd'[i]})</strong>
              <MathRenderer content={statement.text} />
              {review && (
                <span className={`tf-answer-pill ${statement.answer ? 'is-true' : 'is-false'}`}>
                  {statement.answer ? 'Đúng' : 'Sai'}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
      {question.questionType === 'short_answer' && (
        <div className="question-short-answer">
          <span>Đáp án:</span>
          {review ? (
            <strong className="short-answer-value">{question.key}</strong>
          ) : (
            <span className="short-answer-boxes" aria-label="Ô điền đáp án">
              <span>□</span><span>□</span><span>□</span><span>□</span>
            </span>
          )}
        </div>
      )}
      {review && (
        <details className={`question-review ${flagged ? 'flagged' : ''}`}>
          <summary>
            {flagged ? (
              <><AlertTriangle size={14} aria-hidden="true" /><span>Cần xem xét · Xem ghi chú</span></>
            ) : question.status === 'VERIFIED' ? (
              <><CheckCircle2 size={14} aria-hidden="true" /><span>Đã đối chiếu · Xem lời giải</span></>
            ) : (
              <span>Chờ kiểm định · Xem đáp án dự kiến</span>
            )}
          </summary>
          <div className="review-content">
            {flagged ? <>
              <p><strong>Đáp án dự kiến:</strong> {question.key}{question.writerKey ? ` · Người soạn: ${question.writerKey}` : ''}{question.solverKey ? ` · Giải độc lập: ${question.solverKey}` : ''}</p>
              <p><MathRenderer content={question.auditNotes || 'Câu hỏi cần được kiểm tra trước khi sử dụng.'} /></p>
            </> : <p><strong>Đáp án:</strong> {question.key}</p>}
            {question.explanation && <div className="review-explanation"><MathRenderer content={question.explanation} /></div>}
            {question.sourceReference && <p className="review-source">Nguồn: {question.sourceReference}</p>}
            {onEdit && <button type="button" className="button-secondary" onClick={onEdit}>Sửa câu hỏi</button>}
          </div>
        </details>
      )}
    </section>
  );
};
