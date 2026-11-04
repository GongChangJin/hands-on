import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, readFileSync, writeFileSync, statSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { SessionStore } from './store.mjs';
import { atomicWrite } from './atomic.mjs';
import { encode } from './snapshot.mjs';

export const scenarios = {
  'task-identity': ({ store }) => {
    const task = { id: 'task-a', projectId: 'project-a', ownerId: 'owner-a' };
    assert.deepEqual(store.createTask(task), task); assert.deepEqual(store.createTask(task), task);
    assert.throws(() => store.createTask({ ...task, ownerId: 'owner-b' }), /identity conflict/);
    assert.equal(store.listTasks().length, 1);
    return 'Repeated creation preserves identity; another owner is rejected.';
  },
  'immutable-reads': ({ store }) => {
    store.createTask({ id: 'task-a', projectId: 'project-a', ownerId: 'owner-a' });
    store.getTask('task-a').ownerId = 'intruder';
    const input = { value: { nested: 1 } };
    store.appendEvent('task-a', { type: 'message.accepted', payload: input }); input.value.nested = 9;
    store.events('task-a')[0].payload.value.nested = 8;
    assert.equal(store.getTask('task-a').ownerId, 'owner-a'); assert.equal(store.events('task-a')[0].payload.value.nested, 1);
    return 'Input and returned payload mutation cannot alter persisted state.';
  },
  'monotonic-cursors': ({ store }) => {
    for (const id of ['task-a', 'task-b']) store.createTask({ id, projectId: 'project', ownerId: 'owner' });
    for (const taskId of ['task-a', 'task-b', 'task-a']) store.appendEvent(taskId, { type: 'progress', payload: {} });
    assert.deepEqual(store.events('task-a').map(e => e.seq), [1, 3]); assert.deepEqual(store.events('task-a', 1).map(e => e.seq), [3]);
    assert.throws(() => store.events('task-a', -1), /cursor/); return 'Global cursor is monotonic while task queries preserve isolation.';
  },
  'restart-process': ({ store, file }) => {
    store.createTask({ id: 'task-a', projectId: 'project', ownerId: 'owner' });
    store.appendEvent('task-a', { type: 'started', payload: { phase: 1 } }); store.close();
    const source = `import {SessionStore} from ${JSON.stringify(new URL('./store.mjs', import.meta.url).href)}; const s=new SessionStore(process.argv[1]);s.appendEvent('task-a',{type:'resumed',payload:{phase:2}});s.close();`;
    const child = spawnSync(process.execPath, ['--input-type=module', '-e', source, file], { encoding: 'utf8', timeout: 5000 });
    assert.equal(child.status, 0, child.stderr);
    const restarted = new SessionStore(file);
    try { assert.deepEqual(restarted.events('task-a').map(e => e.seq), [1, 2]); } finally { restarted.close(); }
    return 'A separate Node process appends after restart without resetting cursors.';
  },
  'malformed-json': ({ store, file }) => {
    store.close(); writeFileSync(file, '{broken');
    assert.throws(() => new SessionStore(file)); assert.equal(readFileSync(file, 'utf8'), '{broken');
    return 'Corrupted JSON is refused and original bytes remain available for recovery.';
  },
  'checksum-corruption': ({ store, file }) => {
    store.createTask({ id: 'task-a', projectId: 'project', ownerId: 'owner' }); store.close();
    const envelope = JSON.parse(readFileSync(file, 'utf8')); envelope.data.tasks[0].ownerId = 'changed';
    writeFileSync(file, JSON.stringify(envelope)); assert.throws(() => new SessionStore(file), /checksum/);
    return 'Valid JSON with an accidentally changed owner fails its checksum.';
  },
  'unknown-schema': ({ store, file }) => {
    store.close(); assert.throws(() => encode({ version: 99, tasks: [], events: [], nextSeq: 1 }), /schema/);
    assert.equal(JSON.parse(readFileSync(file, 'utf8')).data.version, 1); return 'Unsupported schemas are rejected rather than guessed or overwritten.';
  },
  'invalid-payload': ({ store }) => {
    store.createTask({ id: 'task-a', projectId: 'project', ownerId: 'owner' });
    for (const value of [{ number: NaN }, { fn() {} }, JSON.parse('{"__proto__":{}}'), { huge: 'x'.repeat(70000) }]) assert.throws(() => store.appendEvent('task-a', { type: 'data', payload: value }));
    assert.equal(store.events('task-a').length, 0); return 'Non-JSON, oversized and prototype-like payloads produce no events.';
  },
  'writer-lock': ({ store, file }) => {
    assert.throws(() => new SessionStore(file), /EEXIST/); store.close();
    const next = new SessionStore(file); next.close(); return 'Concurrent writer is refused; orderly close releases ownership.';
  },
  'atomic-failure': ({ store, file, directory }) => {
    const before = readFileSync(file, 'utf8');
    assert.throws(() => atomicWrite(file, 'bad replacement', { beforeRename() { throw new Error('injected write failure'); } }), /injected/);
    assert.equal(readFileSync(file, 'utf8'), before); assert.equal(readdirSync(directory).some(name => name.endsWith('.tmp')), false);
    return 'Failure before rename leaves the committed snapshot intact and cleans the temporary file.';
  },
  'private-files': ({ file }) => {
    assert.equal(statSync(file).mode & 0o777, 0o600); assert.equal(statSync(`${file}.lock`).mode & 0o777, 0o600);
    return 'Snapshot and writer-lock files are owner-readable/writable only.';
  },
  'unknown-task': ({ store }) => {
    assert.throws(() => store.appendEvent('missing', { type: 'data', payload: {} }), /Unknown task/);
    assert.throws(() => store.createTask({ id: '../escape', projectId: 'p', ownerId: 'o' }), /Invalid/);
    assert.equal(store.listTasks().length, 0); return 'Unknown task and path-like identities are rejected before mutation.';
  },
};

export async function runScenario(name) {
  if (!Object.hasOwn(scenarios, name)) throw new Error('Unknown scenario');
  const directory = mkdtempSync(join(tmpdir(), 'session-store-lab-'));
  const file = join(directory, 'state.json'); const store = new SessionStore(file);
  try { return await scenarios[name]({ directory, file, store }); }
  finally { store.close(); rmSync(directory, { recursive: true, force: true }); }
}
