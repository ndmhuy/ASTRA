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
  requestedChange: string;
  teacherText: string;
  status: 'pending' | 'cancelled';
  createdAt: string;
  updatedAt: string;
}

export interface UiContextSnapshot {
  workspaceId: string | null;
  screen: 'start' | 'workspace';
  activeModal: 'exam_setup' | null;
  sidebarCollapsed: boolean;
  stateVersion: number;
  activeJob: { id: string; stage: string; percent: number; source: 'real' | 'mock' | 'unknown' } | null;
  examRevision: number | null;
  sessions: { id: string; title: string; status: 'draft' | 'generating' | 'complete' | 'error'; createdAt: string }[];
  notes: { id: string; targetQuestion: number | null; requestedChange: string; status: 'pending' | 'cancelled' }[];
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
  provider: 'deterministic' | 'gemini' | 'fallback';
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
