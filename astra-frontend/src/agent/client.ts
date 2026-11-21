import type { AgentTurnResponse, UiContextSnapshot } from './contracts';

export class AgentTransportError extends Error {
  readonly code: string;
  constructor(code: string, message: string) { super(message); this.code = code; }
}

const AGENT_UNAVAILABLE_MESSAGE =
  'Trợ lý ASTRA tạm thời chưa sẵn sàng. Bạn vẫn có thể thao tác trực tiếp bằng các nút trên giao diện.';

export class AgentClient {
  private token: string | null = null;

  async interpret(message: string, context: UiContextSnapshot): Promise<AgentTurnResponse> {
    if (!this.token) await this.openSession();
    const turnId = crypto.randomUUID();
    let response: Response;
    try {
      response = await fetch('/agent/interpret', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-ASTRA-Agent-Session': this.token || '' },
        body: JSON.stringify({ turnId, message, context }),
      });
    } catch {
      throw new AgentTransportError('AGENT_UNAVAILABLE', AGENT_UNAVAILABLE_MESSAGE);
    }
    if (response.status === 401) {
      this.token = null;
      throw new AgentTransportError('SESSION_EXPIRED', 'Phiên trò chuyện vừa được làm mới. Bạn vui lòng gửi lại yêu cầu.');
    }
    if (!response.ok) {
      let error = { code: 'AGENT_UNAVAILABLE', message: AGENT_UNAVAILABLE_MESSAGE };
      try {
        const body = await response.json() as { error?: { code?: string; message?: string } };
        error = {
          code: body.error?.code || error.code,
          message: body.error?.message || error.message,
        };
      } catch { /* Preserve the safe transport error when no JSON envelope exists. */ }
      throw new AgentTransportError(error.code, error.message);
    }
    return response.json() as Promise<AgentTurnResponse>;
  }

  private async openSession(): Promise<void> {
    let response: Response;
    try {
      response = await fetch('/agent/session', { method: 'POST' });
    } catch {
      throw new AgentTransportError('AGENT_UNAVAILABLE', AGENT_UNAVAILABLE_MESSAGE);
    }
    if (!response.ok) throw new AgentTransportError('AGENT_UNAVAILABLE', AGENT_UNAVAILABLE_MESSAGE);
    const body = await response.json() as { token?: string };
    if (!body.token) throw new AgentTransportError('INVALID_SESSION', AGENT_UNAVAILABLE_MESSAGE);
    this.token = body.token;
  }
}
