import test from 'node:test';
import assert from 'node:assert/strict';
import { withServer } from '../src/scenarios.mjs';

test('same owner shares a task and reconnect cursor without replay',()=>withServer(async({a,b})=>{
  await b.events('task-a');
  await a.request('/tasks/task-a/instructions',{method:'POST',data:{id:'first',text:'first'}});
  const events=await b.events('task-a');
  assert.equal(events.length,1); assert.equal(events[0].payload.messageId,'first');
  assert.deepEqual(await b.events('task-a'),[]);
}));
test('duplicate id does not duplicate work; changed payload conflicts',()=>withServer(async({a,b})=>{
  await a.request('/tasks/task-a/instructions',{method:'POST',data:{id:'first',text:'first'}});
  await b.request('/tasks/task-a/instructions',{method:'POST',data:{id:'first',text:'first'}});
  await assert.rejects(b.request('/tasks/task-a/instructions',{method:'POST',data:{id:'first',text:'changed'}}),{status:409});
  assert.equal((await a.request('/tasks/task-a/instructions')).length,1);
}));
test('stop preserves messages without claiming process termination',()=>withServer(async({a,server})=>{
  await a.request('/tasks/task-a/instructions',{method:'POST',data:{id:'first',text:'first'}});
  const state=await a.request('/tasks/task-a/control',{method:'POST',data:{action:'stop'}});
  assert.equal(state.runtimeStopped,false); assert.equal(server.queue.next('task-a'),null);
  await a.request('/tasks/task-a/control',{method:'POST',data:{action:'resume'}});
  assert.ok(server.queue.next('task-a'));
}));
test('audit failure preserves truthful durable instruction receipt and dedup',()=>withServer(async({a,server})=>{
  server.store.appendEvent=()=>{throw new Error('injected_audit_failure');};
  for(let attempt=0;attempt<2;attempt++) {
    const receipt=await a.request('/tasks/task-a/instructions',{method:'POST',data:{id:'first',text:'first'}});
    assert.equal(receipt.id,'first');assert.equal(receipt.audit_recorded,false);
  }
  assert.equal(server.queue.list('task-a').length,1);
  assert.deepEqual(server.store.events('task-a'),[]);
}));
test('consumed approval remains acknowledged when audit write fails',()=>withServer(async({a,server})=>{
  const action={kind:'fixture',path:'answer.txt'};
  server.approvals.request({id:'approval1',taskId:'task-a',ownerId:'owner',action,revision:1,expiresAt:Date.now()+60000});
  server.store.appendEvent=()=>{throw new Error('injected_audit_failure');};
  const path='/tasks/task-a/approvals/approval1/decision';
  const receipt=await a.request(path,{method:'POST',data:{action,revision:1,allow:true}});
  assert.equal(receipt.allowed,true);assert.equal(receipt.audit_recorded,false);
  const replay=await a.request(path,{method:'POST',data:{action,revision:1,allow:true}});
  assert.equal(replay.allowed,false);assert.equal(replay.reason,'already_consumed');
}));
