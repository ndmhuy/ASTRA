// Pure routing/target evaluation: never imports an HTTP or model adapter.
import { readFileSync } from 'node:fs';
import { performance } from 'node:perf_hooks';
import { fastRoute, admit, mayDispatch } from '../src/agent/recipes.ts';
import { catalogMeaning } from '../src/agent/local.ts';
import { shortSubjectIntake } from '../src/agent/knowledge.ts';
import { generationTarget } from '../src/agent/lifecycle.ts';

export const dataset = JSON.parse(readFileSync(new URL('../../eval/agent-semantic/local-routing.json', import.meta.url), 'utf8'));
// Snapshot generated offline by exam_baseline.ui.contracts.format_catalog().
export const formats = JSON.parse(readFileSync(new URL('../../eval/agent-semantic/local-catalog.fixture.json', import.meta.url), 'utf8'));

export function classify(message, route = fastRoute, extended = true) {
  if (admit(message).error) return { kind: 'invalid', local: true };
  const result = route(message) ?? (extended ? catalogMeaning(message, formats) : undefined) ??
    (message.length <= 80 ? (() => { const intake = shortSubjectIntake(message); return intake ? { intake } : undefined; })() : undefined);
  if (!result) return { kind: mayDispatch(message) ? 'needs_model' : 'guard', local: false };
  if ('text' in result) return { kind: 'message', local: true };
  if ('confirm' in result) return { kind: 'confirm', args: { confirm: result.confirm }, local: true };
  if ('intake' in result) return { kind: 'intake', args: result.intake, local: true };
  return { kind: result.intents[0].id, args: result.intents[0].args, local: true };
}

export function matches(actual, [, expected, args]) {
  if (expected === 'safe') return ['message', 'needs_model', 'guard', 'invalid'].includes(actual.kind);
  return actual.kind === expected && Object.entries(args ?? {}).every(([key, value]) => actual.args?.[key] === value);
}

export function evaluate(route = fastRoute, extended = true) {
  return Object.fromEntries(['dev', 'eval'].map(split => {
    const families = dataset.families.filter(family => family.split === split);
    const records = families.flatMap(family => family.cases.map(row => ({ family: family.id, row, actual: classify(row[0], route, extended) })));
    const matched = records.filter(record => matches(record.actual, record.row));
    const accepted = records.filter(record => record.actual.local);
    const wrong = accepted.filter(record => !matches(record.actual, record.row));
    const safety = records.filter(record => record.row[1] === 'safe');
    const falseExecutions = safety.filter(record => !matches(record.actual, record.row));
    const semantic = records.filter(record => !['safe', 'invalid'].includes(record.row[1]));
    const percent = (n, d) => d ? Number((100 * n / d).toFixed(2)) : 0;
    return [split, { families: families.length, cases: records.length,
      matched: matched.length, accuracyPercent: percent(matched.length, records.length),
      semanticCases: semantic.length, semanticCorrect: semantic.filter(record => matches(record.actual, record.row)).length,
      accepted: accepted.length, coveragePercent: percent(accepted.length, records.length),
      safetyCases: safety.length, falseExecutions: falseExecutions.length, falseExecutionPercent: percent(falseExecutions.length, safety.length),
      incorrectFastPaths: wrong.length, incorrectAcceptancePercent: percent(wrong.length, accepted.length),
      modelFallbacks: records.filter(record => record.actual.kind === 'needs_model').length,
      mismatches: records.filter(record => !matches(record.actual, record.row)).map(({ family, row, actual }) => ({ family, message: row[0], expected: row[1], expectedArgs: row[2], actual })),
    }];
  }));
}

export function contexts() {
  const mismatches = [];
  for (const item of dataset.contextCases) {
    const sessions = item.sessions.map(([id, title, status]) => ({ id, title, status: 'draft',
      ...( ['running', 'queued', 'retrying', 'pausing', 'resuming'].includes(status) ? { generationId: id } : { stoppedJobId: id }), progress: { status } }));
    const actual = generationTarget(sessions, item.current, item.operation, item.title).target?.id ?? null;
    if (actual !== item.expected) mismatches.push({ id: item.id, expected: item.expected, actual });
  }
  return { cases: dataset.contextCases.length, matched: dataset.contextCases.length - mismatches.length, mismatches };
}

export function latency() {
  const cases = dataset.families.flatMap(family => family.cases);
  cases.forEach(([message]) => classify(message));
  const samples = [];
  for (let batch = 0; batch < 30; batch++) for (const [message] of cases) {
    const start = performance.now();
    classify(message);
    samples.push(performance.now() - start);
  }
  samples.sort((a, b) => a - b);
  return { samples: samples.length, p50ms: Number(samples[Math.ceil(samples.length * .5) - 1].toFixed(4)),
    p95ms: Number(samples[Math.ceil(samples.length * .95) - 1].toFixed(4)) };
}
