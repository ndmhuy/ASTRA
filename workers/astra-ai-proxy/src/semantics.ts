import Ajv from "ajv";
import resources from "./semantic.generated.json";

const ajv = new Ajv({ strict: false, validateFormats: false });
const canonical = ajv.compile(resources.canonicalSchema);
const native = ajv.compile(resources.providerSchema);

export class SemanticContractFailure extends Error {
  constructor(public diagnostics: Record<string, unknown>) { super("canonical_semantic_mismatch"); }
}

export function normalizeSemantic(value: unknown) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new SemanticContractFailure({ schemaStage: "canonical_normalization", invariant: "object_required" });
  }
  const frame: any = { schemaVersion: resources.catalog.schemaVersion, goals: [], constraints: [], ...value };
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
  for (const [stage, validator, input] of [["provider_schema", native, proposal], ["canonical_validation", canonical, frame]] as const) {
    if (!validator(input)) throw new SemanticContractFailure({ schemaStage: stage,
      contractVersion: resources.catalog.schemaVersion,
      validationKeywords: [...new Set(validator.errors?.map(error => error.keyword))],
      validationPaths: [...new Set(validator.errors?.map(error => error.instancePath))]
        .filter(path => /^\/(?:goals|dialogueAct|constraints|title|schemaVersion)(?:\/[A-Za-z0-9_]+)*$/.test(path)).slice(0, 8),
    });
  }
  return frame;
}
