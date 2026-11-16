import { agentService, AgentHttpError } from '../services/agentService.ts';
import type { ExamSessions } from '../state/examSessions.ts';
import type { ExecutionFeedback, ScreenContext, TurnRequest, TurnResponse } from './agentProtocol.ts';
import type { UiExecutor } from './uiExecutor.ts';

export interface AgentControllerDependencies {
  store: ExamSessions;
  getContext: () => ScreenContext;
  executor: UiExecutor;
  service?: typeof agentService;
}
interface PendingTurn {
  request: TurnRequest;
  feedback?: ExecutionFeedback;
  running: boolean;
}
const pendingByStore = new WeakMap<ExamSessions, Map<string, PendingTurn>>();

function checkResponse(response: TurnResponse, request: TurnRequest) {
  if (response.request_id !== request.request_id || response.conversation_id !== request.conversation_id) throw new Error('RESPONSE_CORRELATION_FAILED');
}

export async function runAgentTurn(originWorkspaceId: string, message: string | null, dependencies: AgentControllerDependencies) {
  const { store, getContext, executor, service = agentService } = dependencies;
  if (!store.getSnapshot().some(session => session.id === originWorkspaceId)) return;
  let pending = pendingByStore.get(store);
  if (!pending) { pending = new Map(); pendingByStore.set(store, pending); }
  let turn = pending.get(originWorkspaceId);
  if (turn?.running) return;
  if (!turn) {
    if (!message?.trim()) return;
    turn = { request: {
      schema_version: 'agent-turn/0.1', request_id: crypto.randomUUID(),
      conversation_id: `workspace:${originWorkspaceId}`, workspace_session_id: originWorkspaceId,
      message: message.trim(), screen_context: structuredClone(getContext()),
    }, running: false };
    pending.set(originWorkspaceId, turn);
    store.appendUserMessage(originWorkspaceId, message.trim());
  }
  turn.running = true;
  store.setAgentPending(originWorkspaceId, true);
  try {
    let response: TurnResponse;
    if (turn.feedback) {
      response = await service.feedback(turn.feedback);
    } else {
      response = await service.turn(turn.request);
      checkResponse(response, turn.request);
      if (!store.getSnapshot().some(session => session.id === originWorkspaceId)) { pending.delete(originWorkspaceId); return; }
      if (response.kind === 'action_plan') {
        const plan = response.data.plan;
        if (!plan || plan.conversation_id !== turn.request.conversation_id || plan.expected_state_version !== turn.request.screen_context.state_version) throw new Error('PLAN_CORRELATION_FAILED');
        const results = await executor.execute(plan);
        turn.feedback = {
          feedback_id: crypto.randomUUID(), conversation_id: turn.request.conversation_id,
          workspace_session_id: originWorkspaceId, original_request_id: turn.request.request_id, results,
        };
        response = await service.feedback(turn.feedback);
      }
    }
    checkResponse(response, turn.request);
    if (response.kind === 'action_plan') throw new Error('UNEXPECTED_FOLLOWUP_PLAN');
    store.appendAssistantMessage(originWorkspaceId, response.reply);
    store.setAgentPending(originWorkspaceId, false);
    pending.delete(originWorkspaceId);
  } catch (error) {
    const unavailable = error instanceof AgentHttpError && [502, 503, 504].includes(error.status);
    const detail = unavailable
      ? 'Chưa kết nối được Agent. Mở terminal trong astra-frontend và chạy npm run dev để khởi động cả UI lẫn Agent.'
      : 'Chưa nhận được kết quả từ Agent. Bấm “Thử lại kết nối” để tiếp tục yêu cầu đã gửi.';
    store.setAgentError(originWorkspaceId, turn.feedback ? `Thao tác đã được xử lý trên giao diện; đang chờ Agent xác nhận. ${detail}` : detail);
  } finally {
    turn.running = false;
  }
}
