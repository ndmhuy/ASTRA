import type { StudentPaper } from '../services/contractPaper';

/** Backend-adapted UI contracts. Display numbers are separate from stable MAS IDs. */
export type Subject = 'Tổng hợp' | 'Vật Lý' | 'Toán Học' | 'Hóa Học' | 'Sinh Học' | 'Tiếng Anh' | 'Lịch Sử' | 'Địa Lý' | 'GDCD / KTPL' | 'SAT' | 'IELTS' | 'TOEIC' | 'TOEFL' | 'ACT';
export type ExamType = 'THPT_STANDARD' | 'DGNL_DHQG' | 'MID_TERM' | 'CUSTOM';
export type CognitiveLevel = 'NHAN_BIET' | 'THONG_HIEU' | 'VAN_DUNG' | 'VAN_DUNG_CAO';
export type VerificationStatus = 'PENDING' | 'VERIFIED' | 'FLAGGED';
export type AnswerCheck = 'matched' | 'mismatched' | 'needs_recheck';
export type ExportFormat = 'docx' | 'pdf' | 'tex' | 'json' | 'md';
export interface QuestionApproval {
  questionId: string;
  questionHash?: string;
  revision: number;
  reviewer: string;
  approvedAt: string;
  reason?: string;
  originalCheck?: {
    answerCheck?: AnswerCheck;
    writerKey?: string | null;
    solverKey?: string | null;
    auditNotes?: string;
  };
}
export interface QuestionChoices { A: string; B: string; C: string; D: string; }
export interface QuestionStatement { text: string; answer: boolean; solution: string; }
export interface QuestionItem {
  id: number;
  stableId?: string;
  examRevision?: number;
  part?: string;
  questionType?: 'mcq' | 'true_false' | 'short_answer';
  passageId?: string | null;
  groupInstruction?: string;
  stem: string;
  choices: QuestionChoices;
  statements?: QuestionStatement[];
  key: string;
  explanation: string;
  level: CognitiveLevel;
  topic: string;
  sourceReference?: string;
  status: VerificationStatus;
  answerCheck?: AnswerCheck;
  writerKey?: string | null;
  solverKey?: string | null;
  revisionCount?: number;
  auditNotes?: string;
  mismatchedStatements?: string[];
  questionApproval?: QuestionApproval | null;
  drawingLatex?: string;
  responseKind?: 'numeric' | 'digit_sequence';
  maxAnswerCharacters?: number;
  figures?: { url: string; mimeType: string; alt: string }[];
}
export interface ExamBlueprint {
  subject: Subject; grade: number; examType: ExamType; title: string;
  totalQuestions: number; durationMinutes: number;
  levelDistribution: { nhanBiet: number; thongHieu: number; vanDung: number; vanDungCao: number; };
  topics: string[];
}
export type ExamPreviewStatus =
  | 'not_requested'
  | 'unavailable'
  | 'queued'
  | 'compiling'
  | 'ready'
  | 'failed';

export interface ExamPreviewState {
  status: ExamPreviewStatus;
  revision: number;
  contentHash: string;
  sourceHash: string;
  compilerAvailable: boolean;
  draft: boolean;
  statusUrl: string;
  pdfUrl: string;
  logUrl: string;
  pageCount?: number;
  pdfHash?: string;
  error?: string;
}

export interface VisualWarning {
  questionId: string;
  code: string;
}

export interface ExamPassageTable {
  columns: string[];
  rows: string[][];
}

export interface ExamPassage {
  id: string;
  section: 'TV' | 'TA' | 'TO' | 'LOGIC' | 'SCIENCE' | 'P1' | 'P2' | 'P3';
  kind:
    | 'passage'
    | 'vact_passage_en'
    | 'math_context'
    | 'logic_puzzle'
    | 'data_set'
    | 'science';
  questionRange: [number, number];
  instruction: string;
  heading?: string;
  text: string;
  table?: ExamPassageTable | null;
}

export interface ExamPackage {
  examId: string; title: string; subject: Subject; grade: number;
  durationMinutes: number; totalScore: number | null; createdAt: string;
  blueprint: ExamBlueprint; questions: QuestionItem[];
  passages?: ExamPassage[];
  studentPaper?: StudentPaper;
  revision?: number; contentHash?: string; approved?: boolean;
  approval?: { revision: number; contentHash: string; reviewer: string; approvedAt: string } | null;
  preview?: ExamPreviewState;
  hasDrawings?: boolean;
  visualWarnings?: VisualWarning[];
  warnings?: { code: string; message: string; questionId?: string }[];
  gaps?: { code: string; message: string }[];
  provenance?: Record<string, unknown>;
}

export interface ExamVersionSummary {
  jobId?: string;
  revision: number;
  createdAt: string;
  change: 'generated' | 'baseline' | 'edited' | 'regenerated' | 'restored' | 'undone' | 'branched';
  questionId: number | null;
  restoredFrom: number | null;
  restorable: boolean;
}

export interface ExamHistory {
  list(jobId: string, workspaceId?: string): Promise<{ currentJobId?: string; currentRevision: number; versions: ExamVersionSummary[] }>;
  read(jobId: string, version: number): Promise<ExamPackage>;
  restore(jobId: string, version: number, revision: number, workspaceId?: string, targetJobId?: string): Promise<ExamPackage>;
}

export interface WebSearchSource {
  title: string;
  url: string;
  snippet: string;
}

export interface WebResearchResult {
  schemaVersion: 'astra-web-research-v1';
  clientMessageId: string;
  adjacentTopicId: string;
  topicLabel: string;
  formatId: string;
  subject: Subject;
  summary: string;
  suggestedCount: number;
  suggestedMinutes: number;
  sources: WebSearchSource[];
  searchMode: 'live_web' | 'offline_fallback';
}

export interface ExamRequestParams {
  subject: Subject; grade: number; examType: ExamType; durationMinutes: number;
  itemCount: number; prompt: string; uploadedFiles: string[];
  formatId?: string; formatVersion?: string; clientRequestId?: string;
  adjacentTopicId?: string;
  webSources?: WebSearchSource[];
}
export interface GenerationProgress {
  stage: number; stageName: string; percent: number; estimatedSecondsLeft: number;
  completedItems: number; totalItems: number; statusMessage: string;
  latestItemPreview?: QuestionItem;
  jobId?: string;
  executionVersion?: number;
  checkpointVersion?: number;
  completedOperations?: number;
  resumeAvailable?: boolean;
  connectionLost?: boolean;
  retryNotBefore?: number;
  retry?: { attempt: number; maxAttempts: number; category: string; phase: string; retryAt?: number } | null;
  status?: 'queued' | 'running' | 'pausing' | 'paused' | 'resuming' | 'retrying' | 'interrupted' | 'completed' | 'failed' | 'cancelled';
  error?: { code: string; message: string; details?: unknown };
}
export interface ExamVersionReference { jobId: string; revision: number; }
export interface ChatMessage {
  id: string; role: 'user' | 'assistant' | 'system'; content: string; timestamp: string;
  agentTurn?: boolean;
  examVersion?: ExamVersionReference | null;
  recorded?: boolean;
  changeId?: string;
}
export interface ExamFormat {
  id: string; version: string; displayName: string; examType: ExamType;
  subjects: Subject[]; grades: number[]; durationMinutes: number; totalQuestions: number;
  totalScore: number | null; available: boolean; exportFormats: ExportFormat[];
  sections: {
    id: string;
    title?: string;
    type: string;
    count: number;
    questionRange?: [number, number];
    instructions: string;
  }[];
}
