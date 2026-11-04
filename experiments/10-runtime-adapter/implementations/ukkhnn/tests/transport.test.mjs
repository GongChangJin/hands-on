import test from 'node:test';
import assert from 'node:assert/strict';
import { startFixture } from '../src/fixture.mjs';
import { RuntimeAdapter } from '../src/adapter.mjs';

test('trace excludes password and message text while invalid IDs never hit HTTP', async () => {
  const fixture = await startFixture();
  try {
    const adapter = new RuntimeAdapter(fixture.url, { password: fixture.password });
    const { runtimeId } = await adapter.create('task'); const count = fixture.requests.length;
    await assert.rejects(adapter.send('../config', { id: 'safe', text: 'private text' }), /identifier/);
    assert.equal(fixture.requests.length, count);
    await adapter.send(runtimeId, { id: 'safe', text: 'private text' });
    const trace = JSON.stringify(adapter.transport.trace);
    assert.equal(trace.includes(fixture.password), false); assert.equal(trace.includes('private text'), false);
  } finally { await fixture.close(); }
});
test('wrong authentication is a bounded failure without response-body disclosure', async () => {
  const fixture = await startFixture();
  try { await assert.rejects(new RuntimeAdapter(fixture.url, { password: 'wrong-fixture-password' }).health(), /HTTP 401/); }
  finally { await fixture.close(); }
});
