export function identifier(value, label = 'id') {
  if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$/.test(value)) throw new Error(`Invalid ${label}`);
  return value;
}

export function object(value, label = 'object') {
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.getPrototypeOf(value) !== Object.prototype) throw new Error(`Invalid ${label}`);
  return value;
}

export function jsonValue(value, depth = 0) {
  if (depth > 20) throw new Error('Payload too deep');
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return;
  if (typeof value === 'number' && Number.isFinite(value)) return;
  if (Array.isArray(value)) { for (const child of value) jsonValue(child, depth + 1); return; }
  object(value, 'JSON value');
  for (const [key, child] of Object.entries(value)) {
    if (['__proto__', 'constructor', 'prototype'].includes(key)) throw new Error('Unsafe payload key');
    jsonValue(child, depth + 1);
  }
}

export function payload(value) {
  object(value, 'payload'); jsonValue(value);
  if (Buffer.byteLength(JSON.stringify(value)) > 65536) throw new Error('Payload too large');
  return structuredClone(value);
}

export function cursor(value) {
  if (!Number.isSafeInteger(value) || value < 0) throw new Error('Invalid cursor');
  return value;
}
