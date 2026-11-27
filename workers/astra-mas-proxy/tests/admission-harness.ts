import { MasAdmission as Base, type Env } from "../src/admission";
export class MasAdmission extends Base {
  constructor(private testState: DurableObjectState, env: Env) { super(testState,env); }
  async fetch(request: Request): Promise<Response> {
    if (new URL(request.url).pathname === "/ledger") return Response.json(await this.testState.storage.get("ledger"));
    if (new URL(request.url).pathname === "/seed") {
      await this.testState.storage.put("ledger",await request.json());
      return Response.json({seeded:true});
    }
    return super.fetch(request);
  }
}
export default {fetch:() => new Response("test harness only")};
