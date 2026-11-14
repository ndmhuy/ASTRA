/**
 * PROPOSED v0.1 reference interfaces. NOT imported by the application.
 * No transport, runtime schema validator, UI executor, or approval service is implemented here.
 * Source domain shapes are current frontend types, not authoritative backend requirements.
 */
import type { ExamRequestParams } from '../astra-frontend/src/types/exam';

export type ScreenId = 'splash' | 'welcome' | 'create' | 'library' | 'workspace';
export type SessionStatus = 'draft' | 'generating' | 'complete' | 'error';
export type PanelId = 'exam-setup' | 'generation-confirmation';
export type FocusTargetId = 'chat-composer' | 'exam-canvas' | 'exam-setup' | 'main-navigation';

export interface JobSnapshot {
  jobId: string;
  revision: number;
  // The first four align to present session states; later statuses require store/transport work.
  status: 'generating' | 'complete' | 'error' | 'disconnected' | 'unknown' | 'cancelled';
  completedItems: number;
  totalItems: number;
  visibleQuestionCount: number;
  flaggedQuestionCount: number;
  stage: number | null;
  percent: number | null;
  estimatedSecondsLeft: number | null;
  // Store full stream snapshot before populating the nullable progress fields above.
}

export interface ScreenContext {
  screenId: ScreenId;
  stateVersion: number;
  activeWorkspaceSessionId: string | null; // App activeId, validated against store
  visibleWorkspaceSessionId: string | null; // null off the workspace screen
  activeExamId: string | null; // retain package.examId first; do not substitute jobId
  activeSessionStatus: SessionStatus | null;
  selectedQuestionId: number | null;
  focusedComponentId: FocusTargetId | null;
  openPanels: PanelId[];
  sidebarCollapsed: boolean; // effective visual state, false in top-menu mobile layout
  viewport: 'desktop' | 'mobile'; // breakpoint <=760px
  canvasView: 'exam' | 'answers' | null;
  mobilePane: 'chat' | 'paper' | null;
  availableActions: CapabilityId[];
  activeJob: JobSnapshot | null;
}

export interface AgentTurnRequest {
  schemaVersion: '0.1';
  requestId: string; // stable across a retry of the same submitted message
  sessionId: string; // conversation ID, not a generation job ID
  workspaceSessionId: string | null; // target pinned when the teacher submits
  message: string;
  screenContext: ScreenContext;
  options: {
    searchWeb: boolean; // requested preference, not evidence of a completed search
    uploadedFileIds: string[]; // backend-issued IDs only; no File objects/local paths
  };
}

export interface PendingGeneration {
  pendingRequestId: string;
  sessionId: string;
  workspaceSessionId: string;
  requirementsSchemaVersion: string;
  requestHash: string;
  expiresAt: string; // ISO timestamp; server authoritative
  normalizedRequest: ExamRequestParams; // map through backend-approved schema adapter
  validation: { status: 'valid'; validatedBy: 'backend' };
}

// Created only from trusted UI interaction and verified by server/adapter.
// The model MUST NOT create this object or treat a bare boolean as proof of approval.
export interface GenerationApproval {
  approvalId: string;
  approvedRequestId: string;
  sessionId: string;
  workspaceSessionId: string;
  requestHash: string;
  requirementsSchemaVersion: string;
  approvedAt: string;
  expiresAt: string;
}

export type ConfirmationEvent = {
  schemaVersion: '0.1';
  requestId: string;
  sessionId: string;
  workspaceSessionId: string;
  pendingRequestId: string;
  requestHash: string;
  decision: 'approve' | 'edit' | 'cancel';
  screenContext: ScreenContext;
};
// Any edit submits a new draft for backend validation and invalidates old approvals.

export type ConfirmationResolution =
  | { status: 'approved'; approval: GenerationApproval }
  | { status: 'cancelled' | 'edit_requested'; approval?: never };
export interface ConfirmationFeedback {
  schemaVersion: '0.1';
  feedbackId: string;
  sessionId: string;
  originalRequestId: string;
  pendingRequestId: string;
  decision: 'approve' | 'edit' | 'cancel';
  approvedRequestId: string | null; // reference only, not approval credentials
  screenContext: ScreenContext; // refresh after recording the approval/resolution
}

interface CapabilitySpec {
  'ui.navigate': {
    target: 'application';
    params:
      | { screenId: 'welcome' | 'create' | 'library' }
      | { screenId: 'workspace'; workspaceSessionId: string };
  };
  'ui.session.create': { target: 'exam-sessions'; params: { mode: 'template' | 'custom' } };
  'ui.exam.open_setup': { target: 'exam-setup'; params: { workspaceSessionId: string } };
  'ui.sidebar.set_collapsed': { target: 'main-navigation'; params: { collapsed: boolean } };
  'exam.generate': {
    target: 'exam-generation';
    params: { workspaceSessionId: string; approvedRequestId: string };
  };
}
export type CapabilityId = keyof CapabilitySpec;
export type UiAction = {
  [K in CapabilityId]: { id: string; capabilityId: K } & CapabilitySpec[K]
}[CapabilityId];

export interface ActionPlan {
  schemaVersion: '0.1';
  registryVersion: 'astra-ui-0.1-proposal-1';
  requestId: string;
  planId: string;
  sessionId: string;
  expectedStateVersion: number;
  actions: UiAction[]; // runtime limit 1..5; no duplicate action IDs
  // Hint only: executor derives the actual requirement from registry + trusted approvals.
  requiresUserConfirmation: boolean;
}

interface AgentResponseBase {
  schemaVersion: '0.1';
  requestId: string;
  sessionId: string;
  reply: string;
}
export type AgentTurnResponse = AgentResponseBase & (
  | { kind: 'reply' | 'clarification'; plan?: never; pendingGeneration?: never }
  | { kind: 'confirmation'; pendingGeneration: PendingGeneration; plan?: never }
  | { kind: 'action_plan'; plan: ActionPlan; pendingGeneration?: never }
);

export type ActionErrorCode =
  | 'UNSUPPORTED_SCHEMA' | 'UNKNOWN_CAPABILITY' | 'INVALID_PARAMS'
  | 'STALE_CONTEXT' | 'SESSION_NOT_FOUND' | 'QUESTION_NOT_FOUND'
  | 'CAPABILITY_UNAVAILABLE' | 'PERMISSION_DENIED'
  | 'CONFIRMATION_REQUIRED' | 'CONFIRMATION_EXPIRED' | 'JOB_ALREADY_RUNNING'
  | 'BACKEND_VALIDATION_FAILED' | 'BACKEND_UNAVAILABLE'
  | 'START_OUTCOME_UNKNOWN' | 'ACTION_FAILED';
export interface ActionError { code: ActionErrorCode; message: string; retryable: boolean }

export interface ExecutionResult {
  schemaVersion: '0.1';
  sessionId: string;
  requestId: string;
  planId: string;
  actionId: string;
  status: 'success' | 'failed' | 'skipped' | 'pending_user_confirmation';
  updatedScreenContext: ScreenContext;
  data: {
    createdWorkspaceSessionId?: string;
    workspaceSessionId?: string;
    jobId?: string;
    noOp?: boolean;
  };
  error: ActionError | null;
  // Runtime invariant: failed => error; success => error=null.
  // skipped explains dependency failure; pending_user_confirmation uses CONFIRMATION_REQUIRED.
}

export interface PlanExecutionReport {
  schemaVersion: '0.1';
  requestId: string;
  sessionId: string;
  planId: string;
  status: 'success' | 'failed' | 'pending_user_confirmation';
  results: ExecutionResult[];
  finalScreenContext: ScreenContext;
}

export interface ExecutionFeedback {
  schemaVersion: '0.1';
  feedbackId: string; // deduplicate receipt delivery retries
  sessionId: string;
  originalRequestId: string;
  report: PlanExecutionReport;
}

export interface UiExecutionAdapter {
  getContext(): ScreenContext;
  // Must validate again, execute serially, and wait for committed state before acknowledging.
  executePlan(plan: ActionPlan, trustedApprovals: readonly GenerationApproval[]): Promise<PlanExecutionReport>;
}

export interface ConversationalAgentAdapter {
  // Illustrative transport: POST /agent/turns. Endpoint does not exist in this frontend.
  sendTurn(request: AgentTurnRequest, signal?: AbortSignal): Promise<AgentTurnResponse>;
  // Illustrative transport: POST /agent/execution-results. No automatic tool loop implied.
  reportExecution(feedback: ExecutionFeedback, signal?: AbortSignal): Promise<AgentTurnResponse>;
  // Illustrative transport: POST /agent/confirmation-results, AFTER trusted resolution.
  reportConfirmation(feedback: ConfirmationFeedback, signal?: AbortSignal): Promise<AgentTurnResponse>;
}

export interface GenerationApprovalAdapter {
  // Backend verifies the pending request and trusted UI decision; the LLM is not the issuer.
  // Illustrative backend endpoint: POST /generation-requests/{id}/confirmation.
  resolveConfirmation(event: ConfirmationEvent, signal?: AbortSignal): Promise<ConfirmationResolution>;
}

export interface GenerationStartReceipt {
  workspaceSessionId: string;
  approvedRequestId: string;
  jobId: string;
  acceptedAt: string;
}
export interface GenerationAdapter {
  // Designated sole starter. Current ExamSessions.generate does not yet implement this signature.
  startApproved(approval: GenerationApproval, idempotencyKey: string): Promise<GenerationStartReceipt>;
}
