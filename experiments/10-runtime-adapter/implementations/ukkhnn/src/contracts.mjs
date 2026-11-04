export class ProtocolError extends Error { constructor(message) { super(message); this.name = 'ProtocolError'; } }
export function id(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$/.test(value)) throw new ProtocolError('Invalid runtime identifier');
  return value;
}
export function text(value, max = 20000) {
  if (typeof value !== 'string' || !value.trim() || value.length > max) throw new ProtocolError('Invalid text');
  return value;
}
export function record(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new ProtocolError('Expected object');
  return value;
}
export const CAPABILITIES = Object.freeze({ create: true, send: true, snapshot: true, abort: true, permissions: false, tools: false, memory: false });
export function requireCapabilities(required, capabilities = CAPABILITIES) {
  if (!Array.isArray(required) || required.some(v => typeof v !== 'string')) throw new ProtocolError('Invalid capability request');
  for (const name of required) if (capabilities[name] !== true) throw new ProtocolError(`Unsupported capability: ${name}`);
  return true;
}
