import catalog from '../../../src/exam_baseline/resources/agent/catalog.json' with { type: 'json' };

export const VERSION = catalog.schemaVersion;
export const MAX_ACTIONS = catalog.maxActions;
export type IntentId = keyof typeof catalog.intents;
export type Intent = { id: IntentId; args: Record<string, string | number | boolean> };
export type ExamIntake = {
  mode: 'request' | 'structure' | 'capability';
  family?: 'thpt' | 'vact' | 'custom';
  subject?: string;
  topic?: string;
  grade?: number;
  count?: number;
  minutes?: number;
  useDefaults?: boolean;
};
export type Decision = {
  kind: 'task' | 'answer' | 'clarify' | 'unsupported' | 'temporarily_unavailable';
  intents: Intent[];
  reasonCode?: string;
  guidance?: 'start' | 'capabilities' | 'remark';
  title?: string;
  intake?: ExamIntake;
};
export type AgentContext = {
  screen: 'start' | 'workspace';
  setup: boolean;
  status: 'draft' | 'generating' | 'complete' | 'error' | null;
  view: 'paper' | 'review' | 'pdf';
  history?: string[];
  facts?: string[];
  questionRefs?: string[];
  editor?: boolean;
  approved?: boolean;
  confirmationPending?: boolean;
  dialogue?: {
    family?: 'thpt' | 'vact' | 'custom'; subject?: string;
    missing?: 'family' | 'subject'; phase: 'collecting' | 'selected' | 'evaluated' | 'confirmed';
  };
  preview?: 'not_requested' | 'unavailable' | 'queued' | 'compiling' | 'ready' | 'failed' | null;
};

function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

export function validIntent(value: unknown): value is Intent {
  if (!record(value) || Object.keys(value).length !== 2 || typeof value.id !== 'string' ||
      !Object.hasOwn(catalog.intents, value.id) || !record(value.args)) return false;
  const args = value.args;
  const rules: Record<string, string> = catalog.intents[value.id as IntentId].args;
  return Object.keys(args).every(key => Object.hasOwn(rules, key)) &&
    Object.entries(rules).every(([key, rule]) => {
      if (!Object.hasOwn(args, key)) return rule.endsWith('?');
      const arg = args[key];
      const kind = rule.replace(/\?$/, '');
      if (kind.includes('|')) return typeof arg === 'string' && kind.split('|').includes(arg);
      if (kind === 'integer') return typeof arg === 'number' && Number.isInteger(arg) && arg >= 1 && arg <= 999;
      if (kind === 'string') return typeof arg === 'string' && [...arg].length >= 1 && [...arg].length <= 600;
      return typeof arg === 'boolean';
    });
}

function validIntake(value: unknown): value is ExamIntake {
  if (!record(value) || typeof value.mode !== 'string' || !['request', 'structure', 'capability'].includes(value.mode)) return false;
  return Object.entries(value).every(([key, item]) => {
    switch (key) {
      case 'mode': return true;
      case 'useDefaults': return typeof item === 'boolean';
      case 'family': return typeof item === 'string' && ['thpt', 'vact', 'custom'].includes(item);
      case 'subject':
      case 'topic': return typeof item === 'string' && item.length > 0 && item.length <= (key === 'subject' ? 80 : 250);
      case 'grade':
      case 'count':
      case 'minutes': return typeof item === 'number' && Number.isInteger(item) && item >= 1 && item <= (key === 'grade' ? 12 : 999);
      default: return false;
    }
  });
}

export function parseDecision(value: unknown, messageId: string): Decision {
  if (!record(value) || Object.keys(value).length !== 3 ||
      value.schemaVersion !== VERSION || value.clientMessageId !== messageId || !record(value.decision)) {
    throw new Error('agent_contract');
  }
  const { kind, intents, reasonCode, guidance, title, intake } = value.decision;
  if (Object.keys(value.decision).some(key => !['kind', 'intents', 'reasonCode', 'guidance', 'title', 'intake'].includes(key)) ||
      (title !== undefined && (typeof title !== 'string' || title.trim().length === 0 || [...title].length > 60)) ||
      (guidance !== undefined && (typeof guidance !== 'string' || !['start', 'capabilities', 'remark'].includes(guidance))) ||
      (intake !== undefined && !validIntake(intake)) ||
      ((intake !== undefined || guidance !== undefined) && kind !== 'answer' && kind !== 'clarify') ||
      (intake !== undefined && guidance !== undefined) ||
      (reasonCode !== undefined && (kind !== 'temporarily_unavailable' ||
        !['disabled', 'configuration', 'transient', 'quota', 'schema', 'budget', 'auth', 'model', 'timeout', 'rejected'].includes(String(reasonCode)))) ||
      !['task', 'answer', 'clarify', 'unsupported', 'temporarily_unavailable'].includes(String(kind)) ||
      !Array.isArray(intents) || intents.length > MAX_ACTIONS ||
      (kind === 'task') !== (intents.length > 0) || !intents.every(validIntent)) {
    throw new Error('agent_contract');
  }
  return value.decision as Decision;
}
