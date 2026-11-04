import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';

// A bounded HTTP protocol fixture, not OpenCode and not a model simulator.
export async function startFixture() {
  const password = `fixture-${randomUUID()}`;
  const expected = `Basic ${Buffer.from(`opencode:${password}`).toString('base64')}`;
  const sessions = new Map(), faults = new Map(), requests = [];
  const server = createServer(async (req, res) => {
    const json = (status, value) => { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(value)); };
    try {
      const path = new URL(req.url, 'http://127.0.0.1').pathname;
      requests.push({ method: req.method, path });
      if (req.headers.authorization !== expected) return json(401, { error: 'unauthorized' });
      const fault = faults.get(path);
      if (fault === 'malformed') { res.writeHead(200, { 'content-type': 'application/json' }); return res.end('{broken'); }
      if (fault === 'oversized') return json(200, { text: 'x'.repeat(70000) });
      if (fault === 'redirect') { res.writeHead(302, { location: '/config' }); return res.end(); }
      if (fault === 'timeout') { const timer = setTimeout(() => json(504, {}), 500); res.on('close', () => clearTimeout(timer)); return; }
      if (fault === 'schema') return json(200, { healthy: 'yes' });
      if (fault === 'foreign') return json(200, [{ info: { id: 'm_foreign', sessionID: 'foreign', role: 'user' }, parts: [] }]);
      if (fault === 'unknown-state') return json(200, Object.fromEntries([...sessions.keys()].map(id => [id, { type: 'mystery' }])));
      if (path === '/global/health' && req.method === 'GET') return json(200, { healthy: true, version: 'fixture-v1' });
      if (path === '/session/status' && req.method === 'GET') return json(200, Object.fromEntries([...sessions].map(([id, s]) => [id, { type: s.status }])));
      let body = '';
      for await (const chunk of req) { body += chunk; if (body.length > 65536) return json(413, {}); }
      const input = body ? JSON.parse(body) : {};
      if (path === '/session' && req.method === 'POST') {
        const id = `ses_${sessions.size + 1}`;
        sessions.set(id, { status: 'idle', messages: [] }); return json(200, { id, title: input.title });
      }
      const match = path.match(/^\/session\/([^/]+)\/(message|prompt_async|abort)$/);
      if (!match || !sessions.has(match[1])) return json(404, { error: 'not-found' });
      const [_, id, action] = match, session = sessions.get(id);
      if (action === 'message' && req.method === 'GET') return json(200, session.messages);
      if (action === 'prompt_async' && req.method === 'POST') {
        session.status = 'busy';
        session.messages.push({ info: { id: input.messageID, sessionID: id, role: 'user' }, parts: input.parts });
        res.writeHead(204); return res.end();
      }
      if (action === 'abort' && req.method === 'POST') { session.status = 'idle'; return json(200, true); }
      return json(405, {});
    } catch { if (!res.headersSent) json(400, { error: 'invalid-fixture-request' }); else res.end(); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  return {
    url: `http://127.0.0.1:${server.address().port}`, password, requests,
    fault(path, kind) { faults.set(path, kind); },
    complete(runtimeId, text = 'fixture result') {
      const session = sessions.get(runtimeId); session.status = 'idle';
      session.messages.push({ info: { id: `reply_${session.messages.length}`, sessionID: runtimeId, role: 'assistant', time: { completed: Date.now() } }, parts: [{ type: 'text', text }] });
    },
    close: () => new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }),
  };
}
