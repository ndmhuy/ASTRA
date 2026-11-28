import { policy, type Env } from "./admission";
import limits from "./limits.json";
export { MasAdmission } from "./admission";

class Failure extends Error {
  constructor(public code: string, public status: number, public retryAfter?: string) { super(code); }
}
const reply = (body: unknown, status = 200, requestId?: string, retryAfter?: string) => Response.json(body, {
  status, headers: {"Cache-Control":"no-store", ...(requestId ? {"X-Astra-MAS-Request-ID":requestId} : {}),
    ...(retryAfter ? {"Retry-After":retryAfter} : {})},
});
function retrySeconds(value: string | null): string | undefined {
  if (!value) return;
  const seconds = /^\d+(?:\.\d+)?$/.test(value) ? Number(value) : (Date.parse(value)-Date.now())/1000;
  return Number.isFinite(seconds) ? String(Math.max(0,seconds)) : undefined;
}
function dailyQuota(value: unknown): boolean {
  const pending: unknown[] = [value];
  for (let visited=0;pending.length && visited<1000;visited++) {
    const item = pending.pop();
    if (!item || typeof item !== "object") continue;
    for (const [key,child] of Object.entries(item)) {
      if (key === "code" && ["insufficient_quota","billing_hard_limit_reached"].includes(String(child))) return true;
      if (["quotaId","quota_id","quotaMetric","quota_metric","quotaLimit","quota_limit"].includes(key) &&
        /perday|daily/.test(String(child).toLowerCase().replace(/[^a-z0-9]/g,""))) return true;
      if (child && typeof child === "object") pending.push(child);
    }
  }
  return false;
}
function upstreamFailure(status: number, text: string, retry: string | null): Failure {
  const named: Record<number,string> = {400:"upstream_invalid_request",401:"upstream_auth",403:"upstream_access",404:"upstream_model"};
  let error: any; try { error = JSON.parse(text)?.error; } catch { /* Never expose provider prose. */ }
  const wait = retrySeconds(retry);
  const code = status === 429 ? dailyQuota(error) ? "upstream_quota_exhausted"
    : wait !== undefined || error?.code === "rate_limit_exceeded" ? "upstream_rate_limited" : "upstream_quota_unknown"
    : named[status] ?? "upstream_http_"+status;
  return new Failure(code,status >= 400 && status <= 599 ? status : 502,wait);
}
async function readBounded(input: Request | Response, maximum: number) {
  const reader = input.body?.getReader();
  if (!reader) throw new Failure("invalid_body",400);
  const chunks: Uint8Array[] = []; let size = 0;
  try {
    for (;;) {
      const {done,value} = await reader.read(); if (done) break;
      size += value.length;
      if (size > maximum) throw new Failure("body_too_large",413);
      chunks.push(value);
    }
  } finally { await reader.cancel(); }
  const joined = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { joined.set(chunk,offset); offset += chunk.length; }
  return new TextDecoder("utf-8",{fatal:true,ignoreBOM:false}).decode(joined);
}
async function authorized(request: Request, secret?: string) {
  if (!secret || !/^[a-f0-9]{64}$/.test(secret)) return false;
  const expected = new TextEncoder().encode("Bearer " + secret);
  const actual = new TextEncoder().encode(request.headers.get("Authorization") ?? "");
  const digests = await Promise.all([expected,actual].map(value => crypto.subtle.digest("SHA-256",value)));
  const [a,b] = digests.map(value => new Uint8Array(value)); let difference = 0;
  for (let i=0;i<a.length;i++) difference |= a[i] ^ b[i];
  return difference === 0;
}
function gateway(env: Env) {
  if (!/^[a-fA-F0-9]{32}$/.test(env.ASTRA_MAS_GATEWAY_ACCOUNT_ID ?? "") || env.ASTRA_MAS_GATEWAY_ID !== "astra-mas-gateway" ||
    !/^[A-Za-z0-9._~-]{1,300}$/.test(env.ASTRA_MAS_GATEWAY_TOKEN ?? "") ||
    !/^[A-Za-z0-9_-]{1,64}$/.test(env.ASTRA_MAS_GATEWAY_BYOK_ALIAS ?? "default") ||
    !/^gemini-[A-Za-z0-9._-]{1,90}$/.test(env.ASTRA_MAS_MODEL ?? "")) throw new Failure("configuration",503);
  return "https://gateway.ai.cloudflare.com/v1/" + env.ASTRA_MAS_GATEWAY_ACCOUNT_ID + "/astra-mas-gateway/google-ai-studio/v1beta/openai/chat/completions";
}
function validate(body: any, model: string, maxTokens: number) {
  const allowed = ["model","messages","max_tokens","max_completion_tokens","response_format","temperature","seed","tools","tool_choice"];
  if (!body || typeof body !== "object" || Array.isArray(body) || Object.keys(body).some(key => !allowed.includes(key)) ||
    body.model !== model || !Array.isArray(body.messages) || body.messages.length !== 2 ||
    body.messages[0]?.role !== "system" || body.messages[1]?.role !== "user") throw new Failure("invalid_request",400);
  const tokens = body.max_tokens ?? body.max_completion_tokens;
  if (body.max_tokens !== undefined && body.max_completion_tokens !== undefined ||
    !Number.isSafeInteger(tokens) || tokens < 1 || tokens > maxTokens) throw new Failure("output_limit",400);
  for (const message of body.messages) {
    if (Object.keys(message).some(key => !["role","content"].includes(key))) throw new Failure("invalid_messages",400);
    if (typeof message.content === "string" && message.content.trim()) continue;
    if (message.role !== "user" || !Array.isArray(message.content) || !message.content.length) throw new Failure("invalid_messages",400);
    for (const part of message.content) {
      if (part?.type === "text" && typeof part.text === "string" && Object.keys(part).every(key => ["type","text"].includes(key))) continue;
      if (part?.type === "image_url" && Object.keys(part).every(key => ["type","image_url"].includes(key)) &&
        part.image_url && Object.keys(part.image_url).every(key => key === "url") &&
        /^data:image\/(?:png|jpeg|webp);base64,[A-Za-z0-9+/]+=*$/.test(part.image_url.url)) continue;
      throw new Failure("invalid_content",400);
    }
  }
  return tokens as number;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const path = new URL(request.url).pathname;
    if (request.method === "GET" && path === "/health") {
      try {
        const rules = policy(env);
        const quota = await env.MAS_ADMISSION.get(env.MAS_ADMISSION.idFromName("mas-global-v1")).fetch("https://quota/status");
        if (!quota.ok) throw new Error("storage");
        let configured = true; try { gateway(env); } catch { configured = false; }
        return reply({status:"ok",protocol:"openai-chat-completions",policy:limits.schemaVersion,
          forwarding:env.ASTRA_MAS_FORWARDING_ENABLED === "true", configured,
          callerAuthorization: /^[a-f0-9]{64}$/.test(env.ASTRA_MAS_CALLER_TOKEN ?? ""),
          model:/^gemini-[A-Za-z0-9._-]{1,90}$/.test(env.ASTRA_MAS_MODEL ?? "") ? env.ASTRA_MAS_MODEL : null,
          limits:{maxRequestBytes:limits.maxRequestBytes,maxResponseBytes:limits.maxResponseBytes,
            outputTokens:rules.outputTokens,upstreamMs:rules.upstreamMs,concurrency:rules.concurrency},quota:await quota.json()});
      } catch { return reply({status:"unavailable",forwarding:false},503); }
    }
    if (path !== "/v1/chat/completions") return reply({error:{code:"not_found"}},404);
    if (request.method !== "POST") return reply({error:{code:"method_not_allowed"}},405);
    const id = crypto.randomUUID(), started = performance.now();
    let stub: DurableObjectStub | undefined, admitted = false, attempted = false, settled = false;
    let timer: ReturnType<typeof setTimeout> | undefined, upstreamStatus: number | undefined;
    let role: string | null = null, providerStarted: number | undefined;
    let usage: Record<string, number> | undefined;
    let stage = "authorization";
    const controller = new AbortController();
    const disconnect = () => controller.abort();
    try {
      if (request.headers.has("Origin") || !await authorized(request,env.ASTRA_MAS_CALLER_TOKEN)) throw new Failure("caller_unauthorized",401);
      if (env.ASTRA_MAS_FORWARDING_ENABLED !== "true") throw new Failure("mas_forwarding_disabled",503);
      const rules = policy(env), url = gateway(env);
      if (request.headers.get("content-type")?.split(";")[0].trim() !== "application/json" ||
        ["cf-aig-authorization","x-goog-api-key","cf-aig-byok-alias"].some(name => request.headers.has(name))) throw new Failure("invalid_headers",400);
      const requestedRole = request.headers.get("X-Astra-MAS-Stage");
      if (!["composer","illustrator","solver","reviewer"].includes(requestedRole ?? "")) throw new Failure("invalid_stage",400);
      role = requestedRole;
      const operation = request.headers.get("X-Astra-MAS-Operation");
      const attempt = request.headers.get("X-Astra-MAS-Attempt");
      if (operation && !/^[a-f0-9]{64}$/.test(operation) || attempt && !/^[a-f0-9-]{36}$/.test(attempt)) throw new Failure("invalid_operation",400);
      if (operation) console.log(JSON.stringify({requestId:id,operationId:operation,attemptId:attempt,role}));
      stage = "request_validation";
      const raw = await readBounded(request,limits.maxRequestBytes), body = JSON.parse(raw);
      const tokens = validate(body,env.ASTRA_MAS_MODEL!,rules.outputTokens);
      stub = env.MAS_ADMISSION.get(env.MAS_ADMISSION.idFromName("mas-global-v1"));
      stage = "admission";
      const reservation = await stub.fetch("https://quota/reserve", {method:"POST",body:JSON.stringify({id,tokens:new TextEncoder().encode(raw).length+tokens})});
      if (!reservation.ok) {
        const rejection = await reservation.json() as {error?:string};
        const code = ["mas_capacity","mas_budget_exhausted","mas_forwarding_disabled"].includes(rejection.error ?? "")
          ? rejection.error! : "mas_budget_or_capacity";
        throw new Failure(code,reservation.status === 429 ? 429 : 503,retrySeconds(reservation.headers.get("Retry-After")));
      }
      admitted = true;
      if (request.signal.aborted) throw new Failure("caller_cancelled",499);
      request.signal.addEventListener("abort",disconnect,{once:true});
      timer = setTimeout(() => controller.abort(),rules.upstreamMs);
      stage = "provider_request"; attempted = true;
      providerStarted = performance.now();
      const upstream = await fetch(url,{method:"POST",redirect:"manual",signal:controller.signal,body:raw,headers:{
        "Content-Type":"application/json", "cf-aig-authorization":"Bearer " + env.ASTRA_MAS_GATEWAY_TOKEN,
        "cf-aig-byok-alias":env.ASTRA_MAS_GATEWAY_BYOK_ALIAS ?? "default", "cf-aig-no-wholesale":"true",
        "cf-aig-max-attempts":"1","cf-aig-request-timeout":String(rules.upstreamMs),
        "cf-aig-skip-cache":"true","cf-aig-collect-log":"false","cf-aig-collect-log-payload":"false",
      }});
      upstreamStatus = upstream.status; stage = "provider_response";
      const text = await readBounded(upstream,limits.maxResponseBytes); settled = true;
      if (!upstream.ok) throw upstreamFailure(upstream.status,text,upstream.headers.get("Retry-After"));
      if (!upstream.headers.get("content-type")?.includes("application/json")) throw new Failure("provider_protocol",502);
      const envelope = JSON.parse(text);
      if (!Array.isArray(envelope.choices) || envelope.choices.length !== 1 || !envelope.choices[0]?.message) throw new Failure("provider_protocol",502);
      usage = Object.fromEntries(["prompt_tokens","completion_tokens","total_tokens"].flatMap(key => {
        const value = envelope.usage?.[key];
        return Number.isSafeInteger(value) && value >= 0 && value < limits.maxEstimatedTokens ? [[key,value]] : [];
      }));
      // Preserve the provider envelope. Existing Backend parser/academic validation is authoritative.
      return new Response(text,{status:200,headers:{"Content-Type":"application/json","Cache-Control":"no-store","X-Astra-MAS-Request-ID":id}});
    } catch (error) {
      const failure = error instanceof Failure ? error : error instanceof Error && error.name === "AbortError" ? new Failure("upstream_timeout",504) :
        error instanceof SyntaxError ? new Failure(attempted ? "provider_protocol" : "invalid_json",attempted ? 502 : 400) : new Failure("mas_transport_error",503);
      return reply({error:{type:"astra_mas_error",code:failure.code,message:"MAS inference unavailable; no result was substituted."}},failure.status,id,failure.retryAfter);
    } finally {
      if (timer !== undefined) clearTimeout(timer);
      request.signal.removeEventListener("abort",disconnect);
      console.log(JSON.stringify({requestId:id,role,stage,admitted,attempts:attempted ? 1 : 0,upstreamStatus,
        elapsedMs:Math.round(performance.now()-started),providerElapsedMs:providerStarted === undefined ? undefined : Math.round(performance.now()-providerStarted),usage}));
      // Uncertain timed-out/cancelled calls keep their lease until natural expiry.
      if (admitted && (!attempted || settled)) await stub!.fetch("https://quota/release",{method:"POST",body:JSON.stringify({id})});
    }
  },
};
