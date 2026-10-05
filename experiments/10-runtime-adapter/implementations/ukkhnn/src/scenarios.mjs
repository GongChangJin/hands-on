import assert from 'node:assert/strict';
import { RuntimeAdapter } from './adapter.mjs';
import { startFixture } from './fixture.mjs';

export const scenarios = {
  'lifecycle-http': async ({ fixture, adapter }) => {
    assert.equal((await adapter.health()).healthy, true);
    const { runtimeId } = await adapter.create('bounded coding task');
    assert.deepEqual(await adapter.send(runtimeId, { id: 'msg_1', text: 'fixture instruction' }), { accepted: true, completed: false });
    assert.equal((await adapter.snapshot(runtimeId)).status, 'running'); fixture.complete(runtimeId);
    const result = await adapter.snapshot(runtimeId); assert.equal(result.status, 'idle'); assert.equal(result.messages.at(-1).completed, true);
    return 'Real localhost HTTP carries create, asynchronous acceptance and later completion evidence.';
  },
  'abort-confirmation': async ({ adapter }) => {
    const { runtimeId } = await adapter.create('abort test'); await adapter.send(runtimeId, { id: 'msg_1', text: 'work' });
    assert.deepEqual(await adapter.abort(runtimeId), { requested: true }); assert.equal((await adapter.snapshot(runtimeId)).status, 'idle');
    return 'Abort acknowledgement is followed by an independent idle snapshot.';
  },
  'unsupported-capability': async ({ fixture, adapter }) => {
    assert.throws(() => adapter.require(['permissions']), /Unsupported/); assert.throws(() => adapter.require(['memory']), /Unsupported/);
    assert.equal(fixture.requests.length, 0); return 'Unsupported features fail before transport or credentials are used.';
  },
  'endpoint-allowlist': async ({ fixture, adapter }) => {
    for (const path of ['/config', '/auth/provider', '/session/../config', '/session/status?directory=other']) await assert.rejects(adapter.transport.request('GET', path), /allowlisted/);
    assert.equal(fixture.requests.length, 0); return 'Configuration, credentials and arbitrary proxy requests never reach the fixture.';
  },
  'destination-boundary': async ({ fixture }) => {
    for (const url of ['http://example.com:4096', 'http://localhost:4096', 'http://user:pass@127.0.0.1:4096', `${fixture.url}/config`, `${fixture.url}/?x=1`]) assert.throws(() => new RuntimeAdapter(url, { password: fixture.password }), /loopback/);
    return 'Only an explicit literal loopback origin is accepted.';
  },
  'malformed-json': async ({ fixture, adapter }) => {
    fixture.fault('/global/health', 'malformed'); await assert.rejects(adapter.health(), /Malformed JSON/);
    return 'Broken JSON is a protocol failure, not an empty successful result.';
  },
  'schema-guard': async ({ fixture, adapter }) => {
    fixture.fault('/global/health', 'schema'); await assert.rejects(adapter.health(), /Invalid health/);
    return 'Healthy as a string fails the response guard.';
  },
  'bounded-response': async ({ fixture, adapter }) => {
    fixture.fault('/global/health', 'oversized'); await assert.rejects(adapter.health(), /too large/);
    return 'Response body consumption stops at the configured byte budget.';
  },
  'timeout-no-retry': async ({ fixture }) => {
    fixture.fault('/global/health', 'timeout'); const bounded = new RuntimeAdapter(fixture.url, { password: fixture.password, timeoutMs: 30 });
    await assert.rejects(bounded.health(), /timeout/); assert.equal(fixture.requests.length, 1);
    return 'Timeout returns an explicit uncertain transport failure and performs no retry.';
  },
  'redirect-no-follow': async ({ fixture, adapter }) => {
    fixture.fault('/global/health', 'redirect'); await assert.rejects(adapter.health(), /transport failed/);
    assert.equal(fixture.requests.length, 1); return 'Redirects cannot forward fixture credentials to another route.';
  },
  'foreign-session-response': async ({ fixture, adapter }) => {
    const { runtimeId } = await adapter.create('identity test'); fixture.fault(`/session/${runtimeId}/message`, 'foreign');
    await assert.rejects(adapter.snapshot(runtimeId), /identity mismatch/); return 'A response carrying another session ID fails closed.';
  },
  'unknown-runtime-state': async ({ fixture, adapter }) => {
    const { runtimeId } = await adapter.create('state test'); fixture.fault('/session/status', 'unknown-state');
    await assert.rejects(adapter.snapshot(runtimeId), /Unknown runtime state/); return 'Unrecognized runtime state is never treated as idle or completed.';
  },
};

export async function runScenario(name) {
  if (!Object.hasOwn(scenarios, name)) throw new Error('Unknown scenario');
  const fixture = await startFixture(); const adapter = new RuntimeAdapter(fixture.url, { password: fixture.password });
  try { return await scenarios[name]({ fixture, adapter }); }
  finally { await fixture.close(); }
}
