import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dataset, evaluate, contexts } from '../scripts/local-routing-eval.mjs';

test('routing development families meet their declared semantics; evaluation never executes unsafe inputs', () => {
  assert.equal(new Set(dataset.families.map(group => group.id)).size, dataset.families.length);
  const result = evaluate();
  assert.deepEqual(result.dev.mismatches, []);
  assert.equal(result.eval.falseExecutions, 0, JSON.stringify(result.eval.mismatches));
  assert.deepEqual(contexts().mismatches, []);
});
