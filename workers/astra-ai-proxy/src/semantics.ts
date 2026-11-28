import Ajv from "ajv";
import resources from "./semantic.generated.json";
import v3Resources from "./semantic-v3.generated.json";

const ajv = new Ajv({ strict: false, validateFormats: false });
const canonical = ajv.compile(resources.canonicalSchema);
const native = ajv.compile(resources.providerSchema);
const canonicalV3 = ajv.compile(v3Resources.canonicalSchema);
const nativeV3 = ajv.compile(v3Resources.providerSchema);

export class SemanticContractFailure extends Error {
  constructor(public diagnostics: Record<string, unknown>) { super("canonical_semantic_mismatch"); }
}

export function normalizeSemantic(value: unknown, v3 = false) {
  const contract = v3 ? v3Resources : resources;
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new SemanticContractFailure({ schemaStage: "canonical_normalization", invariant: "object_required" });
  }
  const frame: any = { schemaVersion: contract.catalog.schemaVersion, goals: [], constraints: [], ...value };
  for (const name of ["goals", "constraints"]) if (frame[name] === null) frame[name] = [];
  const title = frame.title;
  delete frame.title;
  if (typeof title === "string" && !/[\u0000-\u001f]/.test(title)) {
    const clean = title.replace(/\s+/g, " ").trim();
    if (clean && [...clean].length <= 60) frame.title = clean;
  }
  if (Array.isArray(frame.goals)) frame.goals = frame.goals.map((goal: any) => {
    if (!goal || typeof goal !== "object" || Array.isArray(goal)) return goal;
    const result = Object.fromEntries(Object.entries(goal).filter(([, value]) => value !== null));
    if (!Object.hasOwn(result, "parameters")) result.parameters = {};
    return result;
  });
  const { schemaVersion, ...proposal } = frame;
  for (const [stage, validator, input] of [["provider_schema", v3 ? nativeV3 : native, proposal], ["canonical_validation", v3 ? canonicalV3 : canonical, frame]] as const) {
    if (!validator(input)) throw new SemanticContractFailure({ schemaStage: stage,
      contractVersion: contract.catalog.schemaVersion,
      validationKeywords: [...new Set(validator.errors?.map(error => error.keyword))],
      validationPaths: [...new Set(validator.errors?.map(error => error.instancePath))]
        .filter(path => /^\/(?:goals|dialogueAct|constraints|title|schemaVersion)(?:\/[A-Za-z0-9_]+)*$/.test(path)).slice(0, 8),
    });
  }
  return frame;
}
