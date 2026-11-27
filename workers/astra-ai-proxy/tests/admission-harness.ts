// Local test entry only. Production exports the original Admission class.
import { Admission as ProductionAdmission } from "../src/admission";
import type { Env } from "../src/env";

export class Admission extends ProductionAdmission {
  constructor(private testState: DurableObjectState, env: Env) { super(testState, env); }
  async fetch(request: Request): Promise<Response> {
    if (new URL(request.url).pathname === "/history") {
      return Response.json(await this.testState.storage.get("daily-history-v1:" + new URL(request.url).searchParams.get("day")) ?? null);
    }
    if (new URL(request.url).pathname === "/seed") {
      await this.testState.storage.put("ledger", await request.json());
      return new Response("seeded");
    }
    return super.fetch(request);
  }
}
export default { fetch: () => new Response("test only") };
