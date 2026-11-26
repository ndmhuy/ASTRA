// No network access or model invocation. Optional predictions must come from an authorized run.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseFrame, resolveSemantic, contextualSubject } from '../src/agent/semantics.ts';
import { resolveIntake } from '../src/agent/knowledge.ts';
import { admit, fastRoute } from '../src/agent/recipes.ts';

const root = fileURLToPath(new URL('../../', import.meta.url));
const dir = resolve(root, 'eval/agent-semantic');
const read = file => JSON.parse(readFileSync(resolve(dir, file), 'utf8'));
const corpus = readFileSync(resolve(dir, 'semantic-corpus.jsonl'), 'utf8').trim().split('\n').map(line => JSON.parse(line));
const scenarios = read('workflow-scenarios.json');
const adversarial = read('adversarial-corpus.json');
const formats = read('catalog.fixture.json');
const families = new Map();
const identifiers = new Set();
const timings = [];
let localMatches = 0, localSubjectTurns = 0, workflowTurns = 0;

for (const row of [...corpus, ...scenarios, ...adversarial]) {
  assert.equal(identifiers.has(row.id), false, `Duplicate id: ${row.id}`);
  identifiers.add(row.id);
  assert.ok(['development', 'evaluation'].includes(row.partition));
  const previous = families.get(row.scenarioFamily);
  assert.ok(!previous || previous === row.partition, `Partition leakage: ${row.scenarioFamily}`);
  families.set(row.scenarioFamily, row.partition);
}
for (const row of corpus) {
  const start = performance.now();
  const frame = parseFrame(row.expectedFrame);
  for (const goal of frame.goals) assert.equal(row.prohibitedGoals.includes(goal.goal), false, row.id);
  resolveSemantic(frame); // Measures resolution of labeled meaning, never language understanding.
  timings.push(performance.now() - start);
  if (fastRoute(row.input)) localMatches++;
}

for (const scenario of scenarios) {
  let intake = scenario.initialState.intake;
  for (const [index, turn] of scenario.turns.entries()) {
    workflowTurns++;
    const frame = parseFrame(turn.expectedFrame);
    const workflow = resolveSemantic(frame);
    const local = contextualSubject(turn.input, intake, formats);
    if (turn.expected.localSubject) {
      assert.ok(local?.intake, `${scenario.id}: pending subject must resolve locally`);
      localSubjectTurns++;
    }
    let capabilities = workflow.decision?.intents.map(intent => intent.id) ?? [];
    let text = workflow.text ?? '';
    if (workflow.cancel) intake = undefined;
    if (workflow.decision?.intake) {
      const result = resolveIntake(local?.intake ?? workflow.decision.intake, turn.input, intake, formats, `source-${index}`, true);
      if (result.draft) intake = result.draft;
      if ('text' in result) text = result.text;
      else capabilities = [workflow.requestGeneration ? 'PREPARE_GENERATION' : workflow.setupOnly ? 'SELECT_FORMAT' : result.intent.id];
    }
    const expected = turn.expected;
    assert.deepEqual(capabilities, expected.capabilities, scenario.id);
    if (expected.missing) assert.equal(intake?.missing, expected.missing, scenario.id);
    if (expected.family) assert.equal(intake?.family, expected.family, scenario.id);
    if (expected.subject) assert.equal(intake?.subject, expected.subject, scenario.id);
    if (expected.topicAbsent) assert.equal(intake?.topic, undefined, scenario.id);
    if (expected.textContains) assert.ok(text.includes(expected.textContains), `${scenario.id}: ${text}`);
    if (expected.invalidatesConfirmation) assert.equal(workflow.invalidateConfirmation, true, scenario.id);
    if (expected.cancelled) assert.equal(intake, undefined, scenario.id);
  }
}
for (const row of adversarial) {
  if (row.invalidFrame) assert.throws(() => parseFrame(row.invalidFrame), undefined, row.id);
  else if (row.expected === 'reject_input') assert.ok(admit(row.input).error, row.id);
  else assert.equal(resolveSemantic(parseFrame(row.frame)).decision, undefined, row.id);
}

const predictionFlag = process.argv.indexOf('--predictions');
let measured = null;
if (predictionFlag >= 0) {
  const predictions = readFileSync(resolve(process.argv[predictionFlag + 1]), 'utf8').trim().split('\n').map(line => JSON.parse(line));
  const byId = new Map(predictions.map(row => [row.id, row]));
  assert.equal(byId.size, predictions.length, 'Duplicate prediction IDs');
  const evaluation = corpus.filter(row => row.partition === 'evaluation' && byId.has(row.id));
  assert.ok(evaluation.length, 'No independent evaluation predictions');
  let goals = 0, slots = 0, acts = 0, invalid = 0, outside = 0, outsideCorrect = 0, falseExecution = 0;
  const stable = value => JSON.stringify(value, (key, item) => item && typeof item === 'object' && !Array.isArray(item)
    ? Object.fromEntries(Object.entries(item).sort(([a], [b]) => a.localeCompare(b))) : item);
  for (const row of evaluation) {
    const expected = parseFrame(row.expectedFrame);
    if (expected.dialogueAct === 'OUT_OF_SCOPE') outside++;
    try {
      const observed = parseFrame(byId.get(row.id).frame);
      if (stable(observed.goals.map(item => item.goal)) === stable(expected.goals.map(item => item.goal))) goals++;
      if (stable(observed.goals) === stable(expected.goals)) slots++;
      if (observed.dialogueAct === expected.dialogueAct) acts++;
      if (expected.dialogueAct === 'OUT_OF_SCOPE' && observed.dialogueAct === 'OUT_OF_SCOPE') outsideCorrect++;
      if (!resolveSemantic(expected).decision?.intents.length && resolveSemantic(observed).decision?.intents.length) falseExecution++;
    } catch { invalid++; }
  }
  measured = { evaluatedPredictions: evaluation.length, goalAccuracy: goals / evaluation.length,
    exactGoalAndSlotAccuracy: slots / evaluation.length, dialogueActAccuracy: acts / evaluation.length,
    schemaFailureRate: invalid / evaluation.length, outOfScopeRecall: outside ? outsideCorrect / outside : null,
    falseExecutableProposalRate: falseExecution / evaluation.length,
    note: 'Execution proposals only; the harness never authorizes or dispatches UI/business operations.' };
}
timings.sort((a, b) => a - b);
const report = {
  schemaVersion: 'astra-semantic-evaluation-v1', generatedAt: new Date().toISOString(),
  evidence: 'OFFLINE_ORACLE_SEMANTICS; no model language-understanding evaluation without predictions',
  records: { semantic: corpus.length, workflows: scenarios.length, workflowTurns, adversarial: adversarial.length,
    development: [...corpus, ...scenarios, ...adversarial].filter(row => row.partition === 'development').length,
    evaluation: [...corpus, ...scenarios, ...adversarial].filter(row => row.partition === 'evaluation').length },
  deterministic: { semanticFramesValidated: corpus.length, workflowScenariosPassed: scenarios.length,
    adversarialChecksPassed: adversarial.length, contextualSubjectTurns: localSubjectTurns,
    legacyFastPathMatches: localMatches, legacyLocalRoutingCoverage: localMatches / corpus.length,
    resolverP50Ms: timings[Math.floor(timings.length * .5)], resolverP95Ms: timings[Math.floor(timings.length * .95)] },
  upstreamAttempts: 0, modelMetrics: measured,
  limits: ['Synthetic fixture labels require team review.', 'No live language accuracy, token usage, billing, UI latency or academic correctness measured.',
    'The approximately 700-record coverage target is not reached; this is the initial representative subset.',
    'Routing matches measure coverage, not accuracy; exact phrase rules were not fitted to evaluation data.'],
};
const outputFlag = process.argv.indexOf('--output');
if (outputFlag >= 0) writeFileSync(resolve(process.argv[outputFlag + 1]), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
