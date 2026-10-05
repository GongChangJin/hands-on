import { ProtocolError } from './contracts.mjs';

const routes = [
  ['GET', /^\/global\/health$/], ['POST', /^\/session$/], ['GET', /^\/session\/status$/],
  ['GET', /^\/session\/[A-Za-z0-9][A-Za-z0-9_-]{0,99}\/message$/],
  ['POST', /^\/session\/[A-Za-z0-9][A-Za-z0-9_-]{0,99}\/(prompt_async|abort)$/],
];

export class LocalTransport {
  #url; #authorization;
  constructor(url, { password, timeoutMs = 1000, maxResponseBytes = 65536 } = {}) {
    const parsed = new URL(url);
    if (parsed.protocol !== 'http:' || parsed.hostname !== '127.0.0.1' || !parsed.port || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) throw new ProtocolError('Only literal IPv4 loopback origins are allowed');
    if (typeof password !== 'string' || !password || password.length > 512) throw new ProtocolError('A fixture password is required');
    if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000 || !Number.isInteger(maxResponseBytes) || maxResponseBytes < 128 || maxResponseBytes > 1048576) throw new ProtocolError('Invalid transport bounds');
    this.#url = parsed; this.#authorization = `Basic ${Buffer.from(`opencode:${password}`).toString('base64')}`;
    this.timeoutMs = timeoutMs; this.maxResponseBytes = maxResponseBytes; this.trace = [];
  }
  async request(method, path, body) {
    if (typeof path !== 'string' || !routes.some(([m, re]) => m === method && re.test(path))) throw new ProtocolError('Endpoint is not allowlisted');
    if (method === 'GET' && body !== undefined) throw new ProtocolError('GET body is not supported');
    const serialized = body === undefined ? undefined : JSON.stringify(body);
    if (serialized && Buffer.byteLength(serialized) > 65536) throw new ProtocolError('Request too large');
    const start = performance.now(); let status = null, outcome = 'failed';
    try {
      const response = await fetch(new URL(path, this.#url), {
        method, body: serialized, redirect: 'error', signal: AbortSignal.timeout(this.timeoutMs),
        headers: { authorization: this.#authorization, 'content-type': 'application/json' },
      });
      status = response.status;
      if (!response.ok) { await response.body?.cancel(); throw new ProtocolError(`Runtime HTTP ${status}`); }
      if (response.status === 204) {
        if (!path.endsWith('/prompt_async')) throw new ProtocolError('Unexpected empty response');
        outcome = 'accepted'; return null;
      }
      if (path.endsWith('/prompt_async')) { await response.body?.cancel(); throw new ProtocolError('Async prompt must return 204'); }
      if (!(response.headers.get('content-type') || '').startsWith('application/json')) { await response.body?.cancel(); throw new ProtocolError('Expected JSON content type'); }
      const chunks = []; let bytes = 0;
      for await (const chunk of response.body) {
        bytes += chunk.length;
        if (bytes > this.maxResponseBytes) throw new ProtocolError('Response too large');
        chunks.push(chunk);
      }
      let data;
      try { data = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
      catch { throw new ProtocolError('Malformed JSON response'); }
      outcome = 'received'; return data;
    } catch (error) {
      if (error instanceof ProtocolError) throw error;
      throw new ProtocolError(error.name === 'TimeoutError' || error.name === 'AbortError' ? 'Runtime timeout; delivery may be uncertain' : 'Runtime transport failed; delivery may be uncertain');
    } finally {
      // No bodies, URLs, headers, model output, or credentials enter this trace.
      this.trace.push({ method, operation: path.replace(/\/session\/[^/]+\//, '/session/:id/'), status, outcome, durationMs: Math.round((performance.now() - start) * 1000) / 1000 });
    }
  }
}
