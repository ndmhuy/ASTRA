import { parseDecision, VERSION, type AgentContext } from './contracts.ts';

export async function interpret(
  workspaceId: string, clientMessageId: string, message: string, context: AgentContext, signal: AbortSignal,
) {
  const response = await fetch('/agent/turn', {
    method: 'POST',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json', 'X-Astra-Agent': VERSION },
    body: JSON.stringify({ schemaVersion: VERSION, workspaceId, clientMessageId, message, context }),
    signal: AbortSignal.any([signal, AbortSignal.timeout(5500)]),
  });
  if (!response.ok) throw new Error(response.status === 429 ? 'agent_rate' : 'agent_unavailable');
  return parseDecision(await response.json(), clientMessageId);
}
