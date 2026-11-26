import catalog from '../../../src/exam_baseline/resources/agent/semantic-catalog.json' with { type: 'json' };
import domain from '../../../src/exam_baseline/resources/agent/domain.json' with { type: 'json' };
import type { Decision, ExamIntake, Intent } from './contracts.ts';
import { validIntent } from './contracts.ts';
import type { Intake } from './intake.ts';
import type { ExamFormat } from '../types/exam.ts';
import { fold } from './recipes.ts';
import { sectionId } from './examActions.ts';

export type GoalId = keyof typeof catalog.goals;
export type SemanticGoal = { goal: GoalId; parameters: Intent['args']; reference?: 'current' | 'previous' | 'recent' };
export type SemanticFrame = {
  schemaVersion: 'astra-semantic-v1';
  dialogueAct: 'REQUEST' | 'INFORM' | 'QUESTION' | 'GUIDANCE' | 'CORRECT' | 'CANCEL' | 'CONFIRM' |
    'CONVERSATION' | 'AMBIGUOUS' | 'UNSUPPORTED' | 'OUT_OF_SCOPE';
  goals: SemanticGoal[];
  constraints: Array<'NO_GENERATION' | 'NO_EXECUTION' | 'CONDITIONAL' | 'NEGATED' | 'CONTRADICTORY'>;
  title?: string;
};
const record = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === 'object' && !Array.isArray(value);
const acts = ['REQUEST', 'INFORM', 'QUESTION', 'GUIDANCE', 'CORRECT', 'CANCEL', 'CONFIRM',
  'CONVERSATION', 'AMBIGUOUS', 'UNSUPPORTED', 'OUT_OF_SCOPE'];
const constraints = ['NO_GENERATION', 'NO_EXECUTION', 'CONDITIONAL', 'NEGATED', 'CONTRADICTORY'];

export function parseFrame(value: unknown): SemanticFrame {
  if (!record(value) || value.schemaVersion !== catalog.schemaVersion || !acts.includes(String(value.dialogueAct)) ||
      Object.keys(value).some(key => !['schemaVersion', 'dialogueAct', 'goals', 'constraints', 'title'].includes(key))) throw new Error('agent_semantic_contract');
  const goals = value.goals ?? [];
  const bounds = value.constraints ?? [];
  if (!Array.isArray(goals) || goals.length > catalog.limits.goalsPerTurn ||
      !Array.isArray(bounds) || bounds.length > 5 || bounds.some(item => !constraints.includes(item))) throw new Error('agent_semantic_contract');
  const normalized = goals.map((item): SemanticGoal => {
    if (!record(item) || !Object.hasOwn(catalog.goals, String(item.goal)) ||
        Object.keys(item).some(key => !['goal', 'parameters', 'reference'].includes(key)) ||
        (item.reference != null && !['current', 'previous', 'recent'].includes(String(item.reference)))) throw new Error('agent_semantic_goal');
    const goal = item.goal as GoalId;
    const parameters = item.parameters ?? {};
    const rules: Record<string, string> = catalog.goals[goal].parameters;
    if (!record(parameters) || Object.entries(parameters).some(([key, value]) => {
      const rule = rules[key]?.replace(/\?$/, '');
      if (!rule) return true;
      if (rule.includes('|')) return typeof value !== 'string' || !rule.split('|').includes(value);
      if (rule === 'string') return typeof value !== 'string' || [...value].length < 1 || [...value].length > 600;
      if (rule === 'integer') return typeof value !== 'number' || !Number.isInteger(value) || value < 1 || value > 999;
      return typeof value !== 'boolean';
    })) throw new Error('agent_semantic_parameter');
    return { goal, parameters: parameters as Intent['args'], ...(item.reference ? { reference: item.reference as SemanticGoal['reference'] } : {}) };
  });
  const title = typeof value.title === 'string' ? value.title.replace(/[\p{Cc}\p{Cf}]/gu, ' ').replace(/\s+/g, ' ').trim() : '';
  return { schemaVersion: 'astra-semantic-v1', dialogueAct: value.dialogueAct as SemanticFrame['dialogueAct'],
    goals: normalized, constraints: bounds, ...(title && [...title].length <= 60 ? { title } : {}) };
}

export type WorkflowResolution = {
  decision?: Decision;
  text?: string;
  invalidateConfirmation: boolean;
  cancel?: boolean;
  requestGeneration?: boolean;
  setupOnly?: boolean;
  referenceTarget?: { number: number; part?: string };
};
const readOnly = new Set(['READ_PROGRESS', 'READ_WARNINGS', 'LIST_EXAM_FORMATS', 'RECALL_REQUIREMENTS', 'FIND_CONVERSATIONS']);

export function resolveSemantic(frame: SemanticFrame, recent?: { number: number; part?: string }): WorkflowResolution {
  const invalidateConfirmation = frame.dialogueAct === 'CORRECT' || frame.dialogueAct === 'CANCEL';
  const stop = (text: string): WorkflowResolution => ({ text, invalidateConfirmation });
  // Inspect the entire turn before exposing even its first side effect.
  if (frame.constraints.some(item => ['NO_EXECUTION', 'CONDITIONAL', 'NEGATED', 'CONTRADICTORY'].includes(item))) {
    return stop('Em chưa thực hiện thao tác. Thầy cô hãy làm rõ yêu cầu muốn thực hiện.');
  }
  if (frame.dialogueAct === 'CANCEL') return { cancel: true, invalidateConfirmation: true };
  if (frame.dialogueAct === 'CONFIRM') return stop('Thầy cô hãy nhắn “Xác nhận” cho thao tác đang chờ, hoặc dùng nút xác nhận.');
  if (frame.dialogueAct === 'CONVERSATION') return stop('Em sẵn sàng hỗ trợ thầy cô chuẩn bị, kiểm tra và quản lý đề thi trong ASTRA.');
  if (frame.dialogueAct === 'OUT_OF_SCOPE') return stop('Em hỗ trợ soạn, kiểm tra và quản lý đề thi trong ASTRA.');
  if (frame.dialogueAct === 'UNSUPPORTED') return stop('Tính năng này chưa có trong ASTRA. Thầy cô có thể xem các mẫu và thao tác hiện có.');
  if (frame.dialogueAct === 'AMBIGUOUS' || !frame.goals.length) return stop('Thầy cô muốn thao tác nào trong ASTRA? Em cần thêm thông tin.');
  const usesReference = frame.goals.some(goal => goal.reference === 'previous');
  const questionGoals = ['INSPECT_QUESTION', 'EDIT_QUESTION', 'VERIFY_ANSWER', 'REGENERATE_ITEM', 'FILL_EDITOR'];
  if (usesReference && (!recent || frame.goals.length !== 1 || !questionGoals.includes(frame.goals[0].goal) ||
      (frame.goals[0].parameters.number !== undefined && frame.goals[0].parameters.number !== recent.number) ||
      (frame.goals[0].parameters.part !== undefined && sectionId(String(frame.goals[0].parameters.part)) !== sectionId(recent.part ?? '')))) {
    return stop('Thầy cô muốn nói đến đề hoặc câu nào? Hãy ghi tên đề hoặc số câu và phần thi.');
  }
  const goals = frame.goals.map(goal => usesReference && recent
    ? { ...goal, parameters: { ...goal.parameters, number: recent.number, ...(recent.part ? { part: recent.part } : {}) } } : goal);
  const definitions = goals.map(goal => catalog.goals[goal.goal]);
  if (frame.goals.some((goal, index) => !definitions[index].dialogueActs.includes(frame.dialogueAct) &&
      !(frame.dialogueAct === 'QUESTION' && (readOnly.has(goal.goal) || ['intake', 'format_info'].includes(definitions[index].resolver))))) {
    return stop('Thầy cô đang hỏi thông tin hay muốn thực hiện thao tác? Em chưa thay đổi đề.');
  }
  const nonActions = definitions.filter(definition => definition.resolver !== 'capability');
  if (nonActions.length) {
    if (frame.goals.length !== 1) return stop('Yêu cầu gồm bước cấu hình hoặc hướng dẫn cần làm rõ trước. Thầy cô hãy hoàn tất bước đó rồi tiếp tục.');
    const definition = definitions[0];
    const goal = frame.goals[0];
    if (definition.resolver === 'guidance') return { invalidateConfirmation, decision: {
      kind: 'answer', intents: [], guidance: goal.goal === 'CAPABILITY_INQUIRY' ? 'capabilities' : 'start', title: frame.title,
    } };
    const information = frame.dialogueAct === 'QUESTION';
    return { invalidateConfirmation, setupOnly: !information && (goal.goal === 'PREPARE_EXAM' || definition.resolver === 'format_info' || frame.constraints.includes('NO_GENERATION')),
      requestGeneration: !information && goal.goal === 'REQUEST_GENERATION' && !frame.constraints.includes('NO_GENERATION'),
      decision: { kind: 'answer', intents: [], title: frame.title,
        intake: { mode: information ? 'structure' : 'request', ...goal.parameters } as ExamIntake } };
  }
  if (frame.constraints.includes('NO_GENERATION') && frame.goals.some(goal => goal.goal === 'APPLY_REVISION_NOTES' || goal.goal === 'REGENERATE_ITEM')) {
    return stop('Em chưa thực hiện thao tác có gọi AI. Thầy cô hãy xác định phần muốn xem hoặc sửa.');
  }
  const intents = goals.map((goal, index) => ({ id: definitions[index].capability, args: goal.parameters })) as Intent[];
  if (!intents.every(validIntent)) return stop('Thầy cô hãy bổ sung tham số hoặc chỉ rõ câu và phần thi cho yêu cầu này.');
  return { invalidateConfirmation, ...(usesReference && recent ? { referenceTarget: recent } : {}), decision: { kind: 'task', intents, title: frame.title } };
}

export function contextualSubject(message: string, previous: Intake | undefined, formats: ExamFormat[]): Decision | undefined {
  if (previous?.missing !== 'subject') return;
  const text = fold(message).replace(/[.!]+$/, '');
  const subjects: Record<string, string[]> = { ...domain.subjects };
  for (const format of formats) for (const subject of format.subjects) subjects[subject] ??= [];
  const subject = Object.entries(subjects).find(([name, aliases]) => [name, ...aliases].some(term => fold(term) === text))?.[0];
  if (subject) return { kind: 'answer', intents: [], intake: { mode: 'request', subject } };
}
