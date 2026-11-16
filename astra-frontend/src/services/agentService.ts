import { parseTurnResponse, type ExecutionFeedback, type TurnRequest, type TurnResponse } from '../integration/agentProtocol.ts';

export class AgentHttpError extends Error {
  readonly status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

async function post(path: string, body: unknown, timeoutMs = 10_000): Promise<TurnResponse> {
  const controller = new AbortController();
  const timer = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = payload && typeof payload === 'object' && 'detail' in payload ? String(payload.detail) : `HTTP_${response.status}`;
      throw new AgentHttpError(response.status, detail);
    }
    return parseTurnResponse(payload);
  } finally {
    globalThis.clearTimeout(timer);
  }
}

async function postWithSafeRetry(path: string, body: unknown): Promise<TurnResponse> {
  try {
    return await post(path, body);
  } catch (error) {
    if (error instanceof AgentHttpError && ![502, 503, 504].includes(error.status)) throw error;
    if (!(error instanceof AgentHttpError) && !(error instanceof TypeError) && !(error instanceof DOMException && error.name === 'AbortError')) throw error;
    // The exact body (including request/feedback ID) is reused so server replay protection applies.
    return post(path, body);
  }
}

export const agentService = {
  turn: (request: TurnRequest) => postWithSafeRetry('/agent/turns', request),
  feedback: (feedback: ExecutionFeedback) => postWithSafeRetry('/agent/execution-results', feedback),
};
