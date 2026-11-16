import { agentService } from '../services/agentService';
import type { ExamSessions } from '../state/examSessions';
import type { ScreenContext, TurnRequest } from './agentProtocol';
import { UiExecutor } from './uiExecutor';

export interface AgentControllerDependencies {
  store: ExamSessions;
  getContext: () => ScreenContext;
  executor: UiExecutor;
}

export async function runAgentTurn(originWorkspaceId: string, message: string, dependencies: AgentControllerDependencies) {
  const { store, getContext, executor } = dependencies;
  const request: TurnRequest = {
    schema_version: 'agent-turn/0.1',
    request_id: crypto.randomUUID(),
    conversation_id: `workspace:${originWorkspaceId}`,
    workspace_session_id: originWorkspaceId,
    message,
    screen_context: getContext(),
  };
  store.appendUserMessage(originWorkspaceId, message);
  store.setAgentPending(originWorkspaceId, true);
  try {
    let response = await agentService.turn(request);
    if (response.request_id !== request.request_id || response.conversation_id !== request.conversation_id) throw new Error('RESPONSE_CORRELATION_FAILED');
    if (response.kind === 'action_plan') {
      const plan = response.data.plan;
      if (!plan || plan.conversation_id !== request.conversation_id) throw new Error('PLAN_CORRELATION_FAILED');
      const results = await executor.execute(plan);
      response = await agentService.feedback({
        feedback_id: crypto.randomUUID(),
        conversation_id: request.conversation_id,
        workspace_session_id: originWorkspaceId,
        original_request_id: request.request_id,
        results,
      });
    }
    store.appendAssistantMessage(originWorkspaceId, response.reply);
    store.setAgentPending(originWorkspaceId, false);
  } catch (error) {
    const messageText = error instanceof Error ? error.message : 'UNKNOWN_AGENT_ERROR';
    store.setAgentError(originWorkspaceId, `Chưa thể xử lý yêu cầu qua Agent (${messageText}). Bạn có thể thử gửi lại.`);
  }
}
