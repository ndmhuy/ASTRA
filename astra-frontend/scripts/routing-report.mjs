// Offline measurements only: no network, provider, browser, or generated exam.
import { execFileSync } from 'node:child_process';
import { writeFileSync, unlinkSync } from 'node:fs';
import { evaluate, contexts, latency } from './local-routing-eval.mjs';

const baselineSha = '98b1df5467255b5de94f0b3191b5613db33bd48a';
const current = evaluate();
const scratch = new URL(`../src/agent/.routing-baseline-${process.pid}.ts`, import.meta.url);
let baseline;
try {
  writeFileSync(scratch, execFileSync('git', ['show', `${baselineSha}:astra-frontend/src/agent/recipes.ts`], { encoding: 'utf8' }));
  const original = await import(scratch.href);
  baseline = evaluate(original.fastRoute, false);
} finally { unlinkSync(scratch); }
const reduction = Object.fromEntries(['dev', 'eval'].map(split => [split, {
  baselineModelFallbacks: baseline[split].modelFallbacks, currentModelFallbacks: current[split].modelFallbacks,
  avoidedFallbacks: baseline[split].modelFallbacks - current[split].modelFallbacks,
  avoidedPercent: Number((100 * (baseline[split].modelFallbacks - current[split].modelFallbacks) / Math.max(1, baseline[split].modelFallbacks)).toFixed(2)),
}]));
const report = { schemaVersion: 'astra-local-routing-results-v1', baselineSha,
  scope: 'Authored local routing fixtures and deterministic context selection only. Split by paraphrase family; no LLM accuracy, rendered UI latency, production traffic or inference claims. Baseline recipes plus unchanged subject shorthand versus current recipes/catalog/shorthand. One evaluation safety failure (mixed note/approval) was fixed and retained as regression; reported evaluation is post-fix, not blind.',
  current, baseline, context: contexts(), fallbackReduction: reduction, localLatency: latency(), inferenceAttempts: 0 };
console.log(JSON.stringify(report, null, 2));
if (process.argv.includes('--save')) writeFileSync(new URL('../../eval/agent-semantic/local-routing-results.json', import.meta.url), JSON.stringify(report, null, 2) + '\n');
if (current.dev.falseExecutions || current.eval.falseExecutions || report.context.mismatches.length) process.exitCode = 1;
