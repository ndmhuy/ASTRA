import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Miniflare, convertV4MiniflareOptions } from "miniflare";
import resources from "../src/generated.json" with {type:"json"};
import semanticResources from "../src/semantic.generated.json" with {type:"json"};
import nativeWire from "../../../eval/agent-semantic/native-wire.fixture.json" with {type:"json"};

const bindings = {
  ASTRA_FORWARDING_ENABLED: "true",
  ASTRA_AGENT_GATEWAY_ACCOUNT_ID: "a".repeat(32),
  ASTRA_AGENT_GATEWAY_ID: "astra-gateway",
  ASTRA_AGENT_GATEWAY_TOKEN: "fixture-only-token",
  ASTRA_AGENT_MODEL: "gemini-fixture",
  ASTRA_GLOBAL_DAILY: "3", ASTRA_AGENT_DAILY: "3", ASTRA_MAS_DAILY: "0",
  ASTRA_CONCURRENCY: "1", ASTRA_IP_PER_MINUTE: "2", ASTRA_GLOBAL_PER_MINUTE: "10",
  ASTRA_UPSTREAM_MS: "100", ASTRA_OUTPUT_TOKENS: "512",
};

test("diagnostic session survives restart and UTC rollover without refreshing its allowance", async () => {
  const path = await mkdtemp(join(tmpdir(), "astra-session-"));
  const config = {ASTRA_GLOBAL_DAILY:"12",ASTRA_AGENT_DAILY:"12",ASTRA_IP_PER_MINUTE:"60",
    ASTRA_DIAGNOSTIC_SESSION:"acceptance-fixture",ASTRA_DIAGNOSTIC_LIMIT:"2",
    ASTRA_DIAGNOSTIC_UNTIL:new Date(Date.now()+600000).toISOString()};
  let {mf} = runtime(config,path,"build-test/admission-harness.js");
  try {
    let ns=await mf.getDurableObjectNamespace("ADMISSION"), stub=ns.get(ns.idFromName("global-v1"));
    const reserve=id=>stub.fetch("https://quota/reserve",{method:"POST",body:JSON.stringify({operation:"agent",ip:"test",id})});
    assert.equal((await reserve("first")).status,200);
    await stub.fetch("https://quota/release",{method:"POST",body:JSON.stringify({release:"first"})});
    await mf.dispose();
    ({mf}=runtime(config,path,"build-test/admission-harness.js"));
    ns=await mf.getDurableObjectNamespace("ADMISSION"); stub=ns.get(ns.idFromName("global-v1"));
    assert.equal((await (await stub.fetch("https://quota/status")).json()).diagnostic.used,1);
    await stub.fetch("https://quota/seed",{method:"POST",body:JSON.stringify({
      counter:{day:"2000-01-01",global:2,agent:2,mas:0},leases:[],rates:[],
      sessions:{"acceptance-fixture":{used:1}},
    })});
    assert.equal((await reserve("second")).status,200);
    await stub.fetch("https://quota/release",{method:"POST",body:JSON.stringify({release:"second"})});
    assert.equal((await reserve("third")).status,429);
    const status=await (await stub.fetch("https://quota/status")).json();
    assert.equal(status.diagnostic.used,2); assert.equal(status.remainingAttempts,0);
    const archived=await (await stub.fetch("https://quota/history?day=2000-01-01")).json();
    assert.equal(archived.agent,2);
    await mf.dispose();
    ({mf}=runtime({...config,ASTRA_DIAGNOSTIC_LIMIT:"3"},path));
    ns=await mf.getDurableObjectNamespace("ADMISSION"); stub=ns.get(ns.idFromName("global-v1"));
    assert.equal((await (await stub.fetch("https://quota/status")).json()).diagnostic.remaining,1);
    await mf.dispose();
    ({mf}=runtime({...config,ASTRA_GLOBAL_DAILY:"32",ASTRA_AGENT_DAILY:"32",ASTRA_DIAGNOSTIC_LIMIT:"32"},path,"build-test/admission-harness.js"));
    ns=await mf.getDurableObjectNamespace("ADMISSION"); stub=ns.get(ns.idFromName("global-v1"));
    await stub.fetch("https://quota/seed",{method:"POST",body:JSON.stringify({
      counter:{day:new Date().toISOString().slice(0,10),global:12,agent:12,mas:0},leases:[],rates:[],
      sessions:{"acceptance-fixture":{used:12}},
    })});
    const extended=await (await stub.fetch("https://quota/status")).json();
    assert.equal(extended.diagnostic.used,12); assert.equal(extended.remainingAttempts,20);
    assert.equal((await reserve("owner-thirteenth")).status,200);
    assert.equal((await (await stub.fetch("https://quota/status")).json()).diagnostic.used,13);
  } finally {await mf.dispose();await rm(path,{recursive:true,force:true});}
});

test("expired or oversized diagnostic allowances fail closed without upstream",async()=>{
  for(const override of [
    {ASTRA_DIAGNOSTIC_LIMIT:"8",ASTRA_DIAGNOSTIC_UNTIL:"2000-01-01T00:00:00Z"},
    {ASTRA_DIAGNOSTIC_LIMIT:"33",ASTRA_DIAGNOSTIC_UNTIL:new Date(Date.now()+600000).toISOString()},
  ]) {
    const {mf,mock}=runtime({ASTRA_DIAGNOSTIC_SESSION:"acceptance-fixture",...override});
    try {assert.notEqual((await post(mf)).status,200);mock.assertNoPendingInterceptors();}
    finally {await mf.dispose();}
  }
});
const turn = { schemaVersion: "astra-intent-v1", clientMessageId: "a".repeat(36),
  workspaceId: "b".repeat(36), message: "Natural fixture",
  context: { screen: "start", setup: false } };
function runtime(overrides = {}, persist = false, scriptPath = "build/index.js", semantic = false) {
  const replies = [];
  const mock = {
    get() { return { intercept() { return { reply(status, body, delay = 0) { replies.push({status,body,delay}); } }; } }; },
    assertNoPendingInterceptors() { assert.equal(replies.length, 0); },
  };
  const outbound = async request => {
      assert.equal(new URL(request.url).hostname, "gateway.ai.cloudflare.com");
      assert.equal(request.headers.get("cf-aig-authorization"), "Bearer fixture-only-token");
      assert.equal(request.headers.get("cf-aig-no-wholesale"), "true");
      assert.equal(request.headers.get("cf-aig-max-attempts"), "1");
      assert.equal(request.headers.has("x-goog-api-key"), false);
      const body = await request.json();
      assert.equal(body.generationConfig.thinkingConfig?.thinkingLevel,
        (overrides.ASTRA_AGENT_MODEL ?? bindings.ASTRA_AGENT_MODEL) === "gemini-3.1-flash-lite" ? "MINIMAL" : undefined);
      assert.deepEqual(body.generationConfig.responseJsonSchema, semantic ? semanticResources.providerSchema : resources.providerSchema);
      assert.equal(body.generationConfig.maxOutputTokens, Number(overrides.ASTRA_OUTPUT_TOKENS ?? bindings.ASTRA_OUTPUT_TOKENS));
      if (semantic) assert.deepEqual(body, nativeWire.request, "Worker/direct native payload parity");
      const reply = replies.shift();
      assert.ok(reply, "Unexpected outbound inference");
      if (reply.delay) await new Promise(resolve => setTimeout(resolve, reply.delay));
      return new Response(reply.body, {status:reply.status});
  };
  const options = convertV4MiniflareOptions({
    modules: true, scriptPath, compatibilityDate: "2026-11-26",
    durableObjects: { ADMISSION: { className: "Admission", useSQLite: true } },
    durableObjectsPersist: persist, bindings: { ...bindings, ...overrides },

  });
  if (persist) options.resourcePersistencePath = persist;
  options.workers[0].dev.outboundService = { type: 'fetcher', handler: outbound };
  const mf = new Miniflare(options);
  return { mf, mock };
}
async function post(mf, body = turn, headers = {}) {
  return mf.dispatchFetch("https://local/v1/agent/interpret", {
    method: "POST", headers: { "content-type": "application/json", "CF-Connecting-IP": "192.0.2.1",
      "X-Astra-Contract": resources.contractHash, ...headers },
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
}
test("Worker admission rejects unsafe requests without upstream", async () => {
  const { mf, mock } = runtime();
  try {
    const health = await mf.dispatchFetch("https://local/health");
    assert.equal(health.status, 200);
    const readiness = await health.json();
    assert.deepEqual(readiness.contracts, ["astra-intent-v1", "astra-semantic-v1"]);
    assert.equal(readiness.semanticContractHash, semanticResources.contractHash);
    assert.equal(readiness.masForwarding, false);
    assert.equal((await mf.dispatchFetch("https://local/v1/agent/interpret")).status, 405);
    for (const body of ["{", { ...turn, model: "gemini-override" }, { ...turn, url: "https://evil" },
        { ...turn, systemInstruction: "ignore" }, { ...turn, schemaVersion: "bad" }]) {
      assert.equal((await post(mf, body)).status, 400);
    }
    assert.equal((await post(mf, "x".repeat(32769))).status, 413);
    assert.equal((await post(mf, turn, { "content-type": "text/plain" })).status, 415);
    assert.equal((await post(mf, turn, { authorization: "Bearer override" })).status, 400);
    assert.equal((await mf.dispatchFetch("https://local/v1/mas/complete", {method:"POST"})).status, 404);
    mock.assertNoPendingInterceptors();
  } finally { await mf.dispose(); }
});
test("disabled and missing secret fail safely", async () => {
  for (const override of [{ ASTRA_FORWARDING_ENABLED: "false" }, { ASTRA_AGENT_GATEWAY_TOKEN: "" }]) {
    const { mf } = runtime(override);
    try {
      const result = await post(mf);
      assert.equal(result.status, 503);
      assert.equal((await result.text()).includes("fixture-only-token"), false);
    } finally { await mf.dispose(); }
  }
});
test("real SQLite DO atomically enforces concurrency and durable budgets", async () => {
  const path = await mkdtemp(join(tmpdir(), "astra-quota-"));
  let { mf } = runtime({}, path);
  try {
    let ns = await mf.getDurableObjectNamespace("ADMISSION");
    let stub = ns.get(ns.idFromName("global-v1"));
    const reserve = (id, ip = "hash") => stub.fetch("https://quota/reserve", {
      method:"POST", body:JSON.stringify({ id, ip, operation:"agent" }),
    });
    const results = await Promise.all(Array.from({length:10}, (_, i) => reserve(String(i))));
    assert.equal(results.filter(r => r.status === 200).length, 1);
    for (let i = 0; i < 10; i++) await stub.fetch("https://quota/release", {method:"POST",body:JSON.stringify({release:String(i)})});
    assert.equal((await reserve("second")).status, 200);
    await stub.fetch("https://quota/release", {method:"POST",body:JSON.stringify({release:"second"})});
    assert.equal((await reserve("ip-throttled")).status, 429);
    assert.equal((await reserve("third","other")).status, 200);
    await mf.dispose();
    ({ mf } = runtime({}, path));
    ns = await mf.getDurableObjectNamespace("ADMISSION");
    stub = ns.get(ns.idFromName("global-v1"));
    assert.equal((await reserve("restart","new-ip")).status, 429);
    assert.equal((await stub.fetch("https://quota/reserve", {method:"POST",
      body:JSON.stringify({id:"mas",ip:"hash",operation:"mas"})})).status,400);
  } finally { await mf.dispose(); await rm(path, {recursive:true,force:true}); }
});
test("native BYOK result is validated and sensitive errors are omitted", async () => {
  const { mf, mock } = runtime();
  const pool = mock.get("https://gateway.ai.cloudflare.com");
  pool.intercept({path:/generateContent$/, method:"POST"}).reply(200, JSON.stringify({
    candidates:[{finishReason:"STOP",content:{parts:[{text:JSON.stringify({
      kind:"clarify",intents:[],intake:{mode:"request",family:"thpt"},title:"Soạn đề THPT",
    })}]}}],
  }));
  pool.intercept({path:/generateContent$/, method:"POST"}).reply(401,"fixture-only-token");
  try {
    const first = await post(mf);
    assert.equal(first.status,200);
    const result=await first.json();
    assert.equal(result.decision.intake.family,"thpt");
    assert.equal(result.evidence.attempts,1);
    const second=await post(mf);
    assert.equal(second.status,502);
    const error=await second.text();
    assert.equal(error.includes("fixture-only-token"),false);
    assert.equal(JSON.parse(error).error,"auth");
    mock.assertNoPendingInterceptors();
  } finally { await mf.dispose(); }
});

test("expired leases recover and UTC rollover preserves attempts until reset", async () => {
  const { mf } = runtime({}, false, "build-test/admission-harness.js");
  try {
    const ns = await mf.getDurableObjectNamespace("ADMISSION");
    const stub = ns.get(ns.idFromName("global-v1"));
    const seed = ledger => stub.fetch("https://quota/seed", {method:"POST",body:JSON.stringify(ledger)});
    const reserve = () => stub.fetch("https://quota/reserve", {method:"POST",
      body:JSON.stringify({operation:"agent",id:"new",ip:"hash"})});
    const today = new Date().toISOString().slice(0,10);
    await seed({counter:{day:today,global:2,agent:2,mas:0},
      leases:[{id:"expired",expires:Date.now()-1}],rates:[]});
    assert.equal((await reserve()).status,200);
    await seed({counter:{day:today,global:3,agent:3,mas:0},leases:[],rates:[]});
    assert.equal((await reserve()).status,429);
    await seed({counter:{day:"2000-01-01",global:3,agent:3,mas:0},leases:[],rates:[]});
    assert.equal((await reserve()).status,200);
  } finally { await mf.dispose(); }
});
test("Agent ceiling applies separately from global capacity", async () => {
  const { mf } = runtime({ASTRA_AGENT_DAILY:"0",ASTRA_GLOBAL_DAILY:"10"});
  try {
    const ns = await mf.getDurableObjectNamespace("ADMISSION");
    const result = await ns.get(ns.idFromName("global-v1")).fetch("https://quota/reserve",
      {method:"POST",body:JSON.stringify({operation:"agent",id:"no",ip:"hash"})});
    assert.equal(result.status,429);
  } finally { await mf.dispose(); }
});

test("invalid upstream semantics consume the attempt and fail closed", async () => {
  const { mf, mock } = runtime({ASTRA_GLOBAL_DAILY:"1"});
  mock.get().intercept().reply(200, JSON.stringify({candidates:[{
    finishReason:"STOP",content:{parts:[{text:JSON.stringify({kind:"task",intents:[{id:"INVENTED",args:{}}]})}]},
  }]}));
  try {
    const invalid = await post(mf);
    assert.equal((await invalid.json()).error,"schema");
    assert.equal((await post(mf)).status,429);
    mock.assertNoPendingInterceptors();
  } finally { await mf.dispose(); }
});

test("timed-out upstream is charged and cannot retry past the daily ceiling", async () => {
  const { mf, mock } = runtime({ASTRA_GLOBAL_DAILY:"1"});
  mock.get().intercept().reply(200, "{}", 300);
  try {
    const result = await post(mf);
    assert.equal((await result.json()).error,"timeout");
    assert.equal((await post(mf)).status,429);
    mock.assertNoPendingInterceptors();
  } finally { await mf.dispose(); }
});
test("admission failure blocks upstream forwarding", async () => {
  // Invalid quota configuration forces admission failure before the upstream request.
  const broken = runtime({ASTRA_GLOBAL_DAILY:"invalid"});
  try {
    const result = await post(broken.mf);
    assert.equal(result.status,503);
    broken.mock.assertNoPendingInterceptors();
  } finally { await broken.mf.dispose(); }
});

test("quota status is read-only and reflects the persisted remaining allowance", async () => {
  const { mf } = runtime();
  try {
    const before = await (await mf.dispatchFetch("https://local/health")).json();
    assert.equal(before.quota.remainingAttempts,3);
    const again = await (await mf.dispatchFetch("https://local/health")).json();
    assert.equal(again.quota.remainingAttempts,3);
    const ns=await mf.getDurableObjectNamespace("ADMISSION");
    const stub=ns.get(ns.idFromName("global-v1"));
    await stub.fetch("https://quota/reserve",{method:"POST",body:JSON.stringify({id:"one",ip:"hash",operation:"agent"})});
    const after=await (await mf.dispatchFetch("https://local/health")).json();
    assert.equal(after.quota.remainingAttempts,2);
  } finally { await mf.dispose(); }
});

test("incomplete and invalid semantic results retain diagnostic stages and fail closed", async () => {
  for (const candidate of [
    {finishReason:"MAX_TOKENS",content:{parts:[{text:"{"}]}},
    {finishReason:"STOP",content:{parts:[{text:"not JSON"}]}},
    {finishReason:"STOP",content:{parts:[{text:JSON.stringify({kind:"clarify",intents:[],guidance:"invented"})}]}},
  ]) {
    const {mf,mock}=runtime();
    mock.get().intercept().reply(200,JSON.stringify({candidates:[candidate]}));
    try {
      const result=await post(mf);
      assert.equal((await result.json()).error,"schema");
      mock.assertNoPendingInterceptors();
    } finally { await mf.dispose(); }
  }
});

test("documented Gemini envelope extraction and optional normalization", async () => {
  const cases = [
    {candidates:[{finishReason:"STOP",content:{role:"model",parts:[{text:JSON.stringify({
      kind:"clarify",intake:{mode:"request",family:"thpt"},guidance:null,title:null,
    })}]}}]},
    {candidates:[{finishReason:"STOP",content:{parts:[
      {thought:true,text:"fixture thought omitted"}, {text:'{"kind":"clarify",'},
      {text:'"intents":[],"intake":{"mode":"request","family":"thpt"}}',thoughtSignature:"fixture-metadata"},
    ]}}]},
  ];
  for (const body of cases) {
    const {mf,mock}=runtime();
    mock.get().intercept().reply(200,JSON.stringify(body));
    try {
      const result=await post(mf);
      assert.equal(result.status,200);
      const payload=await result.json();
      assert.equal(payload.decision.intake.family,"thpt");
      assert.deepEqual(payload.decision.intents,[]);
      assert.equal(Object.hasOwn(payload.decision,"guidance"),false);
    } finally {await mf.dispose();}
  }
});
test("blocked, absent, empty, truncated and invalid required outputs are rejected", async () => {
  const cases=[
    {promptFeedback:{blockReason:"SAFETY"}},
    {candidates:[]},
    {candidates:[{finishReason:"STOP",content:{parts:[]}}]},
    {candidates:[{finishReason:"STOP",content:{parts:[{thought:true,text:"private thought"}]}}]},
    ...[
      '{"kind":', '{}', '{"kind":"bad"}',
      '{"kind":"task","intents":[{"id":"SET_VIEW","args":{}}]}',
      '{"kind":"task","intents":[{"id":"SET_VIEW","args":{"view":"invented"}}]}',
      '{"kind":"task","intents":[{"id":"STATUS","args":{"view":"paper"}}]}',
    ].map(text=>({candidates:[{finishReason:"STOP",content:{parts:[{text}]}}]})),
  ];
  for(const body of cases) {
    const {mf,mock}=runtime();
    mock.get().intercept().reply(200,JSON.stringify(body));
    try {assert.equal((await (await post(mf)).json()).error,"schema");}
    finally {await mf.dispose();}
  }
});
test("HTTP quota and overload stay separate from schema failures", async () => {
  for(const [status,reason] of [[429,"quota"],[503,"transient"]]) {
    const {mf,mock}=runtime();
    mock.get().intercept().reply(status,JSON.stringify({error:{code:status,status:status===429?"RESOURCE_EXHAUSTED":"UNAVAILABLE",message:"private fixture must not be logged"}}));
    try {assert.equal((await (await post(mf)).json()).error,reason);}
    finally {await mf.dispose();}
  }
});
test("all 34 existing intent contracts survive the common provider argument schema",async()=>{
  const {mf,mock}=runtime({ASTRA_AGENT_DAILY:"40",ASTRA_GLOBAL_DAILY:"40",
    ASTRA_IP_PER_MINUTE:"60",ASTRA_GLOBAL_PER_MINUTE:"100",ASTRA_AGENT_TOKEN_DAILY:"2000000"});
  const example = schema => schema.enum?.[0] ?? (schema.type==="integer"?1:schema.type==="boolean"?true:"fixture");
  try {
    for(const variant of resources.outputSchema.properties.intents.items.anyOf) {
      const id=variant.properties.id.enum[0];
      const spec=variant.properties.args;
      const args=Object.fromEntries(spec.required.map(key=>[key,example(spec.properties[key])]));
      mock.get().intercept().reply(200,JSON.stringify({candidates:[{finishReason:"STOP",content:{parts:[{text:JSON.stringify({kind:"task",intents:[{id,args}]})}]}}]}));
      const result=await post(mf);
      assert.equal(result.status,200,id);
      assert.equal((await result.json()).decision.intents[0].id,id);
    }
    mock.assertNoPendingInterceptors();
  } finally {await mf.dispose();}
});

test("provider schema excludes cross-field combinations rejected by the application", async()=>{
  for(const proposal of [
    {kind:"task",intents:[],intake:{mode:"request",family:"thpt"}},
    {kind:"clarify",intents:[],intake:{mode:"request",family:"thpt"},guidance:"start"},
    {kind:"task",intents:[{id:"OPEN_SETUP",args:{}}],intake:{mode:"request",family:"thpt"}},
  ]) {
    const {mf,mock}=runtime();
    mock.get().intercept().reply(200,JSON.stringify({candidates:[{finishReason:"STOP",content:{parts:[{text:JSON.stringify(proposal)}]}}]}));
    try {assert.equal((await (await post(mf)).json()).error,"schema");}
    finally {await mf.dispose();}
  }
});

async function postSemantic(mf, body = turn) {
  return mf.dispatchFetch("https://local/v2/agent/interpret", {
    method: "POST", headers: {"content-type":"application/json", "CF-Connecting-IP":"192.0.2.1",
      "X-Astra-Contract":semanticResources.contractHash}, body:JSON.stringify(body),
  });
}

test("v2 native semantics need no executable kind or clarification invariant", async () => {
  const {mf,mock} = runtime({}, false, "build/index.js", true);
  const frame = {dialogueAct:"REQUEST", goals:[{goal:"PREPARE_EXAM",parameters:{family:"thpt"}}],title:42};
  mock.get().intercept().reply(200, JSON.stringify({candidates:[{finishReason:"STOP",content:{parts:[{text:JSON.stringify(frame)}]}}]}));
  try {
    const reply = await postSemantic(mf);
    assert.equal(reply.status,200);
    const payload = await reply.json();
    assert.equal(payload.frame.goals[0].parameters.family,"thpt");
    assert.equal(payload.frame.title,undefined);
    assert.equal(payload.schemaVersion,"astra-semantic-v1");
    assert.equal(payload.decision,undefined);
    assert.equal((await postSemantic(mf)).status,409);
    mock.assertNoPendingInterceptors();
  } finally { await mf.dispose(); }
});

test("v2 semantic mismatch reports safe field paths and consumes one attempt", async () => {
  const {mf,mock} = runtime({}, false, "build/index.js", true);
  mock.get().intercept().reply(200, JSON.stringify({candidates:[{finishReason:"STOP",content:{parts:[{text:JSON.stringify({
    dialogueAct:"REQUEST",goals:[{goal:"PREPARE_EXAM",parameters:{family:"invented"}}],
  })}]}}]}));
  try {
    const reply = await postSemantic(mf);
    const payload=await reply.json();
    assert.equal(reply.status,502);
    assert.equal(payload.error,"schema");
    assert.ok(payload.diagnostics.schemaStage);
    assert.ok(payload.diagnostics.validationPaths.length);
    assert.equal(JSON.stringify(payload).includes("fixture-only-token"),false);
    assert.equal((await postSemantic(mf)).status,409);
  } finally { await mf.dispose(); }
});

test("MAS cannot consume reserved Chat attempts, concurrency or rate capacity", async () => {
  const {mf} = runtime({ASTRA_GLOBAL_DAILY:"3",ASTRA_AGENT_DAILY:"2",ASTRA_MAS_DAILY:"3",
    ASTRA_CHAT_RESERVED_DAILY:"2",ASTRA_MAS_FORWARDING_ENABLED:"true",ASTRA_MAS_CONCURRENCY:"1",
    ASTRA_MAS_PER_MINUTE:"3",ASTRA_MAS_IP_PER_MINUTE:"3"});
  try {
    const ns=await mf.getDurableObjectNamespace("ADMISSION");
    const stub=ns.get(ns.idFromName("global-v1"));
    const reserve=(operation,id) => stub.fetch("https://quota/reserve",{method:"POST",body:JSON.stringify({operation,id,ip:"same"})});
    assert.equal((await reserve("mas","m1")).status,200);
    assert.equal((await reserve("mas","m2")).status,429);
    assert.equal((await reserve("agent","a1")).status,200);
    await stub.fetch("https://quota/release",{method:"POST",body:JSON.stringify({release:"m1"})});
    assert.equal((await reserve("mas","m3")).status,429);
    await stub.fetch("https://quota/release",{method:"POST",body:JSON.stringify({release:"a1"})});
    assert.equal((await reserve("agent","a2")).status,200);
    const health=await (await stub.fetch("https://quota/status")).json();
    assert.equal(health.workloads.agent.activeReservations,1);
    assert.equal(health.workloads.mas.activeReservations,0);
  } finally { await mf.dispose(); }
});

test("independent token reservations and circuit state fail closed", async () => {
  const {mf} = runtime({ASTRA_GLOBAL_DAILY:"10",ASTRA_AGENT_DAILY:"5",ASTRA_MAS_DAILY:"5",
    ASTRA_CHAT_RESERVED_DAILY:"2",ASTRA_AGENT_TOKEN_DAILY:"100",ASTRA_MAS_TOKEN_DAILY:"10",
    ASTRA_MAS_FORWARDING_ENABLED:"true",ASTRA_MAS_CONCURRENCY:"1",ASTRA_MAS_PER_MINUTE:"5",ASTRA_MAS_IP_PER_MINUTE:"5"});
  try {
    const ns=await mf.getDurableObjectNamespace("ADMISSION"), stub=ns.get(ns.idFromName("global-v1"));
    const reserve=(operation,id,reservedTokens=0) => stub.fetch("https://quota/reserve",{method:"POST",body:JSON.stringify({operation,id,ip:"same",reservedTokens})});
    assert.equal((await reserve("mas","too-many-tokens",11)).status,429);
    for (const id of ["failure1","failure2"]) {
      assert.equal((await reserve("mas",id,1)).status,200);
      await stub.fetch("https://quota/outcome",{method:"POST",body:JSON.stringify({id,outcome:"timeout"})});
      await stub.fetch("https://quota/release",{method:"POST",body:JSON.stringify({release:id})});
    }
    assert.equal((await reserve("mas","circuit")).status,503);
    assert.equal((await reserve("agent","chat",100)).status,200);
    // Exhausting Chat tokens does not release or terminate another workload's lease.
    assert.equal((await reserve("agent","chat2",1)).status,429);
  } finally { await mf.dispose(); }
});
