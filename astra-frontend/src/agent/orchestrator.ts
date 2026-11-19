import { CALLABLE_CAPABILITIES } from './capabilities.ts';
import type {
  AgentTaskState,
  UiActionProposal,
  UiContextSnapshot,
  UiExecutionReceipt,
} from './contracts.ts';
import type { UiActionExecutor } from './executor.ts';

export const MAX_ACTIONS_PER_TURN = 4;
export const MAX_REPLAN_ATTEMPTS = 2;

function signature(proposal: UiActionProposal): string {
  return JSON.stringify([proposal.capabilityId, proposal.params, proposal.target]);
}

function now(): string { return new Date().toISOString(); }

export class AgentTaskController {
  async execute(
    teacherGoal: string,
    workspaceId: string | null,
    proposals: UiActionProposal[],
    executor: UiActionExecutor,
    captureContext: () => UiContextSnapshot,
    previous: AgentTaskState | null = null,
    onUpdate: (task: AgentTaskState) => void = () => undefined,
  ): Promise<{ task: AgentTaskState; receipts: UiExecutionReceipt[] }> {
    const bounded = proposals.slice(0, MAX_ACTIONS_PER_TURN);
    const taskId = previous && previous.taskStatus === 'awaiting_confirmation'
      ? previous.taskId
      : crypto.randomUUID();
    const existingCompleted = previous?.taskId === taskId ? previous.completedSteps : [];
    let task: AgentTaskState = {
      taskId,
      workspaceId,
      teacherGoal: previous?.taskId === taskId ? previous.teacherGoal : teacherGoal,
      taskStatus: 'executing',
      plan: bounded.map((proposal, index) => ({
        stepId: `${taskId}:${(previous?.plan.length || 0) + index + 1}`,
        capabilityId: proposal.capabilityId,
        params: proposal.params,
        target: proposal.target,
        status: 'pending',
      })),
      currentStep: 0,
      completedSteps: existingCompleted,
      pendingSteps: bounded.map(proposal => proposal.capabilityId),
      pendingConfirmation: previous?.pendingConfirmation || null,
      lastExecutionReceipt: previous?.lastExecutionReceipt || null,
      lastObservedStateVersion: captureContext().stateVersion,
      blockingReason: null,
      relatedJobId: captureContext().activeJob?.id || previous?.relatedJobId || null,
      relatedExamId: captureContext().examId || previous?.relatedExamId || null,
      relatedRevisionId: captureContext().examRevision || previous?.relatedRevisionId || null,
      replanAttempts: previous?.replanAttempts || 0,
      updatedAt: now(),
    };
    onUpdate(task);

    if (proposals.length > MAX_ACTIONS_PER_TURN) {
      task = { ...task, taskStatus: 'blocked', blockingReason: 'ACTION_LIMIT_EXCEEDED', updatedAt: now() };
      onUpdate(task);
      return { task, receipts: [] };
    }

    const seen = new Set<string>();
    const receipts: UiExecutionReceipt[] = [];
    for (let index = 0; index < bounded.length; index += 1) {
      const original = bounded[index];
      const step = task.plan[index];
      const actionSignature = signature(original);
      if (seen.has(actionSignature)) {
        const receipt: UiExecutionReceipt = {
          actionId: original.actionId,
          capabilityId: original.capabilityId,
          status: 'skipped',
          observedStateVersion: task.lastObservedStateVersion,
          errorCode: 'LOOP_DETECTED',
        };
        receipts.push(receipt);
        step.status = 'skipped';
        step.receipt = receipt;
        task = { ...task, taskStatus: 'blocked', blockingReason: 'LOOP_DETECTED', lastExecutionReceipt: receipt, updatedAt: now() };
        onUpdate(task);
        break;
      }
      seen.add(actionSignature);

      const definition = CALLABLE_CAPABILITIES[original.capabilityId];
      if (!definition) {
        const receipt: UiExecutionReceipt = {
          actionId: original.actionId,
          capabilityId: original.capabilityId,
          status: 'failed',
          observedStateVersion: captureContext().stateVersion,
          errorCode: 'CAPABILITY_UNAVAILABLE',
        };
        receipts.push(receipt);
        step.status = 'failed';
        step.receipt = receipt;
        task = { ...task, taskStatus: 'blocked', blockingReason: receipt.errorCode!, lastExecutionReceipt: receipt, updatedAt: now() };
        onUpdate(task);
        break;
      }

      step.status = 'running';
      task = { ...task, currentStep: index, pendingSteps: task.plan.slice(index).map(item => item.capabilityId), updatedAt: now() };
      onUpdate(task);
      const current = captureContext();
      const proposal = { ...original, expectedStateVersion: current.stateVersion };
      const receipt = await executor.execute(proposal);
      receipts.push(receipt);
      step.receipt = receipt;
      step.status = receipt.status === 'success' ? 'completed' : receipt.status === 'skipped' ? 'skipped' : 'failed';
      task = {
        ...task,
        completedSteps: receipt.status === 'success' ? [...task.completedSteps, step.stepId] : task.completedSteps,
        pendingSteps: task.plan.slice(index + 1).map(item => item.capabilityId),
        lastExecutionReceipt: receipt,
        lastObservedStateVersion: receipt.observedStateVersion,
        relatedJobId: captureContext().activeJob?.id || task.relatedJobId,
        relatedExamId: captureContext().examId || task.relatedExamId,
        relatedRevisionId: captureContext().examRevision || task.relatedRevisionId,
        updatedAt: now(),
      };
      if (receipt.status !== 'success') {
        task.taskStatus = receipt.errorCode === 'CONFIRMATION_REQUIRED' ? 'awaiting_confirmation' : 'blocked';
        task.blockingReason = receipt.errorCode || 'STEP_FAILED';
        onUpdate(task);
        break;
      }
      const confirmationKind = receipt.result?.pendingConfirmation;
      if (typeof confirmationKind === 'string') {
        task.taskStatus = 'awaiting_confirmation';
        task.pendingConfirmation = captureContext().pendingConfirmation;
        onUpdate(task);
        break;
      }
      onUpdate(task);
    }
    if (task.taskStatus === 'executing') {
      task = { ...task, taskStatus: 'completed', pendingSteps: [], pendingConfirmation: null, updatedAt: now() };
      onUpdate(task);
    }
    return { task, receipts };
  }
}

export function isExplicitConfirmation(message: string): boolean {
  const normalized = message.trim().toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return /^(xac nhan|dong y|bat dau|tien hanh|ap dung|duyet)(\s+(tao de|ghi chu|chinh sua|ban nay))?[.!]?$/u.test(normalized);
}
