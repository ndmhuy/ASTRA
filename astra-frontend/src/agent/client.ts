import type { AgentTurnResponse, UiContextSnapshot } from './contracts';

export class AgentTransportError extends Error {
  readonly code: string;
  constructor(code: string, message: string) { super(message); this.code = code; }
}

export class AgentClient {
  private token: string | null = null;

  async interpret(message: string, context: UiContextSnapshot): Promise<AgentTurnResponse> {
    if (!this.token) await this.openSession();
    const turnId = crypto.randomUUID();
    const response = await fetch('/agent/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-ASTRA-Agent-Session': this.token || '' },
      body: JSON.stringify({ turnId, message, context }),
    });
    if (response.status === 401) {
      this.token = null;
      throw new AgentTransportError('SESSION_EXPIRED', 'Phiên Agent đã hết hạn. Vui lòng gửi lại yêu cầu.');
    }
    if (!response.ok) throw new AgentTransportError('AGENT_UNAVAILABLE', 'Dịch vụ Agent cục bộ chưa sẵn sàng.');
    return response.json() as Promise<AgentTurnResponse>;
  }

  private async openSession(): Promise<void> {
    const response = await fetch('/agent/session', { method: 'POST' });
    if (!response.ok) throw new AgentTransportError('AGENT_UNAVAILABLE', 'Dịch vụ Agent cục bộ chưa sẵn sàng.');
    const body = await response.json() as { token?: string };
    if (!body.token) throw new AgentTransportError('INVALID_SESSION', 'Dịch vụ Agent không cấp được phiên an toàn.');
    this.token = body.token;
  }
}
