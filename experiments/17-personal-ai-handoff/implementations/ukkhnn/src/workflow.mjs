import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { RuntimeAdapter } from '../../../../10-runtime-adapter/implementations/ukkhnn/src/adapter.mjs';
import { startFixture } from '../../../../10-runtime-adapter/implementations/ukkhnn/src/fixture.mjs';
import { createHarnessSnapshot } from '../../../../14-harness-memory/implementations/ukkhnn/src/snapshot.mjs';
import { memoryForHarness } from '../../../../14-harness-memory/implementations/ukkhnn/src/memory.mjs';
import { TemporaryWorktreeLab } from '../../../../15-worktree-isolation/implementations/ukkhnn/src/worktrees.mjs';
import { openWorkspaceServer } from '../../../../16-central-session-client/implementations/ukkhnn/src/server.mjs';
import { WorkspaceClient } from '../../../../16-central-session-client/implementations/ukkhnn/src/client.mjs';
import { createHandoffPlan, sha256 } from './plan.mjs';

function syntheticContext(adapter, now) {
  const template = {
    version:1, prompt:'Read the supplied synthetic project note.',
    model:{id:'fixture-protocol',requiredCapabilities:['send']}, skills:[],tools:[],
    memory:{projectId:'project',enabled:true},permissions:{allowedTools:[],allowWrites:false},
  };
  const snapshot = createHarnessSnapshot(template,{capabilities:Object.entries(adapter.capabilities).filter(([,v])=>v).map(([k])=>k)});
  const memory = {id:'note',projectId:'project',revision:1,supersedes:null,text:'Synthetic source transfer requires a new task.',deleted:false,
    source:{uri:'fixture://project-note',hash:sha256('Synthetic source transfer requires a new task.'),observedAt:now-1000},expiresAt:now+60000};
  const selected = memoryForHarness(snapshot,[memory,{...memory,projectId:'other-project',text:'Other project context must not enter this request.'}],now);
  assert.equal(selected.length,1); assert.equal(selected[0].projectId,'project');
  // Only coordinator-side text injection is exercised. The adapter declares memory:false.
  assert.equal(adapter.capabilities.memory,false);
  const text = [snapshot.template.prompt,...selected.map(item=>item.text)].join('\n');
  return {snapshot,selected,text};
}

export async function runComposedWorkflow({ interruption = 'none' } = {}) {
  if (!['none','restart-before-completion','stop-request'].includes(interruption)) throw new Error('unknown_fixture_scenario');
  const directory = mkdtempSync(join(tmpdir(),'hands-on-handoff-'));
  const tokenA = randomBytes(24).toString('hex'), tokenB = randomBytes(24).toString('hex'), otherToken = randomBytes(24).toString('hex');
  const tokens = new Map([[tokenA,'owner'],[tokenB,'owner'],[otherToken,'other-owner']]);
  let server,fixture,lab; const checkpoints=[];
  try {
    fixture = await startFixture();
    const adapter = new RuntimeAdapter(fixture.url,{password:fixture.password});
    assert.equal((await adapter.health()).version,'fixture-v1');
    server = await openWorkspaceServer({directory,tokens});
    const a = new WorkspaceClient(server.origin,tokenA);
    let b = new WorkspaceClient(server.origin,tokenB);
    await a.request('/tasks',{method:'POST',data:{id:'task',projectId:'project'}});
    const other = new WorkspaceClient(server.origin,otherToken);
    await assert.rejects(other.request('/tasks/task'),{status:404});
    assert.equal((await b.request('/tasks/task')).ownerId,'owner');
    checkpoints.push({stage:'task_created',same_owner_read:true,other_owner_denied:true});

    const {snapshot,selected,text} = syntheticContext(adapter,Date.now());
    const {runtimeId} = await adapter.create('Synthetic handoff task');
    lab = TemporaryWorktreeLab.create();
    const worktree = lab.create('handoff');
    const action = {type:'fixture-write',path:'summary.txt',contentHash:sha256('source transfer verified\n')};
    server.approvals.request({id:'write-once',taskId:'task',ownerId:'owner',action,revision:1,expiresAt:Date.now()+60000});
    const approval = await b.request('/tasks/task/approvals/write-once/decision',{method:'POST',data:{action,revision:1,allow:true}});
    assert.equal(approval.allowed,true); assert.equal(approval.consumed,true);
    const repeated = await a.request('/tasks/task/approvals/write-once/decision',{method:'POST',data:{action,revision:1,allow:true}});
    assert.equal(repeated.allowed,false); assert.equal(repeated.reason,'already_consumed');
    checkpoints.push({stage:'approval_consumed',allowed:true,replay_allowed:false});

    await a.request('/tasks/task/instructions',{method:'POST',data:{id:'message-one',text}});
    await b.request('/tasks/task/instructions',{method:'POST',data:{id:'message-one',text}});
    assert.equal(server.queue.list('task').length,1);
    const first = server.queue.next('task');
    assert.equal(first.status,'sending');
    const receipt = await adapter.send(runtimeId,first);
    assert.deepEqual(receipt,{accepted:true,completed:false});
    assert.equal((await adapter.snapshot(runtimeId)).status,'running');
    await b.request('/tasks/task/instructions',{method:'POST',data:{id:'message-two',text:'Check the source-only result.'}});
    assert.equal(server.queue.next('task'),null);
    assert.equal(fixture.requests.filter(row=>row.path.endsWith('/abort')).length,0);
    server.store.appendEvent('task',{type:'runtime.accepted',payload:{completed:false}});
    await b.events('task');
    const lastCursor = b.cursors.get('task');
    checkpoints.push({stage:'accepted',delivery:'sending',completed:false,queued_followups:1,abort_calls:0});

    if (interruption === 'stop-request') {
      const stopped = await b.request('/tasks/task/control',{method:'POST',data:{action:'stop'}});
      assert.equal(stopped.runtimeStopped,false);
      assert.equal((await adapter.snapshot(runtimeId)).status,'running');
      await adapter.abort(runtimeId);
      assert.equal((await adapter.snapshot(runtimeId)).status,'idle');
      server.queue.markUncertain('task',first.id);
      server.queue.resolve('task',first.id,{outcome:'cancelled',evidence:'Fixture abort followed by idle snapshot.'});
      assert.equal(server.queue.list('task')[1].status,'queued');
      assert.equal(server.queue.next('task'),null);
      const exported=lab.exportSource('handoff');
      assert.throws(()=>createHandoffPlan({source:manifest(exported),completion:{runtime:'idle',delivery:'cancelled',pending:1},approval:{allowed:true,consumed:true},checks:{source_clean:true,tests_passed:true}}),/delivery_not_confirmed/);
      return {outcome:'stop_confirmed_without_handoff',modules_used:[10,11,12,13,14,15,16],checkpoints:[...checkpoints,{stage:'stop_confirmed',runtime_idle:true,queue_preserved:true,plan_created:false}],traces:adapter.transport.trace};
    }

    if (interruption === 'restart-before-completion') {
      const sends = fixture.requests.filter(row=>row.path.endsWith('/prompt_async')).length;
      await server.close();
      server = await openWorkspaceServer({directory,tokens});
      b = new WorkspaceClient(server.origin,tokenB); b.cursors.set('task',lastCursor);
      assert.equal(server.queue.list('task')[0].status,'uncertain');
      assert.equal(server.queue.next('task'),null);
      await assert.rejects(b.request('/tasks/task/control',{method:'POST',data:{action:'resume'}}),{status:409});
      assert.equal(fixture.requests.filter(row=>row.path.endsWith('/prompt_async')).length,sends);
      const exported=lab.exportSource('handoff');
      assert.throws(()=>createHandoffPlan({source:manifest(exported),completion:{runtime:'running',delivery:'uncertain',pending:1},approval:{allowed:true,consumed:true},checks:{source_clean:true,tests_passed:true}}),/delivery_not_confirmed/);
      return {outcome:'uncertain_delivery_blocks_handoff',modules_used:[10,11,12,13,14,15,16],checkpoints:[...checkpoints,{stage:'restarted',delivery:'uncertain',automatic_resends:0,plan_created:false}],traces:adapter.transport.trace};
    }

    // The test coordinator writes fixed synthetic text; no AI coding claim is made.
    lab.write('handoff','summary.txt','source transfer verified\n');
    assert.equal(readFileSync(join(worktree.path,'summary.txt'),'utf8'),'source transfer verified\n');
    assert.equal(readFileSync(join(lab.source,'fixture.txt'),'utf8'),'baseline\n');
    const revision = lab.commit('handoff','Record synthetic source handoff result');
    fixture.complete(runtimeId,'Synthetic first instruction completed.');
    let observed = await adapter.snapshot(runtimeId);
    assert.equal(observed.status,'idle'); assert.equal(observed.messages.at(-1).completed,true);
    server.queue.acknowledge('task',first.id);
    server.store.appendEvent('task',{type:'runtime.completed',payload:{message:'first',synthetic:true}});
    const second = server.queue.next('task'); assert.equal(second.id,'message-two');
    await adapter.send(runtimeId,second);
    fixture.complete(runtimeId,'Synthetic source check completed.');
    observed = await adapter.snapshot(runtimeId);
    assert.equal(observed.status,'idle'); assert.equal(observed.messages.at(-1).completed,true);
    server.queue.acknowledge('task',second.id);
    server.store.appendEvent('task',{type:'runtime.completed',payload:{message:'second',synthetic:true}});
    checkpoints.push({stage:'completed',completed_instructions:2,git_committed:true,working_tree_clean:!lab.status('handoff').dirty});

    await server.close();
    server = await openWorkspaceServer({directory,tokens});
    b = new WorkspaceClient(server.origin,tokenB); b.cursors.set('task',lastCursor);
    const replay = await b.events('task');
    assert.equal(replay.filter(event=>event.type==='runtime.completed').length,2);
    assert.deepEqual(await b.events('task'),[]);
    const restored = await b.request('/tasks/task/instructions');
    assert.equal(restored.length,2); assert.ok(restored.every(message=>message.status==='completed'));
    assert.equal(server.queue.next('task'),null);
    const repeatedAfterRestart = await b.request('/tasks/task/approvals/write-once/decision',{method:'POST',data:{action,revision:1,allow:true}});
    assert.equal(repeatedAfterRestart.allowed,false);
    const exported = lab.exportSource('handoff',['fixture.txt','summary.txt']);
    assert.equal(exported.revision,revision);
    const plan = createHandoffPlan({source:manifest(exported),completion:{runtime:observed.status,delivery:restored.at(-1).status,pending:restored.filter(row=>row.status!=='completed').length},approval:{allowed:approval.allowed,consumed:approval.consumed},checks:{source_clean:!lab.status('handoff').dirty,tests_passed:true}});
    const serialized = JSON.stringify(plan);
    for (const prohibited of [tokenA,tokenB,fixture.password,runtimeId,worktree.path,directory]) assert.equal(serialized.includes(prohibited),false);
    checkpoints.push({stage:'reconnected',events_replayed:2,duplicates:0,approval_replay_allowed:false,auto_resume:plan.target.auto_resume});
    return {outcome:'completed_source_handoff',modules_used:[10,11,12,13,14,15,16],source_plan:plan,template_fingerprint:snapshot.fingerprint,selected_memory_count:selected.length,checkpoints,traces:adapter.transport.trace};
  } finally {
    await server?.close(); await fixture?.close();
    const cleaned = lab?.cleanup();
    rmSync(directory,{recursive:true,force:true});
    if (cleaned && !cleaned.removed) throw new Error(`fixture_cleanup_preserved:${cleaned.reason}`);
  }
}

function manifest(exported) {
  return {repository:'fixture://handoff-source',revision:exported.revision,files:exported.files.map(({path,sha256:hash})=>({path,sha256:hash}))};
}
