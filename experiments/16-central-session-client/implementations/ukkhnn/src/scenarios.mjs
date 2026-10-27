import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { performance } from 'node:perf_hooks';
import { openWorkspaceServer } from './server.mjs';
import { WorkspaceClient } from './client.mjs';

export const fixtureTokens = new Map([
  ['fixture-client-a-0000000000000000', 'owner'],
  ['fixture-client-b-0000000000000000', 'owner'],
  ['fixture-other-user-00000000000000', 'other'],
]);
export async function withServer(fn) {
  const directory = mkdtempSync(join(tmpdir(), 'gcj-client-'));
  let server;
  try {
    server = await openWorkspaceServer({directory, tokens: fixtureTokens});
    const a = new WorkspaceClient(server.origin, [...fixtureTokens.keys()][0]);
    const b = new WorkspaceClient(server.origin, [...fixtureTokens.keys()][1]);
    const other = new WorkspaceClient(server.origin, [...fixtureTokens.keys()][2]);
    await a.request('/tasks', {method:'POST', data:{id:'task-a', projectId:'project'}});
    return await fn({server,a,b,other,directory});
  } finally { await server?.close(); rmSync(directory,{recursive:true,force:true}); }
}

export async function evaluateScenarios() {
  const records=[];
  const run=async (id,expected,fn)=>{
    const start=performance.now();
    try { await withServer(fn); records.push({id,expected,observed:expected,passed:true,latency_ms:performance.now()-start}); }
    catch(error) { records.push({id,expected,observed:'assertion_failed',passed:false,error:error.code??error.name,latency_ms:performance.now()-start}); }
  };
  await run('same-owner-two-clients','shared_task', async({a,b})=>{
    assert.deepEqual(await a.request('/tasks/task-a'), await b.request('/tasks/task-a'));
  });
  await run('instruction-dedup','one_message',async({a,b})=>{
    for(const client of [a,b]) await client.request('/tasks/task-a/instructions',{method:'POST',data:{id:'m1',text:'Inspect fixture'}});
    assert.equal((await a.request('/tasks/task-a/instructions')).length,1);
  });
  await run('cursor-reconnect','no_repeat',async({a,b})=>{
    await b.events('task-a');
    await a.request('/tasks/task-a/instructions',{method:'POST',data:{id:'m1',text:'Inspect fixture'}});
    const events=await b.events('task-a');
    assert.equal(events.filter(e=>e.type==='instruction.requested').length,1);
    assert.deepEqual(await b.events('task-a'),[]);
  });
  await run('other-owner-read','denied_404',async({other})=>assert.rejects(other.request('/tasks/task-a'),{status:404}));
  await run('missing-auth','denied_401',async({server})=>assert.equal((await fetch(server.origin+'/tasks/task-a')).status,401));
  await run('foreign-origin','denied_403',async({a})=>assert.rejects(a.request('/tasks/task-a',{headers:{origin:'https://untrusted.invalid'}}),{status:403}));
  await run('invalid-cursor','denied_400',async({a})=>assert.rejects(a.request('/tasks/task-a/events?after=-1'),{status:400}));
  await run('stop-is-request','not_runtime_confirmation',async({a,server})=>{
    await a.request('/tasks/task-a/instructions',{method:'POST',data:{id:'m1',text:'Inspect fixture'}});
    const result=await a.request('/tasks/task-a/control',{method:'POST',data:{action:'stop'}});
    assert.equal(result.runtimeStopped,false); assert.equal(result.state,'stop_requested');
    assert.equal(server.queue.next('task-a'),null);
    assert.equal((await a.request('/tasks/task-a/instructions')).length,1);
  });
  await run('restart-uncertain','no_redispatch',async({a,server,directory})=>{
    await a.request('/tasks/task-a/instructions',{method:'POST',data:{id:'m1',text:'Inspect fixture'}});
    assert.ok(server.queue.next('task-a'));
    await server.close();
    const reopened=await openWorkspaceServer({directory,tokens:fixtureTokens});
    try { assert.equal(reopened.queue.list('task-a')[0].status,'uncertain'); assert.equal(reopened.queue.next('task-a'),null); }
    finally { await reopened.close(); }
  });
  return records;
}
