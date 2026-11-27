import assert from "node:assert/strict";
import test from "node:test";
import { randomUUID } from "node:crypto";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { Miniflare, convertV4MiniflareOptions } from "miniflare";

const bindings = {
  ASTRA_MAS_CALLER_TOKEN:"a".repeat(64),ASTRA_MAS_GATEWAY_TOKEN:"fixture-gateway-token",
  ASTRA_MAS_GATEWAY_ACCOUNT_ID:"b".repeat(32),ASTRA_MAS_GATEWAY_ID:"astra-mas-gateway",
  ASTRA_MAS_GATEWAY_BYOK_ALIAS:"independent-mas",ASTRA_MAS_MODEL:"gemini-academic-fixture",
  ASTRA_MAS_FORWARDING_ENABLED:"true",ASTRA_MAS_ATTEMPT_LIMIT:"5",ASTRA_MAS_DAILY:"5",
  ASTRA_MAS_TOKEN_BUDGET:"1000000",ASTRA_MAS_UNTIL:new Date(Date.now()+600000).toISOString(),
  ASTRA_MAS_CONCURRENCY:"1",ASTRA_MAS_UPSTREAM_MS:"1000",ASTRA_MAS_OUTPUT_TOKENS:"8192",
};
const payload = {
  model:bindings.ASTRA_MAS_MODEL,messages:[{role:"system",content:"unchanged academic prompt"},
    {role:"user",content:"synthetic academic data"}],max_tokens:8192,
  response_format:{type:"json_schema",json_schema:{name:"exam_response",schema:{type:"object",properties:{value:{type:"integer"}}}}},
};
const responseText = JSON.stringify({id:"synthetic",model:bindings.ASTRA_MAS_MODEL,
  choices:[{finish_reason:"stop",message:{content:'{"value":42}'}}],usage:{prompt_tokens:123,completion_tokens:45,total_tokens:168}});

function runtime(overrides={},persist=false,scriptPath="build/index.js") {
  const queue=[], observed=[];
  const options=convertV4MiniflareOptions({modules:true,scriptPath,compatibilityDate:"2026-11-26",
    durableObjects:{MAS_ADMISSION:{className:"MasAdmission",useSQLite:true}},
    durableObjectsPersist:persist,bindings:{...bindings,...overrides}});
  if(persist) options.resourcePersistencePath=persist;
  options.workers[0].dev.outboundService={type:"fetcher",handler:async request=>{
    observed.push({url:request.url,headers:Object.fromEntries(request.headers),body:await request.text()});
    const item=queue.shift(); assert.ok(item,"Unexpected outbound MAS inference");
    if(item.delay) await new Promise(resolve=>setTimeout(resolve,item.delay));
    return new Response(item.text??responseText,{status:item.status??200,headers:{"content-type":"application/json"}});
  }};
  return {mf:new Miniflare(options),queue,observed};
}
const post=(mf,body=payload,headers={})=>mf.dispatchFetch("https://local/v1/chat/completions",{
  method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+bindings.ASTRA_MAS_CALLER_TOKEN,"X-Astra-MAS-Stage":"composer",...headers},
  body:typeof body==="string"?body:JSON.stringify(body),
});
const health=async mf=>(await(await mf.dispatchFetch("https://local/health")).json());

test("revocable caller authorization and disabled rollout spend no upstream attempts",async()=>{
  const {mf,observed}=runtime({ASTRA_MAS_FORWARDING_ENABLED:"false"});
  try {
    assert.equal((await post(mf,payload,{Authorization:"Bearer incorrect"})).status,401);
    assert.equal((await post(mf,payload,{Origin:"https://untrusted.example"})).status,401);
    assert.equal((await post(mf)).status,503);
    assert.equal((await health(mf)).quota.used,0);
    assert.equal(observed.length,0);
  } finally{await mf.dispose();}
});

test("fixed BYOK passthrough preserves Chat Completions schema and raw response",async()=>{
  const {mf,queue,observed}=runtime(); queue.push({});
  try {
    const response=await post(mf);
    assert.equal(response.status,200);assert.equal(await response.text(),responseText);
    assert.match(response.headers.get("X-Astra-MAS-Request-ID"),/^[a-f0-9-]{36}$/);
    assert.equal(observed.length,1);
    const request=observed[0];
    assert.equal(request.url,"https://gateway.ai.cloudflare.com/v1/"+"b".repeat(32)+"/astra-mas-gateway/google-ai-studio/v1beta/openai/chat/completions");
    assert.equal(request.body,JSON.stringify(payload));
    assert.equal(request.headers["cf-aig-authorization"],"Bearer fixture-gateway-token");
    assert.equal(request.headers["cf-aig-byok-alias"],"independent-mas");
    assert.equal(request.headers["cf-aig-max-attempts"],"1");
    assert.equal(request.headers["cf-aig-no-wholesale"],"true");
    assert.equal(request.headers["cf-aig-skip-cache"],"true");
    assert.equal(request.headers["cf-aig-collect-log-payload"],"false");
    assert.equal(request.headers.authorization,undefined);
    assert.equal(request.headers["x-goog-api-key"],undefined);
    assert.equal((await health(mf)).quota.used,1);
    assert.equal((await health(mf)).quota.activeReservations,0);
  } finally{await mf.dispose();}
});

test("model, destinations, bodies, images and academic limits are bounded before admission",async()=>{
  const {mf,observed}=runtime();
  try {
    for(const body of ["{",{...payload,model:"gemini-other"},{...payload,url:"https://untrusted"},
      {...payload,stream:true},{...payload,max_tokens:8193},{...payload,max_completion_tokens:8192},
      {...payload,messages:[payload.messages[0],{role:"user",content:[{type:"image_url",image_url:{url:"https://untrusted/image.png"}}]}]}]) {
      assert.equal((await post(mf,body)).status,400);
    }
    assert.equal((await post(mf,"x".repeat(1048577))).status,413);
    assert.equal((await post(mf,payload,{"x-goog-api-key":"caller-override"})).status,400);
    assert.equal((await post(mf,payload,{"X-Astra-MAS-Stage":"arbitrary"})).status,400);
    assert.equal(observed.length,0);assert.equal((await health(mf)).quota.used,0);
  } finally{await mf.dispose();}
});

test("image data and forced tool options retain the existing Backend protocol",async()=>{
  const {mf,queue,observed}=runtime();queue.push({});
  try {
    const body={...payload,messages:[payload.messages[0],{role:"user",content:[{type:"text",text:"same data"},
      {type:"image_url",image_url:{url:"data:image/png;base64,c3ludGhldGlj"}}]}],
      tools:[{type:"function",function:{name:"astra_output",parameters:{type:"object"}}}],
      tool_choice:{type:"function",function:{name:"astra_output"}}};
    delete body.response_format;
    assert.equal((await post(mf,body)).status,200);
    assert.deepEqual(JSON.parse(observed[0].body),body);
  } finally{await mf.dispose();}
});

test("atomic independent MAS concurrency prevents duplicate simultaneous upstream calls",async()=>{
  const {mf,queue,observed}=runtime();queue.push({delay:150});
  try {
    const replies=await Promise.all([post(mf),post(mf),post(mf)]);
    assert.equal(replies.filter(reply=>reply.status===200).length,1);
    assert.equal(replies.filter(reply=>reply.status===429).length,2);
    assert.equal(observed.length,1);assert.equal((await health(mf)).quota.used,1);
  } finally{await mf.dispose();}
});

test("upstream failures are sanitized and consume exactly one attempt without fallback",async()=>{
  const {mf,queue,observed}=runtime();queue.push({status:429,text:JSON.stringify({private:"fixture-private-token"})});
  try {
    const response=await post(mf);assert.equal(response.status,429);
    assert.equal((await response.text()).includes("fixture-private-token"),false);
    assert.equal(observed.length,1);assert.equal((await health(mf)).quota.used,1);
  } finally{await mf.dispose();}
});

test("persistent lifetime quota survives restart and UTC rollover; old counters are retained",async()=>{
  const folder=await mkdtemp(join(tmpdir(),"astra-mas-quota-"));
  let {mf}=runtime({ASTRA_MAS_ATTEMPT_LIMIT:"3"},folder,"build-test/admission-harness.js");
  try {
    let ns=await mf.getDurableObjectNamespace("MAS_ADMISSION"),stub=ns.get(ns.idFromName("mas-global-v1"));
    await stub.fetch("https://quota/seed",{method:"POST",body:JSON.stringify({used:2,tokens:10,days:{"2000-01-01":2},leases:[]})});
    await mf.dispose();
    ({mf}=runtime({ASTRA_MAS_ATTEMPT_LIMIT:"3"},folder));
    ns=await mf.getDurableObjectNamespace("MAS_ADMISSION");stub=ns.get(ns.idFromName("mas-global-v1"));
    assert.equal((await health(mf)).quota.used,2);
    assert.equal((await stub.fetch("https://quota/reserve",{method:"POST",body:JSON.stringify({id:randomUUID(),tokens:20})})).status,200);
    const status=await health(mf);
    assert.equal(status.quota.used,3);assert.equal(status.quota.dailyUsed,1);assert.equal(status.quota.remaining,0);
    await mf.dispose();
    ({mf}=runtime({ASTRA_MAS_ATTEMPT_LIMIT:"3"},folder,"build-test/admission-harness.js"));
    ns=await mf.getDurableObjectNamespace("MAS_ADMISSION");stub=ns.get(ns.idFromName("mas-global-v1"));
    assert.equal((await(await stub.fetch("https://quota/ledger")).json()).days["2000-01-01"],2);
    assert.equal((await stub.fetch("https://quota/reserve",{method:"POST",body:JSON.stringify({id:randomUUID(),tokens:1})})).status,429);
  } finally{await mf.dispose();await rm(folder,{recursive:true,force:true});}
});

test("a timed-out request spends one attempt and retains its uncertain-capacity lease",async()=>{
  const {mf,queue,observed}=runtime({ASTRA_MAS_UPSTREAM_MS:"100"});queue.push({delay:300});
  try {
    assert.equal((await post(mf)).status,504);
    const status=await health(mf);
    assert.equal(status.quota.used,1);assert.equal(status.quota.activeReservations,1);
    assert.equal((await post(mf)).status,429);assert.equal(observed.length,1);
  } finally{await mf.dispose();}
});

test("expired windows and exhausted token budgets never reach the provider",async()=>{
  for(const overrides of [{ASTRA_MAS_UNTIL:"2000-01-01T00:00:00Z"},{ASTRA_MAS_TOKEN_BUDGET:"0"}]) {
    const {mf,observed}=runtime(overrides);
    try{assert.equal((await post(mf)).status,429);assert.equal(observed.length,0);assert.equal((await health(mf)).quota.used,0);}
    finally{await mf.dispose();}
  }
});

test("development mode disables only budgets, preserves counters, and production can re-enable them",async()=>{
  const folder=await mkdtemp(join(tmpdir(),"astra-mas-development-"));
  const development={ASTRA_MAS_BUDGETS_ENABLED:"false",ASTRA_MAS_ATTEMPT_LIMIT:"0",ASTRA_MAS_DAILY:"0",
    ASTRA_MAS_TOKEN_BUDGET:"0",ASTRA_MAS_UNTIL:"2000-01-01T00:00:00Z"};
  let {mf}=runtime(development,folder);
  try {
    let ns=await mf.getDurableObjectNamespace("MAS_ADMISSION"),stub=ns.get(ns.idFromName("mas-global-v1"));
    for(let index=0;index<45;index++) {
      const id=randomUUID();
      assert.equal((await stub.fetch("https://quota/reserve",{method:"POST",body:JSON.stringify({id,tokens:50})})).status,200);
      await stub.fetch("https://quota/release",{method:"POST",body:JSON.stringify({id})});
    }
    const quota=(await health(mf)).quota;
    assert.equal(quota.budgetsEnabled,false);assert.equal(quota.used,45);
    assert.equal(quota.estimatedTokensReserved,2250);
    for(const key of ["limit","remaining","estimatedTokenLimit","expiresAt"]) assert.equal(quota[key],null);
    await mf.dispose();
    ({mf}=runtime({ASTRA_MAS_BUDGETS_ENABLED:"true",ASTRA_MAS_ATTEMPT_LIMIT:"45",ASTRA_MAS_DAILY:"512"},folder));
    assert.equal((await health(mf)).quota.used,45);
    assert.equal((await post(mf)).status,429);
    await mf.dispose();
    ({mf}=runtime({...development,ASTRA_MAS_FORWARDING_ENABLED:"false"},folder));
    assert.equal((await post(mf)).status,503);
    assert.equal((await health(mf)).quota.used,45);
  } finally{await mf.dispose();await rm(folder,{recursive:true,force:true});}
});

test("development forwarding still requires authorization and enforces technical concurrency",async()=>{
  const {mf,queue,observed}=runtime({ASTRA_MAS_BUDGETS_ENABLED:"false"});queue.push({delay:150});
  try {
    assert.equal((await post(mf,payload,{Authorization:"Bearer wrong"})).status,401);
    const responses=await Promise.all([post(mf),post(mf)]);
    assert.equal(responses.filter(item=>item.status===200).length,1);
    assert.equal(responses.filter(item=>item.status===429).length,1);
    assert.equal(observed.length,1);
    assert.equal((await post(mf,{...payload,max_tokens:8193})).status,400);
  } finally{await mf.dispose();}
});

test("an invalid budget switch fails closed",async()=>{
  const {mf,observed}=runtime({ASTRA_MAS_BUDGETS_ENABLED:"typo"});
  try {assert.equal((await post(mf)).status,503);assert.equal(observed.length,0);}
  finally{await mf.dispose();}
});

test("incomplete provider envelopes fail closed and oversized responses remain bounded",async()=>{
  for(const text of ["{}","x".repeat(2097153)]) {
    const {mf,queue}=runtime();queue.push({text});
    try{assert.ok((await post(mf)).status>=400);assert.equal((await health(mf)).quota.used,1);}
    finally{await mf.dispose();}
  }
});
