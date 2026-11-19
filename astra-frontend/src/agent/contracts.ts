export type CapabilityStatus = 'available_real' | 'available_mock' | 'unavailable' | 'planned';

export interface UiCapabilitySummary {
  id: string;
  description: string;
  status: CapabilityStatus;
  callable: boolean;
  requiresConfirmation: boolean;
}

export interface DeferredAgentNote {
  id: string;
  workspaceId: string;
  jobId: string | null;
  targetQuestion: number | null;
  stableQuestionId: string | null;
  examId: string | null;
  examRevision: number | null;
  requestedChange: string;
  teacherText: string;
  status: 'pending' | 'approved' | 'applying' | 'applied' | 'failed' | 'cancelled';
  appliedRevision?: number;
  errorCode?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ExamSetupSnapshot {
  status: 'closed' | 'loading' | 'ready' | 'error';
  selectedFormatId: string | null;
  prompt: string;
  formats: {
    id: string;
    version: string;
    displayName: string;
    subject: string;
    grade: number;
    durationMinutes: number;
    totalQuestions: number;
    available: boolean;
  }[];
  errorCode?: string;
}

export interface PendingAgentConfirmation {
  id: string;
  kind: 'generation' | 'revision' | 'approval';
  workspaceId: string;
  summary: string;
  noteId?: string;
  createdAt: string;
}

export interface AgentTaskStep {
  stepId: string;
  capabilityId: string;
  params: Record<string, unknown>;
  target: Record<string, unknown>;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  receipt?: UiExecutionReceipt;
}

export interface AgentTaskState {
  taskId: string;
  workspaceId: string | null;
  teacherGoal: string;
  taskStatus: 'planning' | 'executing' | 'awaiting_confirmation' | 'completed' | 'blocked' | 'cancelled';
  plan: AgentTaskStep[];
  currentStep: number;
  completedSteps: string[];
  pendingSteps: string[];
  pendingConfirmation: PendingAgentConfirmation | null;
  lastExecutionReceipt: UiExecutionReceipt | null;
  lastObservedStateVersion: number;
  blockingReason: string | null;
  relatedJobId: string | null;
  relatedExamId: string | null;
  relatedRevisionId: number | null;
  replanAttempts: number;
  updatedAt: string;
}

export interface UiContextSnapshot {
  workspaceId: string | null;
  screen: 'start' | 'workspace';
  activeModal: 'exam_setup' | 'question_editor' | null;
  sidebarCollapsed: boolean;
  stateVersion: number;
  activeJob: { id: string; stage: string; percent: number; source: 'real' | 'mock' | 'unknown' } | null;
  examRevision: number | null;
  examId: string | null;
  contentHash: string | null;
  selectedQuestion: { id: number; stableId: string | null } | null;
  questions: { id: number; stableId: string | null }[];
  viewMode: 'paper' | 'review' | 'pdf';
  preview: { status: string; revision: number | null; opened: boolean } | null;
  approved: boolean;
  setup: ExamSetupSnapshot;
  pendingConfirmation: PendingAgentConfirmation | null;
  activeTask: AgentTaskState | null;
  sessions: { id: string; title: string; status: 'draft' | 'generating' | 'complete' | 'error'; createdAt: string }[];
  notes: { id: string; targetQuestion: number | null; stableQuestionId: string | null; requestedChange: string; status: DeferredAgentNote['status'] }[];
  capabilities: UiCapabilitySummary[];
}

export interface UiActionProposal {
  kind: 'propose_ui_action';
  text: string;
  actionId: string;
  capabilityId: string;
  expectedStateVersion: number;
  params: Record<string, unknown>;
  target: Record<string, unknown>;
}

export type AgentDecision =
  | { kind: 'answer' | 'clarify' | 'unsupported'; text: string }
  | UiActionProposal;

export interface AgentTurnResponse {
  turnId: string;
  decisions: AgentDecision[];
  provider: 'offline' | 'gemini';
  knowledgeStatus: 'verified_ui_registry_only' | 'approved_document';
}

export interface UiExecutionReceipt {
  actionId: string;
  capabilityId: string;
  status: 'success' | 'failed' | 'skipped' | 'cancelled';
  observedStateVersion: number;
  errorCode?: string;
  result?: Record<string, unknown>;
  duplicate?: boolean;
}
