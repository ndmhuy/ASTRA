// Offline routing evaluation. This process has no provider or browser transport.
import fs from 'node:fs';
import crypto from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { fastRoute, admit } from '../astra-frontend/src/agent/recipes.ts';
import { catalogMeaning } from '../astra-frontend/src/agent/local.ts';
import { contextualSubject } from '../astra-frontend/src/agent/semantics.ts';
const root = new URL('../', import.meta.url);
const read = path => JSON.parse(fs.readFileSync(new URL(path, root), 'utf8'));
const bytes = fs.readFileSync(new URL('eval/agent-v3/scenarios.json', root));
const corpus = JSON.parse(bytes);
const formats = read('eval/agent-semantic/local-catalog.fixture.json');
const goals = {...read('src/exam_baseline/resources/agent/semantic-catalog.json').goals,
  ...read('src/exam_baseline/resources/agent/local-actions.json').goals};
const v3 = process.argv.includes('--v3') ? await import('../astra-frontend/src/agent/intelligence.ts') : null;
let accepted = 0, correct = 0;
const start = performance.now();
const cases = corpus.cases.map(item => {
  const state = corpus.states[item.state];
  let observed;
  if (admit(item.message).error) observed = {outcome: 'invalid'};
  else if (v3) {
    const local = v3.understandLocal(item.message, {formats, intake: state.intake});
    observed = local.frame ? {goal:local.frame.goals[0]?.goal, parameters:local.frame.goals[0]?.parameters ?? {}, outcome:local.kind} : {outcome:'defer'};
  } else {
    const local = fastRoute(item.message) ?? catalogMeaning(item.message, formats) ?? contextualSubject(item.message, state.intake, formats);
    if (local?.intake) observed = {goal: local.intake.mode === 'structure' ? 'READ_EXAM_STRUCTURE' : 'PREPARE_EXAM', parameters:local.intake};
    else if (local?.intents) observed = {goal:Object.entries(goals).find(([,def])=>def.capability===local.intents[0].id)?.[0], parameters:local.intents[0].args};
    else observed = {outcome:local ? 'message' : 'defer'};
  }
  const isAccepted = Boolean(observed.goal);
  const matches = item.expected.outcome ? observed.outcome === item.expected.outcome :
    observed.goal === item.expected.goal && Object.entries(item.expected.parameters ?? {}).every(([key,value])=>observed.parameters?.[key]===value);
  if (isAccepted) { accepted++; if(matches) correct++; }
  return {id:item.id, split:item.split, family:item.family, expected:item.expected, observed, accepted:isAccepted, correct:matches};
});
const report = {schemaVersion:'astra-agent-v3-results', mode:v3?'v3-local':'baseline-local',
  corpusSha256:crypto.createHash('sha256').update(bytes).digest('hex'), provenance:corpus.provenance,
  cases:cases.length, accepted, correctAccepted:correct, accuracyAmongAccepted:accepted?correct/accepted:null,
  coverage:accepted/cases.length, elapsedMs:performance.now()-start, providerCalls:0,
  limitation:'Routing only; prohibited operations require workflow/UI tests. Deferred cases are not counted as understood. No model accuracy measured.', results:cases};
const output = process.argv.find(arg=>arg.startsWith('--output='))?.slice(9);
report.bySplit=Object.fromEntries(['development','challenge'].map(split=>{
  const selected=cases.filter(item=>item.split===split),accepted=selected.filter(item=>item.accepted);
  return [split,{cases:selected.length,accepted:accepted.length,correctAccepted:accepted.filter(item=>item.correct).length,
    deferred:selected.filter(item=>item.observed.outcome==='defer').length,
    falseAccepted:accepted.filter(item=>!item.correct).map(item=>item.id)}];
}));
if(v3)report.engineSha256=crypto.createHash('sha256').update(fs.readFileSync(new URL('astra-frontend/src/agent/intelligence.ts',root))).digest('hex');
if(output) fs.writeFileSync(new URL(output,root),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({...report,results:undefined},null,2));
