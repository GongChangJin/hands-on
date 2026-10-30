import test from 'node:test';
import assert from 'node:assert/strict';
import { createHandoffPlan, validateHandoffPlan } from '../src/plan.mjs';
import { boundaryCases, runBoundaryCase, sampleEvidence } from '../src/scenarios.mjs';

test('source-only manifest roundtrips without executable state or original object aliasing',()=>{
  const evidence=sampleEvidence();const plan=createHandoffPlan(evidence);
  evidence.source.files[0].path='changed.txt';
  assert.equal(plan.source.files[0].path,'README.md');
  assert.deepEqual(validateHandoffPlan(JSON.parse(JSON.stringify(plan))),plan);
  assert.equal(plan.target.auto_resume,false);
  assert.equal(plan.target.requires_new_task,true);
});
for(const item of boundaryCases)test(item.id,()=>runBoundaryCase(item));

test('uncertain delivery cannot create a successful handoff',()=>{
  const evidence=sampleEvidence();evidence.completion.delivery='uncertain';
  assert.throws(()=>createHandoffPlan(evidence),/delivery_not_confirmed/);
});
test('duplicate and malformed source digests fail closed',()=>{
  const evidence=sampleEvidence();evidence.source.files.push({...evidence.source.files[0]});
  assert.throws(()=>createHandoffPlan(evidence),/invalid_source_digest/);
  evidence.source.files.pop();evidence.source.files[0].sha256='not-a-hash';
  assert.throws(()=>createHandoffPlan(evidence),/invalid_source_digest/);
});
test('nested unknown fields and missing checks cannot silently become portable',()=>{
  const evidence=sampleEvidence();evidence.source.files[0].content='unreviewed secret-bearing content';
  assert.throws(()=>createHandoffPlan(evidence),/source_file_unknown_or_missing_field/);
  delete evidence.source.files[0].content;delete evidence.checks.tests_passed;
  assert.throws(()=>createHandoffPlan(evidence),/checks_unknown_or_missing_field/);
});
test('access-code spelling variants and runtime state locations cannot enter a source manifest',()=>{
  for(const path of ['access_code.txt','access-code.txt','config/access_code.json','sessions/runtime.json','state/workspace.json','workspace.json','runtime/log.txt']){
    const evidence=sampleEvidence();evidence.source.files[0].path=path;
    assert.throws(()=>createHandoffPlan(evidence),/unsafe_source_path/,path);
  }
});
