import { CALLABLE_CAPABILITIES } from './capabilities.ts';
import type { UiActionProposal, UiContextSnapshot, UiExecutionReceipt } from './contracts';

export type UiActionHandler = (params: Record<string, unknown>) => Promise<Record<string, unknown> | void> | Record<string, unknown> | void;

export function actionFailureMessage(code?: string): string {
  if (code && /provider_|network|timeout|rate_limit|gemini_/i.test(code)) {
    return 'Dịch vụ đang lỗi tạm thời hoặc quá tải. Chức năng vẫn được hỗ trợ; bạn vui lòng thử lại sau ít phút.';
  }
  if (code === 'CONFIRMATION_REQUIRED') {
    return 'Thao tác cần xác nhận mới cho đúng dữ liệu và đối tượng hiện tại.';
  }
  if (code && /STALE|TARGET_CHANGED|WORKSPACE_CHANGED|stale_/i.test(code)) {
    return 'Đối tượng hoặc phiên bản đã thay đổi; bạn hãy kiểm tra lại trước khi thao tác.';
  }
  if (code === 'EXAM_NOT_READY' || code === 'NO_ACTIVE_EXAM' || code === 'QUESTION_NOT_READY') {
    return 'Chưa có đề thi sẵn sàng để thực hiện thao tác này.';
  }
  if (code === 'PREVIEW_REVIEW_REQUIRED') {
    return 'Vui lòng mở xem trước PDF của bản hiện tại trước khi phê duyệt.';
  }
  if (code === 'APPROVAL_REQUIRED') {
    return 'Cần phê duyệt đề thi trước khi tải xuống.';
  }
  if (code === 'PREVIEW_NOT_READY') {
    return 'Bản xem trước PDF chưa sẵn sàng để tải xuống.';
  }
  if (code === 'GENERATION_ALREADY_RUNNING') {
    return 'Hệ thống đang soạn đề cho phiên này, vui lòng chờ hoàn tất.';
  }
  if (code === 'CATALOG_NOT_READY' || code === 'SETUP_NOT_OPEN' || code === 'SETUP_NOT_READY') {
    return 'Hộp thiết lập đề chưa sẵn sàng, bạn hãy mở lại thiết lập.';
  }
  if (code === 'EDITOR_NOT_OPEN') {
    return 'Trình chỉnh sửa câu hỏi hiện chưa mở.';
  }
  if (code === 'FORMAT_UNAVAILABLE') {
    return 'Định dạng đề này hiện chưa khả dụng để tạo trực tiếp.';
  }
  if (code && /_NOT_FOUND$/.test(code)) {
    return 'Không tìm thấy mục bạn yêu cầu trong phiên hiện tại.';
  }
  if (code === 'CAPABILITY_UNAVAILABLE') {
    return 'Tính năng này hiện chưa được hỗ trợ trên giao diện.';
  }
  if (code && /NOT_READY|REQUIRED|NOT_FOUND|NOT_OPEN|UNAVAILABLE/.test(code)) {
    return 'Chưa đủ điều kiện để thực hiện thao tác này ở trạng thái hiện tại.';
  }
  return 'Giao diện chưa xác nhận được kết quả nên thao tác đã dừng an toàn.';
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
