import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, Pencil } from 'lucide-react';
import type { QuestionItem } from '../../../types/exam';
import { getChoiceGridClass } from '../../../utils/choiceLayout.ts';
import { MathRenderer } from '../../MathRenderer';

interface QuestionCardProps {
  question: QuestionItem;
  articleRef?: React.Ref<HTMLElement>;
  index: number;
  onEdit?: () => void;
  appearing?: boolean;
  review?: boolean;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({ question, articleRef, index, onEdit, appearing = false, review = false }) => {
  const [visible, setVisible] = useState(!appearing);
  useEffect(() => {
    const frame = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(frame);
  }, []);
  const matched = question.answerCheck === 'matched';
  const flagged = question.answerCheck === 'mismatched';
  return (
    <section ref={articleRef} className={`exam-question-card ${visible ? 'visible' : 'appearing'} ${flagged ? 'is-flagged' : ''}`} aria-label={`Câu ${index + 1}`}>
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
      {flagged && (
        <p className="question-answer-warning">
          <AlertTriangle size={16} aria-hidden="true" />
          <span><strong>Cảnh báo lệch đáp án.</strong> Đáp án dự kiến khác kết quả giải độc lập. Thầy cô kiểm tra và sửa câu này nếu cần trước khi duyệt đề.</span>
        </p>
      )}
      {question.figures?.map(figure => (
        figure.mimeType === 'application/pdf'
          ? <iframe key={figure.url} loading="lazy" title={figure.alt} src={figure.url} width="100%" height="240" />
          : <img key={figure.url} className="contract-question-figure" loading="lazy" alt={figure.alt} src={figure.url} />
      ))}
      {!question.figures?.length && question.drawingLatex && <details className="question-drawing-details"><summary>Hình minh họa (xem trực quan ở mục Xem trước PDF)</summary><pre>{question.drawingLatex}</pre></details>}
      {(!question.questionType || question.questionType === 'mcq') && (
        <div className={`question-choices ${getChoiceGridClass(question.choices)}`}>
          {(['A', 'B', 'C', 'D'] as const).map(key => (
            <div key={key} className={`question-choice ${review && matched && question.key === key ? 'correct' : ''}`}>
              <strong className="choice-key-badge">{key}.</strong><MathRenderer content={question.choices[key]} />
              {review && matched && question.key === key && (
                <span className="answer-label">
                  <CheckCircle2 size={12} aria-hidden="true" />
                  Đáp án
                </span>
              )}
            </div>
          ))}
        </div>
      )}
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
      {question.questionType === 'short_answer' && (review || !question.responseKind) && (
        <div className="question-short-answer">
          <span>Đáp án:</span>
          {review ? (
            <strong className="short-answer-value">{question.key}</strong>
          ) : (
            <span className="short-answer-boxes" aria-label={`${question.maxAnswerCharacters ?? 5} ô điền đáp án`}>
              {Array.from({ length: question.maxAnswerCharacters ?? 5 }, (_, index) => (
                <span key={index} className="short-answer-cell" aria-hidden="true" />
              ))}
            </span>
          )}
        </div>
      )}
      {review && (
        <details className={`question-review ${flagged ? 'flagged' : ''}`}>
          <summary>
            {flagged ? (
              <span>Xem hai đáp án để đối chiếu</span>
            ) : matched ? (
              <><CheckCircle2 size={14} aria-hidden="true" /><span>Khớp đáp án · Xem lời giải</span></>
            ) : (
              <span>Cần kiểm tra lại · Xem đáp án dự kiến</span>
            )}
          </summary>
          <div className="review-content">
            <p><strong>{matched ? 'Đáp án' : 'Đáp án dự kiến'}:</strong> {question.key}</p>
            {flagged && question.solverKey && <p><strong>Giải độc lập:</strong> {question.solverKey}</p>}
            {!matched && !flagged && <p>{(question.answerCheck && question.auditNotes) || 'Câu hỏi cần được kiểm tra trước khi sử dụng.'}</p>}
            {question.explanation && <div className="review-explanation"><MathRenderer content={question.explanation} /></div>}
            {question.sourceReference && <p className="review-source">Nguồn: {question.sourceReference}</p>}
            {onEdit && <button type="button" className="button-secondary" onClick={onEdit}>Sửa câu hỏi</button>}
          </div>
        </details>
      )}
    </section>
  );
};
