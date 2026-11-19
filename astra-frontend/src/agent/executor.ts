import { CALLABLE_CAPABILITIES } from './capabilities.ts';
import type { UiActionProposal, UiContextSnapshot, UiExecutionReceipt } from './contracts';

export type UiActionHandler = (params: Record<string, unknown>) => Promise<Record<string, unknown> | void> | Record<string, unknown> | void;

export class UiActionExecutor {
  private receipts = new Map<string, UiExecutionReceipt>();
  private getContext: () => UiContextSnapshot;
  private handlers: Record<string, UiActionHandler>;
  private settle: () => Promise<void>;

  constructor(
    getContext: () => UiContextSnapshot,
    handlers: Record<string, UiActionHandler>,
    settle: () => Promise<void> = () => Promise.resolve(),
  ) {
    this.getContext = getContext;
    this.handlers = handlers;
    this.settle = settle;
  }

  async execute(proposal: UiActionProposal): Promise<UiExecutionReceipt> {
    const duplicate = this.receipts.get(proposal.actionId);
    if (duplicate) return { ...duplicate, duplicate: true };
    const before = this.getContext();
    const capability = CALLABLE_CAPABILITIES[proposal.capabilityId];
    if (!capability || capability.status !== 'available_real' || !capability.callable || !this.handlers[proposal.capabilityId]) {
      return this.remember(proposal, before.stateVersion, 'failed', 'CAPABILITY_UNAVAILABLE');
    }
    if (proposal.expectedStateVersion !== before.stateVersion) {
      return this.remember(proposal, before.stateVersion, 'failed', 'STALE_CONTEXT');
    }
    const validationError = capability.validate(proposal.params, before);
    if (validationError) return this.remember(proposal, before.stateVersion, 'failed', validationError);
    try {
      const result = await this.handlers[proposal.capabilityId](proposal.params);
      await this.settle();
      const after = this.getContext();
      const workspaceActions = ['ui.navigate', 'ui.session.create', 'ui.session.open', 'ui.session.delete', 'ui.chat.branch'];
      if (before.workspaceId !== after.workspaceId && !workspaceActions.includes(proposal.capabilityId)) {
        return this.remember(proposal, after.stateVersion, 'failed', 'WORKSPACE_CHANGED');
      }
      if (!capability.verify(before, after, proposal.params, result || undefined)) {
        return this.remember(proposal, after.stateVersion, 'failed', 'EFFECT_NOT_OBSERVED', result || undefined);
      }
      return this.remember(proposal, after.stateVersion, 'success', undefined, result || undefined);
    } catch {
      return this.remember(proposal, this.getContext().stateVersion, 'failed', 'HANDLER_FAILED');
    }
  }

  private remember(
    proposal: UiActionProposal,
    observedStateVersion: number,
    status: UiExecutionReceipt['status'],
    errorCode?: string,
    result?: Record<string, unknown>,
  ): UiExecutionReceipt {
    const receipt: UiExecutionReceipt = {
      actionId: proposal.actionId,
      capabilityId: proposal.capabilityId,
      status,
      observedStateVersion,
      ...(errorCode ? { errorCode } : {}),
      ...(result ? { result } : {}),
    };
    this.receipts.set(proposal.actionId, receipt);
    return receipt;
  }
}

export async function executeActionPlan(
  proposals: UiActionProposal[],
  executor: UiActionExecutor,
): Promise<UiExecutionReceipt[]> {
  const receipts: UiExecutionReceipt[] = [];
  let dependencyFailed = false;
  for (const proposal of proposals) {
    if (dependencyFailed) {
      receipts.push({
        actionId: proposal.actionId,
        capabilityId: proposal.capabilityId,
        status: 'skipped',
        observedStateVersion: receipts.at(-1)?.observedStateVersion || proposal.expectedStateVersion,
        errorCode: 'DEPENDENCY_FAILED',
      });
      continue;
    }
    const receipt = await executor.execute(proposal);
    receipts.push(receipt);
    dependencyFailed = receipt.status !== 'success';
  }
  return receipts;
}
