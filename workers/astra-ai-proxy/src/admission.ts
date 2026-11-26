import type { Env } from "./env";
import { bounded } from "./env";

type Counter = { day: string; global: number; agent: number; mas: number };
type Reservation = { id: string; expires: number };
type Rate = { key: string; count: number; expires: number };
type Ledger = { counter: Counter; leases: Reservation[]; rates: Rate[] };

export class Admission {
  constructor(private state: DurableObjectState, private env: Env) {}

  async fetch(request: Request): Promise<Response> {
    const body = await request.json() as { release?: string; ip?: string; id?: string; operation?: string };
    // Storage awaits remain inside the transaction. Network calls stay outside.
    return this.state.storage.transaction(async transaction => {
      const now = Date.now();
      const day = new Date(now).toISOString().slice(0, 10);
      const ledger = await transaction.get<Ledger>("ledger") ?? {
        counter: { day, global: 0, agent: 0, mas: 0 }, leases: [], rates: [],
      };
      ledger.leases = ledger.leases.filter(lease => lease.expires > now);
      ledger.rates = ledger.rates.filter(rate => rate.expires > now);
      if (body.release) {
        ledger.leases = ledger.leases.filter(lease => lease.id !== body.release);
        await transaction.put("ledger", ledger);
        return Response.json({ released: true });
      }
      if (body.operation !== "agent" || !body.ip || !body.id) {
        return Response.json({ error: "rejected" }, { status: 400 });
      }
      if (ledger.counter.day !== day) ledger.counter = { day, global: 0, agent: 0, mas: 0 };
      const globalLimit = bounded(this.env.ASTRA_GLOBAL_DAILY, 10000);
      const agentLimit = bounded(this.env.ASTRA_AGENT_DAILY, 10000);
      const concurrency = bounded(this.env.ASTRA_CONCURRENCY, 10);
      const ipLimit = bounded(this.env.ASTRA_IP_PER_MINUTE, 60);
      const burstLimit = bounded(this.env.ASTRA_GLOBAL_PER_MINUTE, 1000);
      const minute = Math.floor(now / 60000);
      const keys = ["global:" + minute, body.ip + ":" + minute];
      const limits = [burstLimit, ipLimit];
      if (keys.some((key, i) => (ledger.rates.find(rate => rate.key === key)?.count ?? 0) >= limits[i]) ||
          ledger.counter.global >= globalLimit || ledger.counter.agent >= agentLimit ||
          ledger.leases.length >= concurrency) {
        return Response.json({ error: "quota" }, { status: 429 });
      }
      // Keep admission storage bounded under source IP churn.
      if (ledger.rates.length > 2000) return Response.json({ error: "quota" }, { status: 429 });
      for (const key of keys) {
        const rate = ledger.rates.find(item => item.key === key);
        if (rate) rate.count++;
        else ledger.rates.push({ key, count: 1, expires: (minute + 1) * 60000 });
      }
      ledger.counter.global++;
      ledger.counter.agent++;
      ledger.leases.push({ id: body.id, expires: now + 45000 });
      await transaction.put("ledger", ledger);
      return Response.json({ admitted: true, attempts: 1 });
    });
  }
}
