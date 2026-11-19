import { CALLABLE_CAPABILITIES } from './capabilities.ts';
import type { UiActionProposal, UiContextSnapshot, UiExecutionReceipt } from './contracts';

export type UiActionHandler = (params: Record<string, unknown>) => Promise<Record<string, unknown> | void> | Record<string, unknown> | void;

export function actionFailureMessage(code?: string): string {
  if (code && /provider_|network|timeout|rate_limit|gemini_/i.test(code)) return 'Dịch vụ đang lỗi tạm thời hoặc quá tải. Chức năng vẫn được hỗ trợ; hãy kiểm tra trạng thái trước khi thử lại.';
  if (code === 'CONFIRMATION_REQUIRED') return 'Thao tác cần xác nhận mới cho đúng dữ liệu và đối tượng hiện tại.';
  if (code && /STALE|TARGET_CHANGED|WORKSPACE_CHANGED|stale_/i.test(code)) return 'Đối tượng hoặc phiên bản đã thay đổi; hãy tải lại và xem lại thao tác.';
  if (code && /NOT_READY|REQUIRED|NOT_FOUND|NOT_OPEN|UNAVAILABLE/.test(code)) return `Chưa đủ điều kiện thực hiện (${code}).`;
  return 'Giao diện chưa xác nhận được kết quả. Các bước phụ thuộc đã dừng.';
}

export class UiActionExecutor {
  private receipts = new Map<string, UiExecutionReceipt>();
  private inFlight = new Map<string, Promise<UiExecutionReceipt>>();
  private signatures = new Map<string, string>();
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
    const signature = JSON.stringify([proposal.capabilityId, proposal.params, proposal.target]);
    if (this.signatures.has(proposal.actionId) && this.signatures.get(proposal.actionId) !== signature) {
      return { actionId: proposal.actionId, capabilityId: proposal.capabilityId, status: 'failed', observedStateVersion: this.getContext().stateVersion, errorCode: 'ACTION_ID_CONFLICT' };
    }
    this.signatures.set(proposal.actionId, signature);
    const running = this.inFlight.get(proposal.actionId);
    if (running) return { ...await running, duplicate: true };
    const work = this.executeOnce(proposal);
    this.inFlight.set(proposal.actionId, work);
    try { return await work; } finally { this.inFlight.delete(proposal.actionId); }
  }

  private async executeOnce(proposal: UiActionProposal): Promise<UiExecutionReceipt> {
    const duplicate = this.receipts.get(proposal.actionId);
    if (duplicate) return { ...duplicate, duplicate: true };
    const before = this.getContext();
    const navigating = ['ui.session.open','ui.navigate'].includes(proposal.capabilityId) && proposal.target.workspaceId === proposal.params.workspaceId;
    if ((proposal.target.workspaceId && proposal.target.workspaceId !== before.workspaceId && !navigating)
      || (proposal.target.examId && proposal.target.examId !== before.examId)
      || (proposal.target.revision !== undefined && proposal.target.revision !== before.examRevision)) {
      return this.remember(proposal, before.stateVersion, 'failed', 'TARGET_CHANGED');
    }
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
    } catch (error) {
      const rawCode = error && typeof error === 'object' && 'code' in error ? error.code : undefined;
      const safeCode = typeof rawCode === 'string' && /^[a-zA-Z0-9_]{1,80}$/.test(rawCode) ? rawCode : 'HANDLER_FAILED';
      return this.remember(proposal, this.getContext().stateVersion, 'failed', safeCode);
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
