import type { ExamFormat, ExamRequestParams } from '../types/exam.ts';
import type { Intent } from './contracts.ts';
import { fold } from './recipes.ts';

export type Intake = {
  sourceId: string;
  formatId?: string;
  version?: string;
  family?: 'thpt' | 'vact' | 'custom';
  subject?: string;
  sourceIds?: string[];
  grade?: number;
  count?: number;
  minutes?: number;
  missing?: 'family' | 'subject';
  validation?: 'passed' | 'failed';
  topic?: string;
  difficulty?: string;
  requirements?: string;
  sourcePreference?: 'attachments' | 'web' | 'default';
  documentIds?: string[];
  provenance?: Record<string, string>;
  visible?: boolean;
  phase: 'collecting' | 'selected' | 'evaluated' | 'confirmed';
};

export function presetParams(format: ExamFormat, topic?: string): ExamRequestParams {
  return {
    formatId: format.id, formatVersion: format.version, subject: format.subjects[0],
    grade: format.grades[0], examType: format.examType, durationMinutes: format.durationMinutes,
    itemCount: format.totalQuestions, prompt: `Tạo đề ${format.displayName}${topic ? `\nChuyên đề: ${topic}` : ''}`,
    uploadedFiles: [],
  };
}

export function prepareParams(format: ExamFormat, args: Intent['args'], message: string, groundedTopic?: string) {
  const text = fold(message);
  const statedCount = /\b(\d+)\s*cau\b/.exec(text)?.[1];
  const statedMinutes = /\b(\d+)\s*phut\b/.exec(text)?.[1];
  if ([args.count, statedCount].some(value => value !== undefined && Number(value) !== format.totalQuestions) ||
      [args.minutes, statedMinutes].some(value => value !== undefined && Number(value) !== format.durationMinutes)) {
    return { error: `Mẫu ${format.displayName} cố định ${format.totalQuestions} câu, ${format.durationMinutes} phút. Thầy cô có thể chọn mẫu này trong phần cấu hình hoặc gửi lại yêu cầu với thông số phù hợp.` };
  }
  const topic = typeof args.topic === 'string' ? args.topic.trim() : undefined;
  if (topic && ((topic !== groundedTopic && !text.includes(fold(topic))) || /\p{Cc}/u.test(topic))) {
    return { error: 'Thầy cô hãy ghi rõ tên chuyên đề theo nội dung muốn ra đề.' };
  }
  if (format.id === 'vact' && topic) {
    return { error: 'Mẫu V-ACT có đủ năm lĩnh vực cố định. Thầy cô có thể gửi lại yêu cầu tạo đề V-ACT theo cấu trúc chuẩn.' };
  }
  return { params: presetParams(format, topic), topic };
}
