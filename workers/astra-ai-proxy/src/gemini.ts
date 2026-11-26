import Ajv, { type ValidateFunction } from "ajv";
import resources from "./generated.json";

const ajv = new Ajv({ strict: false, validateFormats: false });
const providerValidator = ajv.compile(resources.providerSchema);
const outputValidator = ajv.compile(resources.outputSchema);
const decisionValidator = ajv.compile(resources.decisionSchema);

type Diagnostics = Record<string, unknown>;
export class GeminiOutputFailure extends Error {
  constructor(public diagnostics: Diagnostics) { super("schema"); }
}

function safeCode(value: unknown): string {
  return typeof value === "string" && /^[A-Z_]{1,50}$/.test(value) ? value : "missing";
}

function validate(validator: ValidateFunction, value: unknown, diagnostics: Diagnostics): void {
  if (validator(value)) return;
  const errors = validator.errors ?? [];
  throw new GeminiOutputFailure({
    ...diagnostics,
    validationKeywords: [...new Set(errors.map(error => error.keyword))],
    validationPaths: [...new Set(errors.map(error => error.instancePath))]
      .filter(path => /^\/(?:intents|intake|guidance|title|kind)(?:\/[A-Za-z0-9_]+)*$/.test(path))
      .slice(0, 8),
  });
}

export function parseGemini(raw: string, mimeType: string | null) {
  const diagnostics: Diagnostics = {
    schemaStage: "upstream_json", envelopeParsing: "invalid", jsonParsing: "not_started",
    responseMimeType: mimeType?.split(";")[0] === "application/json" ? "application/json" : "other",
    responseBytes: new TextEncoder().encode(raw).length,
  };
  try {
    const payload = JSON.parse(raw);
    diagnostics.envelopeParsing = "valid";
    diagnostics.schemaStage = "response_envelope";
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new GeminiOutputFailure(diagnostics);
    }
    const candidates = payload.candidates;
    diagnostics.candidateCount = Array.isArray(candidates) ? candidates.length : 0;
    diagnostics.promptBlockReason = safeCode(payload.promptFeedback?.blockReason);
    diagnostics.finishReason = safeCode(candidates?.[0]?.finishReason);
    for (const name of ["promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount", "totalTokenCount"]) {
      const value = payload.usageMetadata?.[name];
      diagnostics[name] = Number.isSafeInteger(value) && value >= 0 ? value : null;
    }
    diagnostics.schemaStage = "candidate_selection";
    if (!Array.isArray(candidates) || candidates.length !== 1 || !candidates[0]) {
      throw new GeminiOutputFailure(diagnostics);
    }
    diagnostics.schemaStage = "candidate_completion";
    if (candidates[0].finishReason !== "STOP") throw new GeminiOutputFailure(diagnostics);
    diagnostics.schemaStage = "text_extraction";
    const parts = candidates[0].content?.parts;
    if (!Array.isArray(parts) || !parts.length) throw new GeminiOutputFailure(diagnostics);
    diagnostics.partCount = parts.length;
    const textParts = parts.filter(part => part && !part.thought && typeof part.text === "string");
    const text = textParts.map(part => part.text).join("");
    diagnostics.finalTextParts = textParts.length;
    diagnostics.textBytes = new TextEncoder().encode(text).length;
    if (!text.trim()) throw new GeminiOutputFailure(diagnostics);
    diagnostics.schemaStage = "semantic_json";
    diagnostics.jsonParsing = "invalid";
    const proposal = JSON.parse(text);
    diagnostics.jsonParsing = "valid";
    const decision = { intents: [], ...proposal };
    // Null optional prose/proposal fields have the same meaning as omission.
    for (const name of ["guidance", "title", "intake"]) {
      if (decision[name] === null) delete decision[name];
    }
    diagnostics.schemaStage = "provider_schema";
    validate(providerValidator, decision, diagnostics);
    diagnostics.schemaStage = "application_contract";
    diagnostics.kind = decision.kind;
    diagnostics.intents = decision.intents.map((intent: { id: string }) => intent.id);
    diagnostics.hasIntake = Boolean(decision.intake);
    diagnostics.hasGuidance = Boolean(decision.guidance);
    validate(decisionValidator, decision, diagnostics);
    validate(outputValidator, decision, diagnostics);
    const invariant = (decision.kind === "task") !== Boolean(decision.intents.length)
      ? "task_action_mismatch" : decision.intake && decision.guidance ? "intake_guidance_conflict"
      : (decision.intake || decision.guidance) && !["answer", "clarify"].includes(decision.kind)
        ? "executable_kind_with_proposal" : null;
    if (invariant) throw new GeminiOutputFailure({ ...diagnostics, validationKeywords: [invariant] });
    diagnostics.schemaStage = "validated";
    diagnostics.kind = decision.kind;
    diagnostics.intents = decision.intents.map((intent: { id: string }) => intent.id);
    diagnostics.family = decision.intake?.family;
    return { decision, diagnostics };
  } catch (error) {
    if (error instanceof GeminiOutputFailure) throw error;
    throw new GeminiOutputFailure(diagnostics);
  }
}
