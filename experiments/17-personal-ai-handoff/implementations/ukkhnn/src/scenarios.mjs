import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { createHandoffPlan, validateHandoffPlan, sha256 } from './plan.mjs';
import { runComposedWorkflow } from './workflow.mjs';

export function sampleEvidence() {
  return {source:{repository:'fixture://contract-only',revision:'a'.repeat(40),files:[{path:'README.md',sha256:sha256('synthetic source')}]},
    completion:{runtime:'idle',delivery:'completed',pending:0},approval:{allowed:true,consumed:true},checks:{source_clean:true,tests_passed:true}};
}

export const boundaryCases = [
  {id:'unknown-schema',expected:'unsupported_handoff_schema',change:plan=>{plan.schema_version=99;}},
  {id:'auth-field',expected:'plan_unknown_or_missing_field',change:plan=>{plan.auth={token:'fixture-only-secret'};}},
  {id:'active-session-field',expected:'target_unknown_or_missing_field',change:plan=>{plan.target.runtime_session_id='fixture-active-session';}},
  {id:'absolute-path',expected:'unsafe_source_path',change:plan=>{plan.source.files[0].path='/private/tmp/runtime/file.txt';}},
  {id:'traversal-path',expected:'unsafe_source_path',change:plan=>{plan.source.files[0].path='src/../../auth.json';}},
  {id:'private-file',expected:'unsafe_source_path',change:plan=>{plan.source.files[0].path='config/credentials.json';}},
  {id:'runtime-state-file',expected:'unsafe_source_path',change:plan=>{plan.source.files[0].path='sessions/runtime.json';}},
  {id:'array-revision',expected:'invalid_source_revision',change:plan=>{plan.source.revision=['a'.repeat(40)];}},
  {id:'array-digest',expected:'invalid_source_digest',change:plan=>{plan.source.files[0].sha256=['b'.repeat(64)];}},
  {id:'credential-url',expected:'unsafe_repository',change:plan=>{plan.source.repository='https://user:token@github.com/example/project';}},
  {id:'auto-resume',expected:'auto_resume_forbidden',change:plan=>{plan.target.auto_resume=true;}},
  {id:'pending-instructions',expected:'instructions_remaining',evidence:value=>{value.completion.pending=1;}},
  {id:'runtime-still-running',expected:'runtime_not_idle',evidence:value=>{value.completion.runtime='running';}},
  {id:'approval-not-consumed',expected:'approval_not_consumed',evidence:value=>{value.approval.consumed=false;}},
  {id:'dirty-source',expected:'source_checks_incomplete',evidence:value=>{value.checks.source_clean=false;}},
];

export function runBoundaryCase(item) {
  const value=sampleEvidence();
  const action=item.evidence?()=>{item.evidence(value);return createHandoffPlan(value);}:()=>{const plan=createHandoffPlan(value);item.change(plan);return validateHandoffPlan(plan);};
  assert.throws(action,{message:item.expected});
  return {outcome:item.expected,checkpoints:[],traces:[]};
}

export async function evaluateScenarios() {
  const records=[];
  const run=async(id,expected,fn)=>{
    const started=performance.now();
    try { const value=await fn();assert.equal(value.outcome,expected);records.push({id,expected,observed:value.outcome,passed:true,latency_ms:performance.now()-started,...value}); }
    catch(error){records.push({id,expected,observed:'assertion_failed',passed:false,error:error.name,latency_ms:performance.now()-started,checkpoints:[],traces:[]});}
  };
  await run('completed-restart-handoff','completed_source_handoff',()=>runComposedWorkflow());
  await run('uncertain-restart-denial','uncertain_delivery_blocks_handoff',()=>runComposedWorkflow({interruption:'restart-before-completion'}));
  await run('stop-confirmation','stop_confirmed_without_handoff',()=>runComposedWorkflow({interruption:'stop-request'}));
  for(const item of boundaryCases)await run(item.id,item.expected,()=>runBoundaryCase(item));
  return records;
}
