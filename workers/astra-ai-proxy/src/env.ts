export interface Env {
  ADMISSION: DurableObjectNamespace;
  ASTRA_AGENT_GATEWAY_TOKEN?: string;
  ASTRA_AGENT_GATEWAY_ACCOUNT_ID?: string;
  ASTRA_AGENT_GATEWAY_ID?: string;
  ASTRA_AGENT_GATEWAY_BYOK_ALIAS?: string;
  ASTRA_AGENT_MODEL?: string;
  ASTRA_FORWARDING_ENABLED?: string;
  ASTRA_GLOBAL_DAILY?: string;
  ASTRA_AGENT_DAILY?: string;
  ASTRA_MAS_DAILY?: string;
  ASTRA_CONCURRENCY?: string;
  ASTRA_IP_PER_MINUTE?: string;
  ASTRA_GLOBAL_PER_MINUTE?: string;
  ASTRA_UPSTREAM_MS?: string;
  ASTRA_OUTPUT_TOKENS?: string;
  ASTRA_AGENT_FORWARDING_ENABLED?: string;
  ASTRA_MAS_FORWARDING_ENABLED?: string;
  ASTRA_AGENT_CONCURRENCY?: string;
  ASTRA_MAS_CONCURRENCY?: string;
  ASTRA_CHAT_RESERVED_DAILY?: string;
  ASTRA_AGENT_TOKEN_DAILY?: string;
  ASTRA_MAS_TOKEN_DAILY?: string;
  ASTRA_MAS_PER_MINUTE?: string;
  ASTRA_MAS_IP_PER_MINUTE?: string;
}

export function bounded(value: string | undefined, maximum: number): number {
  if (!value || !/^\d+$/.test(value)) throw new Error("configuration");
  const number = Number(value);
  if (!Number.isSafeInteger(number) || number > maximum) throw new Error("configuration");
  return number;
}
