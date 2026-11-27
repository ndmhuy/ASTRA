import React, { useEffect, useRef, useState } from 'react';
import { AlertTriangle, Check, CheckCircle2, Pencil, RotateCcw } from 'lucide-react';
import type { QuestionItem } from '../../../types/exam';
import { getChoiceGridClass } from '../../../utils/choiceLayout.ts';
import { getPrimaryReviewReason, getQuestionReviewState } from '../../../utils/questionReview.ts';
import { MathRenderer } from '../../MathRenderer';

interface QuestionCardProps {
  question: QuestionItem;
  articleRef?: React.Ref<HTMLElement>;
  index: number;
  questionLabel?: string;
  onEdit?: () => void;
  onVerify?: () => void;
  onApprove?: (reason?: string) => Promise<void> | void;
  verifying?: boolean;
  approving?: boolean;
  reviewOpen?: boolean;
  sourceNotes?: string[];
  appearing?: boolean;
  review?: boolean;
}

function formatApprovalTime(value?: string): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  articleRef,
  index,
  questionLabel,
  onEdit,
  onVerify,
  onApprove,
  verifying = false,
  approving = false,
  reviewOpen = false,
  sourceNotes = [],
  appearing = false,
  review = false,
}) => {
  const [visible, setVisible] = useState(!appearing);
  const detailsRef = useRef<HTMLDetailsElement>(null);
  const [confirmingApprove, setConfirmingApprove] = useState(false);
  const [approveReason, setApproveReason] = useState('');
  const [approveReasonError, setApproveReasonError] = useState('');

  useEffect(() => {
    const frame = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    if (reviewOpen && detailsRef.current) detailsRef.current.open = true;
  }, [reviewOpen]);

  const matched = question.answerCheck === 'matched';
  const flagged = question.answerCheck === 'mismatched';
  const approval = question.questionApproval ?? null;
  const reviewState = getQuestionReviewState(question);
  const requiresReason = !matched;
  const approvalTime = formatApprovalTime(approval?.approvedAt);

  const handleApproveClick = async () => {
    if (!onApprove || approval) return;
    if (requiresReason) {
      setApproveReasonError('');
      setConfirmingApprove(value => !value);
      return;
    }
    await onApprove('');
  };

  const handleConfirmReasonApprove = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!onApprove) return;
    const clean = approveReason.trim();
    if (!clean) {
      setApproveReasonError('Thầy cô vui lòng nhập lý do xác nhận đáp án dự kiến.');
      return;
    }
    setApproveReasonError('');
    await onApprove(clean);
    setConfirmingApprove(false);
    setApproveReason('');
  };

  return (
    <section
      ref={articleRef}
      className={`exam-question-card ${visible ? 'visible' : 'appearing'} ${flagged && !approval ? 'is-flagged' : ''} ${approval ? 'is-approved' : ''} ${review ? 'is-review-mode' : ''}`}
      aria-label={questionLabel || `Câu ${index + 1}`}
    >
      <div className="question-card-top">
        <div className="question-stem">
          <strong>Câu {question.stableId?.split('-')[1] || index + 1}.</strong>
          <MathRenderer content={question.stem} />
        </div>
        {(review || onEdit) && (
          <div className="question-card-actions">
            {review && (
              <span className={`question-status-badge is-${reviewState.kind}`}>
                {reviewState.label}
              </span>
            )}
            {review && !approval && onApprove && (
              <button
                type="button"
                className="question-action-btn is-approve"
                disabled={approving || verifying}
                onClick={() => { void handleApproveClick(); }}
              >
                <Check size={12} aria-hidden="true" />
                <span>{approving ? 'Đang lưu...' : 'Duyệt câu'}</span>
              </button>
            )}
            {review && onVerify && (
              <button
                type="button"
                className="question-action-btn is-verify"
                disabled={verifying || approving}
                onClick={onVerify}
              >
                <RotateCcw size={12} aria-hidden="true" />
                <span>{verifying ? 'Đang giải lại...' : 'Giải kiểm tra lại'}</span>
              </button>
            )}
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
        )}
      </div>

      {review && approval && (
        <div className="question-approved-meta" role="status">
          <CheckCircle2 size={14} aria-hidden="true" />
          <div>
            <span>
              <strong>Đã duyệt</strong>
              {approval.reviewer ? ` · ${approval.reviewer}` : ''}
              {approvalTime ? ` · ${approvalTime}` : ''}
            </span>
            {approval.reason && (
              <p className="question-approved-reason">Lý do xác nhận: {approval.reason}</p>
            )}
            {approval.originalCheck && approval.originalCheck.answerCheck !== 'matched' && (
              <p className="question-approved-origin">
                Đối chiếu ban đầu: Dự kiến {approval.originalCheck.writerKey || question.key}
                {approval.originalCheck.solverKey ? ` · Giải độc lập ${approval.originalCheck.solverKey}` : ' · Chưa có kết quả Solver'}
              </p>
            )}
          </div>
        </div>
      )}

      {review && confirmingApprove && !approval && onApprove && (
        <form className="question-approve-form" onSubmit={event => { void handleConfirmReasonApprove(event); }}>
          <label className="question-approve-form-label" htmlFor={`approve-reason-${question.id}`}>
            Đáp án dự kiến chưa khớp kết quả giải độc lập. Nhập lý do xác nhận để duyệt câu:
          </label>
          <textarea
            id={`approve-reason-${question.id}`}
            rows={2}
            value={approveReason}
            onChange={event => {
              setApproveReason(event.target.value);
              if (approveReasonError) setApproveReasonError('');
            }}
            placeholder="Ví dụ: Đáp án 0,67 đúng theo yêu cầu làm tròn của đề..."
          />
          {approveReasonError && <p className="question-approve-error" role="alert">{approveReasonError}</p>}
          <div className="question-approve-form-actions">
            <button type="submit" className="button-primary" disabled={approving}>
              {approving ? 'Đang duyệt...' : 'Xác nhận duyệt câu'}
            </button>
            <button
              type="button"
              className="button-secondary"
              disabled={approving}
              onClick={() => { setConfirmingApprove(false); setApproveReasonError(''); }}
            >
              Hủy
            </button>
          </div>
        </form>
      )}

      {flagged && !approval && (
        <p className="question-answer-warning">
          <AlertTriangle size={16} aria-hidden="true" />
          <span>
            <strong>Cảnh báo lệch đáp án.</strong>{' '}
            {question.mismatchedStatements?.length
              ? `Khác kết quả giải độc lập ở ý ${question.mismatchedStatements.join(', ')}.`
              : 'Đáp án dự kiến khác kết quả giải độc lập.'}{' '}
            Thầy cô kiểm tra và sửa hoặc ghi lý do xác nhận trước khi duyệt câu.
          </span>
        </p>
      )}

      {question.figures?.map(figure => (
        figure.mimeType === 'application/pdf'
          ? <iframe key={figure.url} loading="lazy" title={figure.alt} src={figure.url} width="100%" height="240" />
          : <img key={figure.url} className="contract-question-figure" loading="lazy" alt={figure.alt} src={figure.url} />
      ))}
      {!question.figures?.length && question.drawingLatex && (
        <details className="question-drawing-details">
          <summary>Hình minh họa (xem trực quan ở mục Xem trước PDF)</summary>
          <pre>{question.drawingLatex}</pre>
        </details>
      )}
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
          {question.statements?.map((statement, i) => {
            const letter = 'abcd'[i];
            const statementMismatched = Boolean(review && question.mismatchedStatements?.includes(letter));
            return (
              <div key={i} className={`question-choice question-tf-row ${statementMismatched ? 'is-mismatched' : ''}`}>
                <strong>{letter})</strong>
                <MathRenderer content={statement.text} />
                {statementMismatched && (
                  <span className="tf-mismatch-pill">Lệch ở ý {letter}</span>
                )}
                {review && (
                  <span className={`tf-answer-pill ${statement.answer ? 'is-true' : 'is-false'}`}>
                    {statement.answer ? 'Đúng' : 'Sai'}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
      {question.questionType === 'short_answer' && (review || !question.responseKind) && (
        <div className="question-short-answer">
          <span>Đáp án:</span>
          {review ? (
            <strong className="short-answer-value">{question.key}</strong>
          ) : (
            <span className="short-answer-boxes" aria-label={`${question.maxAnswerCharacters ?? 5} ô điền đáp án`}>
              {Array.from({ length: question.maxAnswerCharacters ?? 5 }, (_, idx) => (
                <span key={idx} className="short-answer-cell" aria-hidden="true" />
              ))}
            </span>
          )}
        </div>
      )}
      {review && (
        <details
          ref={detailsRef}
          className={`question-review ${flagged ? 'flagged' : ''}`}
        >
          <summary>
            {flagged ? (
              <span>Xem đối chiếu · Hai đáp án khác nhau</span>
            ) : matched ? (
              <><CheckCircle2 size={14} aria-hidden="true" /><span>Xem đối chiếu · Khớp đáp án</span></>
            ) : (
              <span>Xem đối chiếu · Cần kiểm tra lại</span>
            )}
          </summary>
          <div className="review-content">
            <p><strong>{matched ? 'Đáp án' : 'Đáp án dự kiến'}:</strong> {question.writerKey || question.key}</p>
            {question.solverKey && <p><strong>Giải độc lập:</strong> {question.solverKey}</p>}
            {!matched && <p>{getPrimaryReviewReason(question)}</p>}
            {sourceNotes.length > 0 && (
              <details className="review-secondary-notes">
                <summary>Lưu ý nguồn hoặc hình/bảng ({sourceNotes.length})</summary>
                <ul>
                  {sourceNotes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              </details>
            )}
            {question.explanation && <div className="review-explanation"><MathRenderer content={question.explanation} /></div>}
            {question.sourceReference && <p className="review-source">Nguồn: {question.sourceReference}</p>}
            <div className="review-content-actions">
              {onEdit && <button type="button" className="button-secondary" onClick={onEdit}>Sửa câu hỏi</button>}
              {onVerify && (
                <button
                  type="button"
                  className="button-secondary"
                  disabled={verifying || approving}
                  onClick={onVerify}
                >
                  {verifying ? 'Đang giải lại...' : 'Giải kiểm tra lại'}
                </button>
              )}
              {!approval && onApprove && (
                <button
                  type="button"
                  className="button-primary"
                  disabled={approving || verifying}
                  onClick={() => { void handleApproveClick(); }}
                >
                  {approving ? 'Đang duyệt...' : 'Duyệt câu'}
                </button>
              )}
            </div>
          </div>
        </details>
      )}
    </section>
  );
};
