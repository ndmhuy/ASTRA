import React, { useState } from 'react';
import { StationeryArt } from '../../StationeryArt';
import { SchoolArt } from '../../SchoolArt';
import type { QuestionItem } from '../../../types/exam';
import { QuestionCard } from './QuestionCard';

interface ExamPaperViewProps {
  questions: QuestionItem[];
  examMeta: {
    title: string;
    subject: string;
    duration: number;
    completedCount: number;
    totalCount: number;
  } | null;
  isGenerating: boolean;
  latestQuestionCount?: number;
  onEditQuestion?: (questionId: number) => void;
}

export const ExamPaperView: React.FC<ExamPaperViewProps> = ({ questions, examMeta, isGenerating, latestQuestionCount = 0, onEditQuestion }) => {
  const [review, setReview] = useState(false);
  const flaggedCount = questions.filter(q => q.status === 'FLAGGED').length;
  return <>
    <div className="paper-toolbar">
      <div className="view-switch" role="group" aria-label="Chế độ xem đề thi">
        <button aria-pressed={!review} onClick={() => setReview(false)}>Đề thi</button>
        <button aria-pressed={review} onClick={() => setReview(true)}>Xem đáp án</button>
      </div>
      {flaggedCount > 0 && <button className="review-count" onClick={() => setReview(true)}>{flaggedCount} câu cần xem xét</button>}
    </div>
    <div className="paper-scroll">
      <article className={`exam-paper ${!examMeta ? 'is-empty' : ''}`}>
        {examMeta ? <header className="exam-paper-heading">
          <div className="eyebrow">Đề kiểm tra · {examMeta.subject}</div>
          <h1>{examMeta.title || `Đề thi ${examMeta.subject}`}</h1>
          <p>Thời gian: {examMeta.duration} phút <span>·</span> {examMeta.totalCount} câu hỏi</p>
          {!review && <div className="student-line">Họ và tên: ................................................ <span>Lớp: ................</span></div>}
        </header> : <div className="paper-empty">
          <StationeryArt kind="pencil" className="preview-pencil" /><StationeryArt kind="apple" className="preview-apple" /><span className="preview-label">02 / TRANG ĐỀ</span><SchoolArt kind="book" className="preview-art" />
          <h2>Một trang mới,<br />chờ ý tưởng hay.</h2>
          <p>Trao đổi với ASTRA, chọn thiết lập đề, rồi xem từng câu hỏi xuất hiện tại đây.</p>
        </div>}
        {questions.map((q, i) => <QuestionCard key={q.id} question={q} index={i} review={review} appearing={i >= latestQuestionCount} onEdit={onEditQuestion ? () => onEditQuestion(q.id) : undefined} />)}
        {isGenerating && <p className="paper-progress" role="status">Đang soạn câu hỏi tiếp theo…</p>}
        {questions.length > 0 && !isGenerating && <footer className="paper-end">— Hết —</footer>}
      </article>
    </div>
  </>;
};
