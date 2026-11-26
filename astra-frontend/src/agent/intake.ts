import type { ExamFormat, ExamRequestParams } from '../types/exam.ts';
import type { Intent } from './contracts.ts';
import { fold } from './recipes.ts';

export type Intake = {
  sourceId: string;
  formatId: string;
  version: string;
  topic?: string;
  phase: 'selected' | 'evaluated' | 'confirmed';
};

export function presetParams(format: ExamFormat, topic?: string): ExamRequestParams {
  return {
    formatId: format.id, formatVersion: format.version, subject: format.subjects[0],
    grade: format.grades[0], examType: format.examType, durationMinutes: format.durationMinutes,
    itemCount: format.totalQuestions, prompt: `Tạo đề ${format.displayName}${topic ? `\nChuyên đề: ${topic}` : ''}`,
    uploadedFiles: [],
  };
}

export function prepareParams(format: ExamFormat, args: Intent['args'], message: string) {
  const text = fold(message);
  const statedCount = /\b(\d+)\s*cau\b/.exec(text)?.[1];
  const statedMinutes = /\b(\d+)\s*phut\b/.exec(text)?.[1];
  if ([args.count, statedCount].some(value => value !== undefined && Number(value) !== format.totalQuestions) ||
      [args.minutes, statedMinutes].some(value => value !== undefined && Number(value) !== format.durationMinutes)) {
    return { error: `Mẫu ${format.displayName} cố định ${format.totalQuestions} câu, ${format.durationMinutes} phút. Thầy cô muốn dùng cấu trúc này hay chọn mẫu khác?` };
  }
  const topic = typeof args.topic === 'string' ? args.topic.trim() : undefined;
  if (topic && (!text.includes(fold(topic)) || /\p{Cc}/u.test(topic))) {
    return { error: 'Thầy cô hãy ghi rõ tên chuyên đề theo nội dung muốn ra đề.' };
  }
  if (format.id === 'vact' && topic) {
    return { error: 'Mẫu V-ACT có đủ năm lĩnh vực cố định. Thầy cô có muốn giữ nguyên cấu trúc của mẫu này?' };
  }
  return { params: presetParams(format, topic), topic };
}
