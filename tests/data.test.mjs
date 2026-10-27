import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const readJson = async (name) => JSON.parse(await readFile(new URL(`../data/${name}`, import.meta.url), 'utf8'));

test('canonical IDs are unique and references resolve', async () => {
  const [interventions, claims, sources] = await Promise.all([
    readJson('interventions.json'), readJson('claims.json'), readJson('sources.json')
  ]);
  const unique = (items) => new Set(items.map((x) => x.id));
  assert.equal(unique(interventions).size, interventions.length);
  assert.equal(unique(claims).size, claims.length);
  assert.equal(unique(sources).size, sources.length);

  const claimIds = unique(claims);
  const sourceIds = unique(sources);
  for (const item of interventions) for (const id of item.claim_ids) assert.ok(claimIds.has(id), `${item.id} -> ${id}`);
  for (const claim of claims) for (const id of claim.source_ids) assert.ok(sourceIds.has(id), `${claim.id} -> ${id}`);
});

test('public records preserve limitations and review dates', async () => {
  const [interventions, claims] = await Promise.all([readJson('interventions.json'), readJson('claims.json')]);
  for (const item of interventions) {
    assert.ok(item.safety_note.length > 20);
    assert.match(item.reviewed_at, /^\d{4}-\d{2}-\d{2}$/);
  }
  for (const claim of claims) {
    assert.ok(claim.limitations.length >= 1);
    assert.ok(claim.source_claims.length >= 1);
  }
});
