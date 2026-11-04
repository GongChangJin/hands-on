import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { InstructionQueue } from './queue.mjs';

export const scenarios = {
  'empty-task-lifecycle': ({ queue }) => {
    assert.throws(() => queue.list('unknown'), /Unknown task/);
    queue.ensureTask('task'); assert.deepEqual(queue.list('task'), []); assert.equal(queue.next('task'), null);
    queue.stop('task'); assert.equal(queue.status('task').paused, true); queue.resume('task'); assert.equal(queue.status('task').paused, false);
    return 'Explicit task creation permits empty state and controls; reads never create unknown tasks.';
  },
  'idempotent-enqueue': ({ queue }) => {
    const input = { id: 'message-a', text: 'first' };
    assert.deepEqual(queue.enqueue('task-a', input), queue.enqueue('task-a', input));
    assert.equal(queue.list('task-a').length, 1); return 'Retrying the same request ID preserves one instruction.';
  },
  'idempotency-conflict': ({ queue }) => {
    queue.enqueue('task-a', { id: 'message-a', text: 'first' });
    assert.throws(() => queue.enqueue('task-a', { id: 'message-a', text: 'changed' }), /conflict/);
    assert.equal(queue.list('task-a')[0].text, 'first'); return 'A reused ID with different content cannot rewrite intent.';
  },
  'ordered-dispatch': ({ queue }) => {
    for (const id of ['a', 'b']) queue.enqueue('task', { id, text: id });
    assert.equal(queue.next('task').id, 'a'); assert.equal(queue.next('task'), null);
    queue.acknowledge('task', 'a'); assert.equal(queue.next('task').id, 'b'); queue.acknowledge('task', 'b');
    assert.equal(queue.next('task'), null); return 'Only completion of the active instruction permits the next dispatch.';
  },
  'followup-does-not-stop': ({ queue }) => {
    queue.enqueue('task', { id: 'a', text: 'current' }); queue.next('task');
    queue.enqueue('task', { id: 'b', text: 'follow-up' });
    assert.equal(queue.list('task')[0].status, 'sending'); assert.equal(queue.status('task').paused, false);
    return 'A normal follow-up message leaves the active execution intact.';
  },
  'stop-preserves-queue': ({ queue }) => {
    for (const id of ['a', 'b']) queue.enqueue('task', { id, text: id });
    queue.next('task'); const stopped = queue.stop('task');
    assert.deepEqual(stopped.active, ['a']); assert.equal(queue.next('task'), null);
    assert.equal(queue.list('task')[1].status, 'queued');
    queue.acknowledge('task', 'a'); assert.equal(queue.next('task'), null);
    queue.resume('task'); assert.equal(queue.next('task').id, 'b');
    return 'Stop pauses dispatch and preserves pending intent; it does not claim the remote process stopped.';
  },
  'uncertain-no-retry': ({ queue }) => {
    for (const id of ['a', 'b']) queue.enqueue('task', { id, text: id });
    const executed = []; executed.push(queue.next('task').id); queue.markUncertain('task', 'a');
    for (let n = 0; n < 3; n++) assert.equal(queue.next('task'), null);
    assert.throws(() => queue.resume('task'), /Resolve/); assert.deepEqual(executed, ['a']);
    return 'Ambiguous delivery blocks both automatic retries and later instructions.';
  },
  'sending-restart': ({ queue, file }) => {
    for (const id of ['a', 'b']) queue.enqueue('task', { id, text: id });
    queue.next('task'); queue.close();
    const restarted = new InstructionQueue(file);
    try { assert.equal(restarted.list('task')[0].status, 'uncertain'); assert.equal(restarted.next('task'), null); }
    finally { restarted.close(); }
    return 'Recovery converts sending to uncertain before any new dispatch.';
  },
  'completed-restart-process': ({ queue, file }) => {
    for (const id of ['a', 'b']) queue.enqueue('task', { id, text: id });
    queue.next('task'); queue.acknowledge('task', 'a'); queue.close();
    const source = `import {InstructionQueue} from ${JSON.stringify(new URL('./queue.mjs', import.meta.url).href)};const q=new InstructionQueue(process.argv[1]);if(q.next('task').id!=='b')process.exitCode=1;q.acknowledge('task','b');q.close();`;
    const child = spawnSync(process.execPath, ['--input-type=module', '-e', source, file], { encoding: 'utf8', timeout: 5000 });
    assert.equal(child.status, 0, child.stderr);
    const restarted = new InstructionQueue(file);
    try { assert.equal(restarted.next('task'), null); assert.deepEqual(restarted.list('task').map(m => m.status), ['completed', 'completed']); }
    finally { restarted.close(); }
    return 'A new Node process resumes only pending work and never re-dispatches completed work.';
  },
  'explicit-resolution': ({ queue }) => {
    for (const id of ['a', 'b']) queue.enqueue('task', { id, text: id });
    queue.next('task'); queue.markUncertain('task', 'a');
    assert.throws(() => queue.resolve('task', 'a', { outcome: 'completed', evidence: '' }), /evidence/);
    queue.resolve('task', 'a', { outcome: 'completed', evidence: 'Fixture runtime history confirms completion.' });
    assert.equal(queue.next('task'), null); queue.resume('task'); assert.equal(queue.next('task').id, 'b');
    return 'Recorded completion evidence and explicit resume are both needed after uncertainty.';
  },
  'cross-task-acknowledgement': ({ queue }) => {
    queue.enqueue('task-a', { id: 'a', text: 'a' }); queue.enqueue('task-b', { id: 'b', text: 'b' }); queue.next('task-a');
    assert.throws(() => queue.acknowledge('task-b', 'a'), /Unknown/);
    assert.equal(queue.list('task-a')[0].status, 'sending'); return 'Acknowledgement cannot cross task ownership boundaries.';
  },
  'invalid-inputs': ({ queue }) => {
    for (const input of [{ id: '../bad', text: 'a' }, { id: 'a', text: '' }, { id: 'a', text: 'x'.repeat(20001) }]) assert.throws(() => queue.enqueue('task', input));
    assert.throws(() => queue.enqueue('__proto__', { id: 'a', text: 'a' })); return 'Path-like IDs, empty and oversized messages are rejected.';
  },
  'immutable-list': ({ queue }) => {
    queue.enqueue('task', { id: 'a', text: 'original' }); const copy = queue.list('task'); copy[0].text = 'mutated'; copy[0].status = 'completed';
    assert.equal(queue.next('task').text, 'original'); return 'Returned message data cannot bypass durable transitions.';
  },
};

export async function runScenario(name) {
  if (!Object.hasOwn(scenarios, name)) throw new Error('Unknown scenario');
  const directory = mkdtempSync(join(tmpdir(), 'instruction-queue-lab-'));
  const file = join(directory, 'queue.json'); const queue = new InstructionQueue(file);
  try { return await scenarios[name]({ queue, file, directory }); }
  finally { queue.close(); rmSync(directory, { recursive: true, force: true }); }
}
