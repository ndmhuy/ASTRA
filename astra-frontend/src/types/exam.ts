/** Backend-adapted UI contracts. Display numbers are separate from stable MAS IDs. */
export type Subject = 'Tổng hợp' | 'Vật Lý' | 'Toán Học' | 'Hóa Học' | 'Sinh Học' | 'Tiếng Anh' | 'Lịch Sử' | 'Địa Lý' | 'GDCD / KTPL';
export type ExamType = 'THPT_STANDARD' | 'DGNL_DHQG' | 'MID_TERM' | 'CUSTOM';
export type CognitiveLevel = 'NHAN_BIET' | 'THONG_HIEU' | 'VAN_DUNG' | 'VAN_DUNG_CAO';
export type VerificationStatus = 'PENDING' | 'VERIFIED' | 'FLAGGED';
export type ExportFormat = 'docx' | 'pdf' | 'tex' | 'json';
export interface QuestionChoices { A: string; B: string; C: string; D: string; }
export interface QuestionStatement { text: string; answer: boolean; solution: string; }
export interface QuestionItem {
  id: number;
  stableId?: string;
  examRevision?: number;
  part?: 'P1' | 'P2' | 'P3';
  questionType?: 'mcq' | 'true_false' | 'short_answer';
  stem: string;
  choices: QuestionChoices;
  statements?: QuestionStatement[];
  key: string;
  explanation: string;
  level: CognitiveLevel;
  topic: string;
  sourceReference?: string;
  status: VerificationStatus;
  writerKey?: string;
  solverKey?: string;
  revisionCount?: number;
  auditNotes?: string;
  drawingLatex?: string;
}
export interface ExamBlueprint {
  subject: Subject; grade: number; examType: ExamType; title: string;
  totalQuestions: number; durationMinutes: number;
  levelDistribution: { nhanBiet: number; thongHieu: number; vanDung: number; vanDungCao: number; };
  topics: string[];
}
export interface ExamPackage {
  examId: string; title: string; subject: Subject; grade: number;
  durationMinutes: number; totalScore: number; createdAt: string;
  blueprint: ExamBlueprint; questions: QuestionItem[];
  revision?: number; contentHash?: string; approved?: boolean;
  warnings?: { code: string; message: string; questionId?: string }[];
  gaps?: { code: string; message: string }[];
  provenance?: Record<string, unknown>;
}
export interface ExamRequestParams {
  subject: Subject; grade: number; examType: ExamType; durationMinutes: number;
  itemCount: number; prompt: string; uploadedFiles: string[];
  formatId?: string; formatVersion?: string; clientRequestId?: string;
}
export interface GenerationProgress {
  stage: number; stageName: string; percent: number; estimatedSecondsLeft: number;
  completedItems: number; totalItems: number; statusMessage: string;
  latestItemPreview?: QuestionItem;
  status?: 'queued' | 'running' | 'completed' | 'failed';
  error?: { code: string; message: string; details?: unknown };
}
export interface ChatMessage { id: string; role: 'user' | 'assistant' | 'system'; content: string; timestamp: string; }
export interface ExamFormat {
  id: string; version: string; displayName: string; examType: ExamType;
  subjects: Subject[]; grades: number[]; durationMinutes: number; totalQuestions: number;
  totalScore: number; available: boolean; exportFormats: ExportFormat[];
  sections: { id: string; type: string; count: number; instructions: string }[];
}
