import limits from "./limits.json";

export interface Env {
  MAS_ADMISSION: DurableObjectNamespace;
  ASTRA_MAS_CALLER_TOKEN?: string;
  ASTRA_MAS_GATEWAY_TOKEN?: string;
  ASTRA_MAS_GATEWAY_ACCOUNT_ID?: string;
  ASTRA_MAS_GATEWAY_ID?: string;
  ASTRA_MAS_GATEWAY_BYOK_ALIAS?: string;
  ASTRA_MAS_MODEL?: string;
  ASTRA_MAS_FORWARDING_ENABLED?: string;
  ASTRA_MAS_BUDGETS_ENABLED?: string;
  ASTRA_MAS_ATTEMPT_LIMIT?: string;
  ASTRA_MAS_DAILY?: string;
  ASTRA_MAS_TOKEN_BUDGET?: string;
  ASTRA_MAS_UNTIL?: string;
  ASTRA_MAS_CONCURRENCY?: string;
  ASTRA_MAS_UPSTREAM_MS?: string;
  ASTRA_MAS_OUTPUT_TOKENS?: string;
}

export function bounded(value: string | undefined, maximum: number) {
  if (!value || !/^\d+$/.test(value)) throw new Error("configuration");
  const result = Number(value);
  if (!Number.isSafeInteger(result) || result > maximum) throw new Error("configuration");
  return result;
}

export function policy(env: Env) {
  const budgetSwitch = env.ASTRA_MAS_BUDGETS_ENABLED ?? "true";
  if (!["true", "false"].includes(budgetSwitch)) throw new Error("configuration");
  const budgetsEnabled = budgetSwitch === "true";
  const until = budgetsEnabled ? Date.parse(env.ASTRA_MAS_UNTIL ?? "") : null;
  if (budgetsEnabled && !Number.isFinite(until)) throw new Error("configuration");
  const result = {
    budgetsEnabled,
    attempts: budgetsEnabled ? bounded(env.ASTRA_MAS_ATTEMPT_LIMIT, limits.maxAttempts) : null,
    daily: budgetsEnabled ? bounded(env.ASTRA_MAS_DAILY, limits.maxAttempts) : null,
    tokens: budgetsEnabled ? bounded(env.ASTRA_MAS_TOKEN_BUDGET, limits.maxEstimatedTokens) : null,
    concurrency: bounded(env.ASTRA_MAS_CONCURRENCY, limits.maxConcurrency),
    upstreamMs: bounded(env.ASTRA_MAS_UPSTREAM_MS, limits.maxDeadlineMs),
    outputTokens: bounded(env.ASTRA_MAS_OUTPUT_TOKENS, limits.maxOutputTokens), until,
  };
  if (result.concurrency < 1 || result.upstreamMs < 100 || result.outputTokens < 128) throw new Error("configuration");
  return result;
}

type Ledger = { used: number; tokens: number; days: Record<string, number>; leases: {id: string; until: number}[] };

export class MasAdmission {
  constructor(private state: DurableObjectState, private env: Env) {}

  async fetch(request: Request): Promise<Response> {
    const path = new URL(request.url).pathname;
    const rules = policy(this.env);
    if (request.method === "GET" && path === "/status") {
      const ledger = await this.state.storage.get<Ledger>("ledger");
      const now = Date.now(), day = new Date(now).toISOString().slice(0, 10);
      const used = ledger?.used ?? 0;
      return Response.json({ used, budgetsEnabled: rules.budgetsEnabled, limit: rules.attempts, day, dailyUsed: ledger?.days[day] ?? 0,
        remaining: !rules.budgetsEnabled ? null : rules.until! <= now ? 0 : Math.max(0, Math.min(rules.attempts! - used, rules.daily! - (ledger?.days[day] ?? 0))),
        estimatedTokensReserved: ledger?.tokens ?? 0, estimatedTokenLimit: rules.tokens,
        expiresAt: rules.until === null ? null : new Date(rules.until).toISOString(),
        activeReservations: ledger?.leases.filter(lease => lease.until > now).length ?? 0 });
    }
    if (request.method !== "POST") return Response.json({error:"rejected"}, {status:405});
    const body = await request.json() as { id: string; tokens?: number };
    return this.state.storage.transaction(async storage => {
      const now = Date.now(), day = new Date(now).toISOString().slice(0, 10);
      const ledger = await storage.get<Ledger>("ledger") ?? {used:0, tokens:0, days:{}, leases:[]};
      ledger.leases = ledger.leases.filter(lease => lease.until > now);
      if (path === "/release") {
        ledger.leases = ledger.leases.filter(lease => lease.id !== body.id);
      } else if (path === "/reserve") {
        if (!/^[a-f0-9-]{36}$/.test(body.id ?? "") || !Number.isSafeInteger(body.tokens) || body.tokens! < 0) return Response.json({error:"rejected"}, {status:400});
        const budgetBlocked = rules.budgetsEnabled && (rules.until! <= now || ledger.used >= rules.attempts! ||
          (ledger.days[day] ?? 0) >= rules.daily! || ledger.tokens + body.tokens! > rules.tokens!);
        if (this.env.ASTRA_MAS_FORWARDING_ENABLED !== "true" || budgetBlocked || ledger.leases.length >= rules.concurrency) return Response.json({error:"quota"}, {status:429});
        // Lifetime counters cannot renew at midnight or process restart. No refunds.
        ledger.used++; ledger.tokens += body.tokens!;
        ledger.days[day] = (ledger.days[day] ?? 0) + 1;
        ledger.leases.push({id:body.id, until:now + rules.upstreamMs + limits.leaseBufferMs});
      } else return Response.json({error:"rejected"}, {status:404});
      await storage.put("ledger", ledger);
      return Response.json({accepted:true});
    });
  }
}
