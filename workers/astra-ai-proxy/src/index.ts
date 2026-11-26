import Ajv from "ajv";
import resources from "./generated.json";
import { bounded, type Env } from "./env";
export { Admission } from "./admission";

const ajv = new Ajv({ strict: false, validateFormats: false });
const validateTurn = ajv.compile(resources.turnSchema);
const validateDecision: (data: unknown) => boolean = ajv.compile(resources.decisionSchema);
const validateOutput: (data: unknown) => boolean = ajv.compile(resources.outputSchema);
const MAX_BODY = 32768;
const MAX_RESPONSE = 65536;
const VERSION = "astra-intent-v1";

class Failure extends Error {
  constructor(public category: string, public status: number) { super(category); }
}

async function readBounded(response: Request | Response, limit: number): Promise<string> {
  const reader = response.body?.getReader();
  if (!reader) throw new Failure("rejected", 400);
  let size = 0;
  const chunks: Uint8Array[] = [];
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > limit) throw new Failure("rejected", 413);
      chunks.push(value);
    }
  } finally { await reader.cancel(); }
  const joined = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { joined.set(chunk, offset); offset += chunk.length; }
  return new TextDecoder("utf-8", { fatal: true, ignoreBOM: false }).decode(joined);
}

function response(body: unknown, status = 200) {
  return Response.json(body, { status, headers: { "Cache-Control": "no-store" } });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const path = new URL(request.url).pathname;
    if (path === "/health" && request.method === "GET") {
      return response({ status: "ok", contract: VERSION, forwarding: env.ASTRA_FORWARDING_ENABLED === "true" });
    }
    if (path !== "/v1/agent/interpret") return response({ error: "rejected" }, 404);
    if (request.method !== "POST") return response({ error: "rejected" }, 405);
    const id = crypto.randomUUID();
    const started = performance.now();
    let admission: DurableObjectStub | undefined;
    let reserved = false;
    let upstreamStatus: number | undefined;
    let attempts = 0;
    let category = "valid";
    let controller: AbortController | undefined;
    const disconnect = () => controller?.abort();
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      if (env.ASTRA_FORWARDING_ENABLED !== "true") throw new Failure("disabled", 503);
      if (request.headers.get("X-Astra-Contract") !== resources.contractHash) {
        throw new Failure("configuration", 409);
      }
      const account = env.ASTRA_AGENT_GATEWAY_ACCOUNT_ID ?? "";
      const gateway = env.ASTRA_AGENT_GATEWAY_ID ?? "";
      const alias = env.ASTRA_AGENT_GATEWAY_BYOK_ALIAS ?? "default";
      const model = env.ASTRA_AGENT_MODEL ?? "";
      const token = env.ASTRA_AGENT_GATEWAY_TOKEN ?? "";
      if (!/^[a-fA-F0-9]{32}$/.test(account) || gateway !== "astra-gateway" ||
          !/^[A-Za-z0-9_-]{1,64}$/.test(alias) || !/^[A-Za-z0-9._~-]{1,300}$/.test(token) ||
          !/^gemini-[A-Za-z0-9._-]{1,90}$/.test(model)) throw new Failure("configuration", 503);
      const milliseconds = bounded(env.ASTRA_UPSTREAM_MS, 30000);
      const tokens = bounded(env.ASTRA_OUTPUT_TOKENS, 1024);
      if (milliseconds < 100 || tokens < 128) throw new Failure("configuration", 503);
      if (request.headers.get("content-type")?.split(";")[0].trim() !== "application/json") {
        throw new Failure("rejected", 415);
      }
      if (["authorization", "cf-aig-authorization", "x-goog-api-key"].some(key => request.headers.has(key))) {
        throw new Failure("rejected", 400);
      }
      const turn: any = JSON.parse(await readBounded(request, MAX_BODY));
      if (!validateTurn(turn)) throw new Failure("rejected", 400);
      // Connection metadata is set by Cloudflare at the edge. Claimed IDs never grant quota.
      const ip = request.headers.get("CF-Connecting-IP");
      if (!ip) throw new Failure("configuration", 503);
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ip));
      const ipHash = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
      admission = env.ADMISSION.get(env.ADMISSION.idFromName("global-v1"));
      const admitted = await admission.fetch("https://admission/reserve", {
        method: "POST", body: JSON.stringify({ ip: ipHash, id, operation: "agent" }),
      });
      if (admitted.status === 429) throw new Failure("quota", 429);
      if (!admitted.ok) throw new Failure("transient", 503);
      reserved = true;
      controller = new AbortController();
      request.signal.addEventListener("abort", disconnect, { once: true });
      timer = setTimeout(() => controller?.abort(), milliseconds);
      const context = turn.context as Record<string, any>;
      const preview = ["failed", "unavailable"].includes(context.preview) ? context.preview : null;
      const hintKey = JSON.stringify([context.setup, context.status ?? null, context.approved ?? false, preview]);
      const hints = (resources.hints as Record<string, string[]>)[hintKey] ?? [];
      const upstreamUrl = "https://gateway.ai.cloudflare.com/v1/" + account + "/" + gateway +
        "/google-ai-studio/v1/models/" + model + ":generateContent";
      attempts = 1;
      const upstream = await fetch(upstreamUrl, {
        method: "POST", redirect: "manual", signal: controller.signal,
        headers: {
          "Content-Type": "application/json", "cf-aig-authorization": "Bearer " + token,
          "cf-aig-byok-alias": alias, "cf-aig-no-wholesale": "true",
          "cf-aig-max-attempts": "1", "cf-aig-request-timeout": String(milliseconds),
          "cf-aig-skip-cache": "true", "cf-aig-collect-log": "false",
          "cf-aig-collect-log-payload": "false",
        },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: resources.system }] },
          contents: [{ role: "user", parts: [{ text: JSON.stringify({
            ...resources.base, availableHints: hints, context, message: turn.message,
          }) }] }],
          generationConfig: {
            responseMimeType: "application/json", responseJsonSchema: resources.outputSchema,
            maxOutputTokens: tokens,
          },
        }),
      });
      upstreamStatus = upstream.status;
      if (!upstream.ok) {
        await upstream.body?.cancel();
        const category = upstream.status === 429 ? "quota" : [401,403].includes(upstream.status) ? "auth" :
          upstream.status === 404 ? "model" : [408,504].includes(upstream.status) ? "timeout" :
          upstream.status >= 500 ? "transient" : "rejected";
        throw new Failure(category, 502);
      }
      const payload = JSON.parse(await readBounded(upstream, MAX_RESPONSE));
      const candidates = payload.candidates;
      if (!Array.isArray(candidates) || candidates.length !== 1 || candidates[0].finishReason !== "STOP") {
        throw new Failure("schema", 502);
      }
      const parts = candidates[0].content?.parts;
      if (!Array.isArray(parts)) throw new Failure("schema", 502);
      const text = parts.filter(part => !part.thought).map(part => part.text).join("");
      const decision: any = JSON.parse(text);
      const semanticValid = validateDecision(decision) && validateOutput(decision);
      if (!semanticValid ||
          (decision.kind === "task") !== Boolean(decision.intents.length) ||
          (decision.intake && decision.guidance) ||
          ((decision.intake || decision.guidance) && !["answer","clarify"].includes(decision.kind))) {
        throw new Failure("schema", 502);
      }
      return response({ schemaVersion: VERSION, clientMessageId: turn.clientMessageId, decision,
        evidence: { requestId: id, admitted: true, attempts, provider: "google-ai-studio",
          model, upstreamStatus, elapsedMs: Math.round(performance.now() - started) } });
    } catch (error) {
      const failure = error instanceof Failure ? error :
        error instanceof Error && error.name === "AbortError" ? new Failure("timeout", 504) :
        error instanceof SyntaxError ? new Failure(reserved ? "schema" : "rejected", reserved ? 502 : 400) :
        new Failure("transient", 503);
      category = failure.category;
      return response({ error: failure.category, requestId: id }, failure.status);
    } finally {
      if (timer !== undefined) clearTimeout(timer);
      request.signal.removeEventListener("abort", disconnect);
      console.log(JSON.stringify({ requestId: id, admitted: reserved, attempts, upstreamStatus,
        provider: attempts ? "google-ai-studio" : undefined,
        model: attempts ? env.ASTRA_AGENT_MODEL : undefined,
        category, elapsedMs: Math.round(performance.now() - started) }));
      if (reserved && admission) {
        try { await admission.fetch("https://admission/release", { method: "POST", body: JSON.stringify({ release: id }) }); }
        catch { /* Lease expires without refunding the daily attempt. */ }
      }
    }
  },
};
