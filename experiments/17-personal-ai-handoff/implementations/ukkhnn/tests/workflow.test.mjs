import test from 'node:test';
import assert from 'node:assert/strict';
import { runComposedWorkflow } from '../src/workflow.mjs';

test('10–16 compose through accepted, approved, completed, persisted and reconnected source handoff',async()=>{
  const result=await runComposedWorkflow();
  assert.equal(result.outcome,'completed_source_handoff');
  assert.deepEqual(result.modules_used,[10,11,12,13,14,15,16]);
  assert.equal(result.source_plan.source.files.length,2);
  assert.equal(result.selected_memory_count,1);
  assert.equal(result.checkpoints.find(row=>row.stage==='accepted').completed,false);
  assert.equal(result.checkpoints.at(-1).duplicates,0);
  assert.equal(result.source_plan.target.auto_resume,false);
  assert.ok(result.traces.some(row=>row.operation==='/session/:id/prompt_async'&&row.status===204));
});
test('restart after accepted delivery retains uncertainty and never re-dispatches',async()=>{
  const result=await runComposedWorkflow({interruption:'restart-before-completion'});
  assert.equal(result.outcome,'uncertain_delivery_blocks_handoff');
  assert.equal(result.checkpoints.at(-1).automatic_resends,0);
  assert.equal(result.source_plan,undefined);
});
test('stop request requires runtime idle confirmation and keeps queued followup',async()=>{
  const result=await runComposedWorkflow({interruption:'stop-request'});
  assert.equal(result.outcome,'stop_confirmed_without_handoff');
  assert.equal(result.checkpoints.at(-1).queue_preserved,true);
  assert.equal(result.source_plan,undefined);
  assert.equal(result.traces.filter(row=>row.operation==='/session/:id/abort').length,1);
});
