import React from 'react';
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

export const ExamPaperView: React.FC<ExamPaperViewProps> = ({
  questions,
  examMeta,
  isGenerating,
  latestQuestionCount = 0,
  onEditQuestion,
}) => {
  return (
    <div
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px 24px',
      }}
    >
      {/* Exam Paper Header */}
      {examMeta && (
        <div
          style={{
            textAlign: 'center',
            marginBottom: 24,
            paddingBottom: 16,
            borderBottom: '1px solid #e2e8f0',
          }}
        >
          <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>
            TRƯỜNG THPT — Năm học 2025–2026
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>
            {examMeta.title || `ĐỀ KIỂM TRA MÔN ${examMeta.subject.toUpperCase()}`}
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 24, fontSize: 13, color: '#334155', flexWrap: 'wrap' }}>
            <span>Môn: <strong>{examMeta.subject}</strong></span>
            <span>Thời gian: <strong>{examMeta.duration} phút</strong></span>
            <span>Số câu: <strong>{examMeta.totalCount}</strong></span>
          </div>
        </div>
      )}

      {/* Questions */}
      {questions.length === 0 && !isGenerating && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '60px 20px',
            color: '#94a3b8',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 12 }}>📄</div>
          <p style={{ fontSize: 14, lineHeight: 1.6 }}>
            Đề thi sẽ hiển thị ở đây khi quá trình tạo bắt đầu.
          </p>
        </div>
      )}

      {questions.map((q, i) => {
        // Questions added after the previous snapshot are "appearing"
        const isNew = i >= latestQuestionCount;
        return (
          <QuestionCard
            key={q.id}
            question={q}
            index={i}
            appearing={isNew}
            onEdit={onEditQuestion ? () => onEditQuestion(q.id) : undefined}
          />
        );
      })}

      {/* Generating indicator */}
      {isGenerating && (
        <div
          style={{
            textAlign: 'center',
            padding: '16px 0 8px',
            fontSize: 13,
            color: '#64748b',
          }}
        >
          Đang tạo câu tiếp theo…
        </div>
      )}
    </div>
  );
};
