import { parseActionPlan, type ActionPlan, type ActionReceipt, type AgentAction, type CapabilityId, type ScreenContext } from './agentProtocol.ts';

export interface UiCapabilityResult { data: Record<string, unknown>; stateVersion: number }
export type UiCapabilityHandler = (action: AgentAction) => Promise<UiCapabilityResult>;
export type UiCapabilityRegistry = Partial<Record<CapabilityId, UiCapabilityHandler>>;

export class UiExecutor {
  private queue: Promise<unknown> = Promise.resolve();
  private readonly plans = new Map<string, string>();
  private readonly ledger = new Map<string, { fingerprint: string; receipt: ActionReceipt }>();
  private readonly registry: UiCapabilityRegistry;
  private readonly getContext: () => ScreenContext;
  constructor(registry: UiCapabilityRegistry, getContext: () => ScreenContext) {
    this.registry = registry;
    this.getContext = getContext;
  }

  async execute(plan: ActionPlan): Promise<ActionReceipt[]> {
    plan = parseActionPlan(plan);
    const key = `${plan.conversation_id}\u0000${plan.plan_id}`;
    const canonical = JSON.stringify(plan);
    const prior = this.plans.get(key);
    if (prior && prior !== canonical) throw new Error('PLAN_ACTION_ID_REUSED');
    this.plans.set(key, canonical);
    const task = this.queue.then(() => this.executeSerial(plan));
    this.queue = task.catch(() => {});
    return task;
  }

  private async executeSerial(plan: ActionPlan): Promise<ActionReceipt[]> {
    const fingerprint = (action: AgentAction) => JSON.stringify({ expected_state_version: plan.expected_state_version, capability_id: action.capability_id, target: action.target, params: action.params });
    const replay = plan.actions.map(action => {
      const record = this.ledger.get(`${plan.conversation_id}\u0000${plan.plan_id}\u0000${action.action_id}`);
      if (record && record.fingerprint !== fingerprint(action)) throw new Error('PLAN_ACTION_ID_REUSED');
      return record?.receipt;
    });
    if (replay.every((receipt): receipt is ActionReceipt => receipt !== undefined)) return replay;
    if (plan.expected_state_version !== this.getContext().state_version) {
      return plan.actions.map((action, index) => {
        const receipt: ActionReceipt = { plan_id: plan.plan_id, action_id: action.action_id, status: index === 0 ? 'failed' : 'skipped', error_code: index === 0 ? 'STALE_CONTEXT' : 'DEPENDENCY_FAILED', data: {}, state_version: this.getContext().state_version };
        this.ledger.set(`${plan.conversation_id}\u0000${plan.plan_id}\u0000${action.action_id}`, { fingerprint: fingerprint(action), receipt });
        return receipt;
      });
    }
    const receipts: ActionReceipt[] = [];
    let failed = false;
    for (const action of plan.actions) {
      const key = `${plan.conversation_id}\u0000${plan.plan_id}\u0000${action.action_id}`;
      const prior = this.ledger.get(key)?.receipt;
      if (prior) { receipts.push(prior); failed ||= prior.status !== 'success'; continue; }
      let receipt: ActionReceipt;
      if (failed) {
        receipt = { plan_id: plan.plan_id, action_id: action.action_id, status: 'skipped', error_code: 'DEPENDENCY_FAILED', data: {}, state_version: this.getContext().state_version };
      } else {
        const handler = this.registry[action.capability_id];
        if (!handler || !this.getContext().available_actions.includes(action.capability_id)) {
          receipt = { plan_id: plan.plan_id, action_id: action.action_id, status: 'failed', error_code: 'CAPABILITY_UNAVAILABLE', data: {}, state_version: this.getContext().state_version };
        } else {
          try {
            const result = await handler(action);
            receipt = { plan_id: plan.plan_id, action_id: action.action_id, status: 'success', error_code: null, data: result.data, state_version: result.stateVersion };
          } catch (error) {
            const code = error instanceof Error && /^[A-Z_]+$/.test(error.message) ? error.message : 'ACTION_FAILED';
            receipt = { plan_id: plan.plan_id, action_id: action.action_id, status: 'failed', error_code: code, data: {}, state_version: this.getContext().state_version };
          }
        }
      }
      this.ledger.set(key, { fingerprint: fingerprint(action), receipt });
      receipts.push(receipt);
      failed ||= receipt.status !== 'success';
    }
    return receipts;
  }
}
