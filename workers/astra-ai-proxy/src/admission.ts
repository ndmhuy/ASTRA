import type { Env } from "./env";
import { bounded } from "./env";
import policies from "../../../src/exam_baseline/resources/agent/workloads.json";

type Operation = "agent" | "mas";
type Counter = { day: string; global: number; agent: number; mas: number; agentTokens?: number; masTokens?: number };
type Reservation = { id: string; expires: number; operation?: Operation };
type Rate = { key: string; count: number; expires: number; operation?: Operation };
type Ledger = { counter: Counter; leases: Reservation[]; rates: Rate[]; turns?: {id: string; expires: number; operation?: Operation}[]; circuits?: Partial<Record<Operation, {failures: number; until: number}>> };

export class Admission {
  constructor(private state: DurableObjectState, private env: Env) {}

  async fetch(request: Request): Promise<Response> {
    if (request.method === "GET" && new URL(request.url).pathname === "/status") {
      const now = Date.now();
      const day = new Date(now).toISOString().slice(0, 10);
      const ledger = await this.state.storage.get<Ledger>("ledger");
      const current = ledger?.counter.day === day ? ledger.counter : undefined;
      const remaining = Math.max(0, Math.min(
        bounded(this.env.ASTRA_GLOBAL_DAILY, 10000) - (current?.global ?? 0),
        bounded(this.env.ASTRA_AGENT_DAILY, 10000) - (current?.agent ?? 0),
      ));
      const active = ledger?.leases.filter(lease => lease.expires > now).length ?? 0;
      return Response.json({ day, remainingAttempts: remaining, activeReservations: active,
        workloads: { agent: { remainingAttempts: remaining,
          activeReservations: ledger?.leases.filter(lease => lease.expires > now && (lease.operation ?? "agent") === "agent").length ?? 0 },
          mas: { enabled: this.env.ASTRA_MAS_FORWARDING_ENABLED === "true",
            remainingAttempts: Math.max(0, bounded(this.env.ASTRA_MAS_DAILY ?? "0", 10000) - (current?.mas ?? 0)),
            activeReservations: ledger?.leases.filter(lease => lease.expires > now && lease.operation === "mas").length ?? 0 } } });
    }
    const body = await request.json() as { release?: string; ip?: string; id?: string; operation?: string; turnId?: string; reservedTokens?: number; outcome?: string };
    // Storage awaits remain inside the transaction. Network calls stay outside.
    return this.state.storage.transaction(async transaction => {
      const now = Date.now();
      const day = new Date(now).toISOString().slice(0, 10);
      const ledger = await transaction.get<Ledger>("ledger") ?? {
        counter: { day, global: 0, agent: 0, mas: 0 }, leases: [], rates: [],
      };
      ledger.leases = ledger.leases.filter(lease => lease.expires > now);
      ledger.rates = ledger.rates.filter(rate => rate.expires > now);
      if (new URL(request.url).pathname === "/outcome") {
        const lease = ledger.leases.find(lease => lease.id === body.id);
        if (!lease) return Response.json({error: "rejected"}, {status: 400});
        const operation = lease.operation ?? "agent";
        ledger.circuits ??= {};
        const circuit = ledger.circuits[operation] ?? {failures: 0, until: 0};
        if (body.outcome === "valid") { circuit.failures = 0; circuit.until = 0; }
        else if (["timeout", "transient", "auth", "model", "quota"].includes(body.outcome ?? "")) {
          circuit.failures++;
          const policy = operation === "agent" ? policies.AGENT_CHAT : policies.MAS_GENERATION;
          if (circuit.failures >= policy.circuitFailures) circuit.until = now + policy.circuitCooldownMs;
        }
        ledger.circuits[operation] = circuit;
        await transaction.put("ledger", ledger);
        return Response.json({recorded: true});
      }
      if (body.release) {
        ledger.leases = ledger.leases.filter(lease => lease.id !== body.release);
        await transaction.put("ledger", ledger);
        return Response.json({ released: true });
      }
      if (!["agent", "mas"].includes(body.operation ?? "") || !body.ip || !body.id ||
          body.id.length > 100 || body.ip.length > 100 ||
          (body.operation === "mas" && this.env.ASTRA_MAS_FORWARDING_ENABLED !== "true") ||
          (body.operation === "agent" && this.env.ASTRA_AGENT_FORWARDING_ENABLED === "false")) {
        return Response.json({ error: "rejected" }, { status: 400 });
      }
      if (ledger.counter.day !== day) ledger.counter = { day, global: 0, agent: 0, mas: 0 };
      const globalLimit = bounded(this.env.ASTRA_GLOBAL_DAILY, 10000);
      const operation = body.operation as Operation;
      if ((ledger.circuits?.[operation]?.until ?? 0) > now) return Response.json({error: "circuit_open"}, {status: 503});
      const agentLimit = bounded(this.env.ASTRA_AGENT_DAILY, 10000);
      const workloadLimit = operation === "agent" ? agentLimit : bounded(this.env.ASTRA_MAS_DAILY ?? "0", 10000);
      const reservedChat = bounded(this.env.ASTRA_CHAT_RESERVED_DAILY ?? String(agentLimit), 10000);
      const tokenLimit = operation === "agent"
        ? bounded(this.env.ASTRA_AGENT_TOKEN_DAILY ?? String(policies.AGENT_CHAT.estimatedDailyTokens), 100000000)
        : bounded(this.env.ASTRA_MAS_TOKEN_DAILY ?? String(policies.MAS_GENERATION.estimatedDailyTokens), 100000000);
      const reservedTokens = body.reservedTokens ?? 0;
      if (!Number.isSafeInteger(reservedTokens) || reservedTokens < 0 || reservedTokens > 1000000 ||
          (body.turnId !== undefined && (typeof body.turnId !== "string" || body.turnId.length > 100))) return Response.json({error: "rejected"}, {status: 400});
      ledger.turns = (ledger.turns ?? []).filter(turn => turn.expires > now);
      if (body.turnId && ledger.turns.some(turn => turn.id === body.turnId && (turn.operation ?? "agent") === operation)) return Response.json({error: "duplicate_turn"}, {status: 409});
      const concurrency = operation === "agent"
        ? bounded(this.env.ASTRA_AGENT_CONCURRENCY ?? this.env.ASTRA_CONCURRENCY, 10)
        : bounded(this.env.ASTRA_MAS_CONCURRENCY ?? "0", 10);
      const ipLimit = operation === "agent" ? bounded(this.env.ASTRA_IP_PER_MINUTE, 60)
        : bounded(this.env.ASTRA_MAS_IP_PER_MINUTE ?? "0", 60);
      const burstLimit = operation === "agent" ? bounded(this.env.ASTRA_GLOBAL_PER_MINUTE, 1000)
        : bounded(this.env.ASTRA_MAS_PER_MINUTE ?? "0", 1000);
      const minute = Math.floor(now / 60000);
      const prefix = operation === "agent" ? "" : "mas:";
      const keys = [prefix + "global:" + minute, prefix + body.ip + ":" + minute];
      const limits = [burstLimit, ipLimit];
      if (keys.some((key, i) => (ledger.rates.find(rate => rate.key === key)?.count ?? 0) >= limits[i]) ||
          ledger.counter.global >= globalLimit || ledger.counter[operation] >= workloadLimit ||
          (operation === "mas" && globalLimit - ledger.counter.global <= Math.max(0, reservedChat - ledger.counter.agent)) ||
          (ledger.counter[operation === "agent" ? "agentTokens" : "masTokens"] ?? 0) + reservedTokens > tokenLimit ||
          ledger.leases.filter(lease => (lease.operation ?? "agent") === operation).length >= concurrency ||
          ledger.turns.filter(turn => (turn.operation ?? "agent") === operation).length >= 256) {
        return Response.json({ error: "quota" }, { status: 429 });
      }
      // Keep admission storage bounded under source IP churn.
      if (ledger.rates.filter(rate => (rate.operation ?? "agent") === operation).length >= 1000) return Response.json({ error: "quota" }, { status: 429 });
      for (const key of keys) {
        const rate = ledger.rates.find(item => item.key === key);
        if (rate) rate.count++;
        else ledger.rates.push({ key, count: 1, operation, expires: (minute + 1) * 60000 });
      }
      ledger.counter.global++;
      ledger.counter[operation]++;
      const tokenKey = operation === "agent" ? "agentTokens" : "masTokens";
      ledger.counter[tokenKey] = (ledger.counter[tokenKey] ?? 0) + reservedTokens;
      if (body.turnId) ledger.turns.push({id: body.turnId, operation, expires: now + 300000});
      const policy = operation === "agent" ? policies.AGENT_CHAT : policies.MAS_GENERATION;
      ledger.leases.push({ id: body.id, operation, expires: now + policy.leaseMs });
      await transaction.put("ledger", ledger);
      return Response.json({ admitted: true, attempts: 1 });
    });
  }
}
