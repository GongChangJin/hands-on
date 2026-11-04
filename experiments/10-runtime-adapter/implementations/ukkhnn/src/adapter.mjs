import { CAPABILITIES, requireCapabilities, id, text, record, ProtocolError } from './contracts.mjs';
import { LocalTransport } from './transport.mjs';

export class RuntimeAdapter {
  constructor(url, options) { this.transport = new LocalTransport(url, options); this.capabilities = CAPABILITIES; }
  require(features) { return requireCapabilities(features, this.capabilities); }
  async health() {
    const health = record(await this.transport.request('GET', '/global/health'));
    if (health.healthy !== true || typeof health.version !== 'string' || !health.version) throw new ProtocolError('Invalid health response');
    return { healthy: true, version: health.version };
  }
  async create(title) {
    this.require(['create']); text(title, 160);
    const session = record(await this.transport.request('POST', '/session', { title }));
    return { runtimeId: id(session.id) };
  }
  async send(runtimeId, message) {
    this.require(['send']); id(runtimeId); record(message); id(message.id); text(message.text);
    await this.transport.request('POST', `/session/${runtimeId}/prompt_async`, { messageID: message.id, parts: [{ type: 'text', text: message.text }] });
    return { accepted: true, completed: false };
  }
  async snapshot(runtimeId) {
    this.require(['snapshot']); id(runtimeId);
    const [rawMessages, rawStates] = await Promise.all([
      this.transport.request('GET', `/session/${runtimeId}/message`),
      this.transport.request('GET', '/session/status'),
    ]);
    record(rawStates);
    if (!Array.isArray(rawMessages)) throw new ProtocolError('Invalid message list');
    const messages = rawMessages.map(raw => {
      record(raw); const info = record(raw.info); id(info.id);
      if (info.sessionID !== runtimeId || !['user', 'assistant'].includes(info.role) || !Array.isArray(raw.parts)) throw new ProtocolError('Message identity mismatch');
      for (const part of raw.parts) {
        record(part);
        if (typeof part.type !== 'string' || (part.type === 'text' && typeof part.text !== 'string')) throw new ProtocolError('Invalid message part');
      }
      return { id: info.id, role: info.role, text: raw.parts.filter(p => p.type === 'text').map(p => p.text).join('\n'), completed: Number.isFinite(info.time?.completed) };
    });
    const state = Object.hasOwn(rawStates, runtimeId) ? record(rawStates[runtimeId]).type : 'idle';
    if (!['idle', 'busy', 'retry'].includes(state)) throw new ProtocolError('Unknown runtime state');
    return { runtimeId, status: { idle: 'idle', busy: 'running', retry: 'retrying' }[state], messages };
  }
  async abort(runtimeId) {
    this.require(['abort']); id(runtimeId);
    if (await this.transport.request('POST', `/session/${runtimeId}/abort`, {}) !== true) throw new ProtocolError('Abort was not confirmed');
    return { requested: true }; // A subsequent snapshot must verify idle.
  }
}
