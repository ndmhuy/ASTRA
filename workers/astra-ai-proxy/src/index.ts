import Ajv from "ajv";
import resources from "./generated.json";
import semanticResources from "./semantic.generated.json";
import { bounded, type Env } from "./env";
import { parseGemini, GeminiOutputFailure } from "./gemini";
export { Admission } from "./admission";

const ajv = new Ajv({ strict: false, validateFormats: false });
const validateTurn = ajv.compile(resources.turnSchema);
const validateSemanticTurn = ajv.compile(semanticResources.turnSchema);
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
      try {
        const admission = env.ADMISSION.get(env.ADMISSION.idFromName("global-v1"));
        const status = await admission.fetch("https://admission/status");
        if (!status.ok) throw new Error("quota storage unavailable");
        return response({ status: "ok", contract: VERSION,
          forwarding: env.ASTRA_FORWARDING_ENABLED === "true", quota: await status.json() });
      } catch {
        return response({ status: "unavailable", forwarding: false }, 503);
      }
    }
    const semantic = path === "/v2/agent/interpret";
    if (path !== "/v1/agent/interpret" && !semantic) return response({ error: "rejected" }, 404);
    if (request.method !== "POST") return response({ error: "rejected" }, 405);
    const id = crypto.randomUUID();
    const started = performance.now();
    let admission: DurableObjectStub | undefined;
    let reserved = false;
    let upstreamStatus: number | undefined;
    let providerStarted: number | undefined;
    let attempts = 0;
    let category = "valid";
    let outputMetadata: Record<string, unknown> = {};
    let controller: AbortController | undefined;
    const disconnect = () => controller?.abort();
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      if (env.ASTRA_FORWARDING_ENABLED !== "true" || env.ASTRA_AGENT_FORWARDING_ENABLED === "false") throw new Failure("disabled", 503);
      if (request.headers.get("X-Astra-Contract") !== (semantic ? semanticResources.contractHash : resources.contractHash)) {
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
      if (!(semantic ? validateSemanticTurn(turn) : validateTurn(turn))) throw new Failure("rejected", 400);
      const message = turn.message.trim();
      if (!message || !/[\p{Letter}\p{Number}]/u.test(message) || /^(.)\1{11,}$/su.test(message) ||
          /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(message)) throw new Failure("rejected", 400);
      // Connection metadata is set by Cloudflare at the edge. Claimed IDs never grant quota.
      const ip = request.headers.get("CF-Connecting-IP");
      if (!ip) throw new Failure("configuration", 503);
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ip));
      const ipHash = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
      const context = turn.context as Record<string, any>;
      const preview = ["failed", "unavailable"].includes(context.preview) ? context.preview : null;
      const hintKey = JSON.stringify([context.setup, context.status ?? null, context.approved ?? false, preview]);
      const hints = (resources.hints as Record<string, string[]>)[hintKey] ?? [];
      const providerBody = JSON.stringify({
        systemInstruction: { parts: [{ text: semantic ? semanticResources.system : resources.system }] },
        contents: [{ role: "user", parts: [{ text: JSON.stringify({
          ...(semantic ? { goals: Object.fromEntries(Object.entries(semanticResources.catalog.goals).map(([name, item]) =>
            [name, { meaning: item.meaning, parameters: item.parameters }])) }
            : { ...resources.base, availableHints: hints }), context, message: turn.message,
        }) }] }],
        generationConfig: {
          responseMimeType: "application/json", responseJsonSchema: semantic ? semanticResources.providerSchema : resources.providerSchema,
          ...(model === "gemini-3.1-flash-lite" ? { thinkingConfig: { thinkingLevel: "MINIMAL" } } : {}), maxOutputTokens: tokens,
        },
      });
      admission = env.ADMISSION.get(env.ADMISSION.idFromName("global-v1"));
      const admitted = await admission.fetch("https://admission/reserve", {
        method: "POST", body: JSON.stringify({ ip: ipHash, id, operation: "agent",
          reservedTokens: new TextEncoder().encode(providerBody).length + tokens,
          ...(semantic ? { turnId: turn.workspaceId + ":" + turn.clientMessageId } : {}) }),
      });
      if (admitted.status === 429) throw new Failure("quota", 429);
      if (admitted.status === 409) throw new Failure("rejected", 409);
      if (!admitted.ok) throw new Failure("transient", 503);
      reserved = true;
      if (request.signal.aborted) throw new Failure("rejected", 499);
      controller = new AbortController();
      request.signal.addEventListener("abort", disconnect, { once: true });
      timer = setTimeout(() => controller?.abort(), milliseconds);
      const upstreamUrl = "https://gateway.ai.cloudflare.com/v1/" + account + "/" + gateway +
        "/google-ai-studio/v1/models/" + model + ":generateContent";
      attempts = 1;
      providerStarted = performance.now();
      const upstream = await fetch(upstreamUrl, {
        method: "POST", redirect: "manual", signal: controller.signal,
        headers: {
          "Content-Type": "application/json", "cf-aig-authorization": "Bearer " + token,
          "cf-aig-byok-alias": alias, "cf-aig-no-wholesale": "true",
          "cf-aig-max-attempts": "1", "cf-aig-request-timeout": String(milliseconds),
          "cf-aig-skip-cache": "true", "cf-aig-collect-log": "false",
          "cf-aig-collect-log-payload": "false",
        },
        body: providerBody,
      });
      upstreamStatus = upstream.status;
      if (!upstream.ok) {
        let errorCode: number | undefined;
        let errorStatus: string | undefined;
        try {
          const error = JSON.parse(await readBounded(upstream, MAX_RESPONSE)).error;
          errorCode = Number.isSafeInteger(error?.code) ? error.code : undefined;
          errorStatus = typeof error?.status === "string" && /^[A-Z_]{1,50}$/.test(error.status)
            ? error.status : undefined;
        } catch { /* HTTP classification remains authoritative for malformed error bodies. */ }
        console.log(JSON.stringify({ requestId: id, upstreamStatus, errorCode, errorStatus }));
        const category = upstream.status === 429 ? "quota" : [401,403].includes(upstream.status) ? "auth" :
          upstream.status === 404 ? "model" : [408,504].includes(upstream.status) ? "timeout" :
          upstream.status >= 500 ? "transient" : "rejected";
        throw new Failure(category, 502);
      }
      const parsed = parseGemini(await readBounded(upstream, MAX_RESPONSE), upstream.headers.get("content-type"), semantic);
      const decision = parsed.decision;
      outputMetadata = parsed.diagnostics;
      console.log(JSON.stringify({ requestId: id, ...outputMetadata }));
      return response({ schemaVersion: semantic ? semanticResources.catalog.schemaVersion : VERSION,
        clientMessageId: turn.clientMessageId, ...(semantic ? { frame: decision } : { decision }),
        evidence: { requestId: id, admitted: true, attempts, provider: "google-ai-studio",
          model, upstreamStatus, elapsedMs: Math.round(performance.now() - started) } });
    } catch (error) {
      if (error instanceof GeminiOutputFailure) outputMetadata = error.diagnostics;
      const failure = error instanceof GeminiOutputFailure ? new Failure("schema", 502) :
        error instanceof Failure ? error :
        error instanceof Error && error.name === "AbortError" ? new Failure("timeout", 504) :
        error instanceof SyntaxError ? new Failure(reserved ? "schema" : "rejected", reserved ? 502 : 400) :
        new Failure("transient", 503);
      category = failure.category;
      if (category === "schema") console.log(JSON.stringify({ requestId: id, ...outputMetadata }));
      return response({ error: failure.category, requestId: id,
        ...(semantic && Object.keys(outputMetadata).length ? { diagnostics: outputMetadata } : {}) }, failure.status);
    } finally {
      if (timer !== undefined) clearTimeout(timer);
      request.signal.removeEventListener("abort", disconnect);
      console.log(JSON.stringify({ requestId: id, admitted: reserved, attempts, upstreamStatus,
        providerElapsedMs: providerStarted === undefined ? undefined
          : Math.round(performance.now() - providerStarted),
        provider: attempts ? "google-ai-studio" : undefined,
        model: attempts ? env.ASTRA_AGENT_MODEL : undefined,
        category, elapsedMs: Math.round(performance.now() - started) }));
      if (reserved && admission) {
        try {
          await admission.fetch("https://admission/outcome", { method: "POST", body: JSON.stringify({ id, outcome: category }) });
          // An aborted request can still consume upstream capacity. Keep its bounded lease.
          if (category !== "timeout" && (!attempts || upstreamStatus !== undefined) && !request.signal.aborted) {
            await admission.fetch("https://admission/release", { method: "POST", body: JSON.stringify({ release: id }) });
          }
        }
        catch { /* Lease expires without refunding the daily attempt. */ }
      }
    }
  },
};
