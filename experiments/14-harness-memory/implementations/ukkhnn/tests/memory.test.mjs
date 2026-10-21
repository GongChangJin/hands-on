import test from 'node:test';
import assert from 'node:assert/strict';
import {createMemoryRecord,selectMemory,memoryForHarness} from '../src/memory.mjs';
const memory=(changes={})=>({id:'preference',projectId:'project-a',revision:1,supersedes:null,text:'Use concise notes',deleted:false,
  source:{uri:'fixture://notes/1',hash:'a'.repeat(64),observedAt:100},expiresAt:1000,...changes});
const scope={projectId:'project-a',now:500};

test('scope selection never mixes project memories',()=>{
  const selected=selectMemory([memory(),memory({projectId:'project-b',text:'private'})],scope);
  assert.equal(selected.length,1);assert.equal(selected[0].projectId,'project-a');
  assert.deepEqual(selectMemory([memory()],{...scope,projectId:'other'}),[]);
});
test('same revision with conflicting facts fails closed',()=>{
  assert.throws(()=>selectMemory([memory(),memory({text:'conflict'})],scope),/conflicting_revision/);
  assert.equal(selectMemory([memory(),memory()],scope).length,1);
});
test('expired newest record cannot resurrect a still-valid old record',()=>{
  const newer=memory({revision:2,supersedes:1,expiresAt:400,source:{uri:'fixture://notes/2',hash:'b'.repeat(64),observedAt:200}});
  assert.deepEqual(selectMemory([newer,memory()],scope),[]);
});
test('tombstones suppress previous memory, including when the tombstone expires',()=>{
  const deleted=memory({revision:2,supersedes:1,deleted:true,expiresAt:300,source:{uri:'fixture://deletion',hash:'b'.repeat(64),observedAt:200}});
  assert.deepEqual(selectMemory([memory(),deleted],scope),[]);
});
test('snapshot and returned records cannot be changed by callers',()=>{
  const input=memory();const record=createMemoryRecord(input);input.source.uri='forged';
  assert.equal(record.source.uri,'fixture://notes/1');
  assert.throws(()=>selectMemory([record],scope)[0].source.hash='b'.repeat(64),TypeError);
});
test('provenance, history and trusted clock constraints are enforced',()=>{
  assert.throws(()=>selectMemory([memory({source:{uri:'',hash:'x',observedAt:100}})],scope),/provenance/);
  assert.throws(()=>selectMemory([memory({revision:2,supersedes:1})],scope),/missing_revision_history/);
  assert.throws(()=>selectMemory([memory(),memory({revision:2,supersedes:1}),memory({revision:3,supersedes:1})],scope),/forked/);
  assert.throws(()=>selectMemory([memory()],{...scope,now:50}),/future_provenance/);
});
test('expiry is exclusive and disabled harness cannot retrieve memory',()=>{
  assert.deepEqual(selectMemory([memory()],{...scope,now:1000}),[]);
  assert.deepEqual(memoryForHarness({template:{memory:{enabled:false}}},[memory()],500),[]);
});
