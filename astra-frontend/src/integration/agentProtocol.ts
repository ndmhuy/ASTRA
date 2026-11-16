export type ScreenId = 'welcome' | 'create' | 'library' | 'workspace';
export type CapabilityId = 'ui.navigate' | 'ui.session.create' | 'ui.exam.open_setup' | 'ui.sidebar.set_collapsed';

export interface ScreenContext {
  screen_id: ScreenId;
  state_version: number;
  workspace_session_id: string | null;
  selected_question_id: string | null;
  question_index_map: Record<string, string>;
  available_actions: CapabilityId[];
}

export interface TurnRequest {
  schema_version: 'agent-turn/0.1';
  request_id: string;
  conversation_id: string;
  workspace_session_id: string;
  message: string;
  screen_context: ScreenContext;
}

export interface AgentAction {
  action_id: string;
  capability_id: CapabilityId;
  target: string;
  params: Record<string, unknown>;
}

export interface ActionPlan {
  schema_version: 'agent-actions/0.1';
  plan_id: string;
  conversation_id: string;
  expected_state_version: number;
  actions: AgentAction[];
}

export interface TurnResponse {
  schema_version: 'agent-turn/0.1';
  request_id: string;
  conversation_id: string;
  kind: 'reply' | 'clarification' | 'confirmation' | 'action_plan';
  reply: string;
  data: Record<string, unknown> & { plan?: ActionPlan };
  mock: boolean;
}

export interface ActionReceipt {
  plan_id: string;
  action_id: string;
  status: 'success' | 'failed' | 'skipped';
  error_code: string | null;
  data: Record<string, unknown>;
  state_version: number;
}

export interface ExecutionFeedback {
  feedback_id: string;
  conversation_id: string;
  workspace_session_id: string;
  original_request_id: string;
  results: ActionReceipt[];
}

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const exactKeys = (value: Record<string, unknown>, required: string[], optional: string[] = []) => {
  const keys = Object.keys(value);
  return required.every(key => keys.includes(key)) && keys.every(key => required.includes(key) || optional.includes(key));
};
const nonEmpty = (value: unknown): value is string => typeof value === 'string' && value.length > 0;

function parseAction(value: unknown): AgentAction {
  if (!isRecord(value) || !exactKeys(value, ['action_id', 'capability_id', 'target', 'params'])) throw new Error('INVALID_ACTION_SHAPE');
  if (!nonEmpty(value.action_id) || !nonEmpty(value.target) || !isRecord(value.params)) throw new Error('INVALID_ACTION_VALUE');
  const capability = value.capability_id;
  const allowed: CapabilityId[] = ['ui.navigate', 'ui.session.create', 'ui.exam.open_setup', 'ui.sidebar.set_collapsed'];
  if (!allowed.includes(capability as CapabilityId)) throw new Error('UNKNOWN_CAPABILITY');
  const targets: Record<CapabilityId, string> = { 'ui.navigate': 'application', 'ui.session.create': 'exam-sessions', 'ui.exam.open_setup': 'exam-setup', 'ui.sidebar.set_collapsed': 'main-navigation' };
  if (value.target !== targets[capability as CapabilityId]) throw new Error('INVALID_TARGET');
  const params = value.params;
  if (capability === 'ui.navigate') {
    if (!exactKeys(params, ['screen_id'], ['workspace_session_id']) || !['welcome', 'create', 'library', 'workspace'].includes(String(params.screen_id))) throw new Error('INVALID_PARAMS');
    if ((params.screen_id === 'workspace') !== nonEmpty(params.workspace_session_id)) throw new Error('INVALID_PARAMS');
  } else if (capability === 'ui.session.create') {
    if (!exactKeys(params, ['mode']) || !['template', 'custom'].includes(String(params.mode))) throw new Error('INVALID_PARAMS');
  } else if (capability === 'ui.exam.open_setup') {
    if (!exactKeys(params, ['workspace_session_id']) || !nonEmpty(params.workspace_session_id)) throw new Error('INVALID_PARAMS');
  } else if (!exactKeys(params, ['collapsed']) || typeof params.collapsed !== 'boolean') {
    throw new Error('INVALID_PARAMS');
  }
  return { action_id: value.action_id, capability_id: capability as CapabilityId, target: value.target, params };
}

export function parseActionPlan(value: unknown): ActionPlan {
  if (!isRecord(value) || !exactKeys(value, ['schema_version', 'plan_id', 'conversation_id', 'expected_state_version', 'actions'])) throw new Error('INVALID_PLAN_SHAPE');
  if (value.schema_version !== 'agent-actions/0.1' || !nonEmpty(value.plan_id) || !nonEmpty(value.conversation_id) || !Number.isInteger(value.expected_state_version)) throw new Error('INVALID_PLAN_VALUE');
  if (!Array.isArray(value.actions) || value.actions.length < 1 || value.actions.length > 5) throw new Error('INVALID_ACTION_COUNT');
  const actions = value.actions.map(parseAction);
  if (new Set(actions.map(action => action.action_id)).size !== actions.length) throw new Error('DUPLICATE_ACTION_ID');
  return { schema_version: 'agent-actions/0.1', plan_id: value.plan_id, conversation_id: value.conversation_id, expected_state_version: value.expected_state_version as number, actions };
}

export function parseTurnResponse(value: unknown): TurnResponse {
  if (!isRecord(value) || !exactKeys(value, ['schema_version', 'request_id', 'conversation_id', 'kind', 'reply', 'data', 'mock'])) throw new Error('INVALID_RESPONSE_SHAPE');
  if (value.schema_version !== 'agent-turn/0.1' || !nonEmpty(value.request_id) || !nonEmpty(value.conversation_id) || !nonEmpty(value.reply) || typeof value.mock !== 'boolean' || !isRecord(value.data)) throw new Error('INVALID_RESPONSE_VALUE');
  if (!['reply', 'clarification', 'confirmation', 'action_plan'].includes(String(value.kind))) throw new Error('INVALID_RESPONSE_KIND');
  const data = { ...value.data } as Record<string, unknown> & { plan?: ActionPlan };
  if (value.kind === 'action_plan') data.plan = parseActionPlan(value.data.plan);
  else if ('plan' in value.data) throw new Error('UNEXPECTED_PLAN');
  return { schema_version: 'agent-turn/0.1', request_id: value.request_id, conversation_id: value.conversation_id, kind: value.kind as TurnResponse['kind'], reply: value.reply, data, mock: value.mock };
}
