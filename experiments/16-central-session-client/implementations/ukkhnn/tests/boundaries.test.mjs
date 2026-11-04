import test from 'node:test';
import assert from 'node:assert/strict';
import { request as httpRequest } from 'node:http';
import { withServer } from '../src/scenarios.mjs';
import { WorkspaceClient } from '../src/client.mjs';

test('foreign owner cannot read events, enqueue, or stop',()=>withServer(async({other})=>{
  for (const [path,method,data] of [['events','GET'],['instructions','POST',{id:'m',text:'x'}],['control','POST',{action:'stop'}]]) {
    await assert.rejects(other.request('/tasks/task-a/'+path,{method,data}),{status:404});
  }
}));
test('authentication and browser origin are both enforced',()=>withServer(async({a,server})=>{
  assert.equal((await fetch(server.origin+'/tasks/task-a')).status,401);
  await assert.rejects(a.request('/tasks/task-a',{headers:{origin:'https://evil.invalid'}}),{status:403});
  const status=await new Promise((resolve,reject)=>{
    const req=httpRequest(server.origin+'/tasks/task-a',{headers:{host:'evil.invalid',authorization:`Bearer ${a.token}`,origin:server.origin}},res=>{res.resume();resolve(res.statusCode);});
    req.on('error',reject);req.end();
  });
  assert.equal(status,403);
}));
test('invalid cursor and input cannot mutate task ownership',()=>withServer(async({a})=>{
  for(const cursor of ['-1','1.5','1e2','9007199254740992']) await assert.rejects(a.request('/tasks/task-a/events?after='+cursor),{status:400});
  await assert.rejects(a.request('/tasks/task-a/events?after=99'),{status:409});
  await assert.rejects(a.request('/tasks',{method:'POST',data:{id:'new',projectId:'p',ownerId:'other'}}),{status:400});
  await assert.rejects(a.request('/tasks/task-a/instructions',{method:'POST',data:{id:'m',text:''}}),{status:400});
}));
test('client refuses external endpoint and credential URL',()=>{
  for(const origin of ['https://example.com','http://user:pass@127.0.0.1','http://127.0.0.1/path']) assert.throws(()=>new WorkspaceClient(origin,'test'));
});
test('fresh approval is bound to content and cannot be consumed twice',()=>withServer(async({a,other,server})=>{
  const action={kind:'write-fixture',path:'answer.txt'};
  server.approvals.request({id:'approval1',taskId:'task-a',ownerId:'owner',action,revision:1,expiresAt:Date.now()+60000});
  const path='/tasks/task-a/approvals/approval1/decision';
  await assert.rejects(other.request(path,{method:'POST',data:{action,revision:1,allow:true}}),{status:404});
  const changed=await a.request(path,{method:'POST',data:{action:{...action,path:'different.txt'},revision:1,allow:true}});
  assert.equal(changed.allowed,false);
  const allowed=await a.request(path,{method:'POST',data:{action,revision:1,allow:true}});
  assert.equal(allowed.allowed,true);
  const replay=await a.request(path,{method:'POST',data:{action,revision:1,allow:true}});
  assert.equal(replay.allowed,false);
  const events=await a.events('task-a');
  assert.deepEqual(events.filter(e=>e.type==='approval.decided').map(e=>e.payload.allowed),[false,true,false]);
}));
test('fresh empty task can be stopped and resumed',()=>withServer(async({a})=>{
  assert.deepEqual(await a.request('/tasks/task-a/instructions'),[]);
  for(const action of ['stop','resume']) await a.request('/tasks/task-a/control',{method:'POST',data:{action}});
}));
