import { createHash } from 'node:crypto';

// Reject values JSON silently drops or coerces before hashing or saving them.
export function canonical(value, seen = new Set()) {
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
  if (typeof value === 'number' && Number.isFinite(value)) return JSON.stringify(value);
  if (typeof value !== 'object' || seen.has(value)) throw new TypeError('action_must_be_finite_json');
  if (!Array.isArray(value) && Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null) {
    throw new TypeError('action_must_be_plain_json');
  }
  if (Reflect.ownKeys(value).some(key => typeof key === 'symbol')) throw new TypeError('symbol_key');
  seen.add(value);
  let result;
  if (Array.isArray(value)) {
    if (Object.keys(value).length !== value.length) throw new TypeError('sparse_or_decorated_array');
    result = '[' + value.map(item => canonical(item, seen)).join(',') + ']';
  } else {
    const keys = Object.keys(value).sort();
    if (keys.some(key => !('value' in Object.getOwnPropertyDescriptor(value, key)))) throw new TypeError('accessor_not_json');
    result = '{' + keys.map(key => JSON.stringify(key) + ':' + canonical(value[key], seen)).join(',') + '}';
  }
  seen.delete(value);
  return result;
}

export function fingerprint(action) {
  if (!action || typeof action !== 'object' || Array.isArray(action) || !Object.keys(action).length) {
    throw new TypeError('action_object_required');
  }
  return createHash('sha256').update(canonical(action)).digest('hex');
}

export function immutable(value) {
  const clone = JSON.parse(canonical(value));
  const freeze = item => {
    if (item && typeof item === 'object') {
      Object.values(item).forEach(freeze);
      Object.freeze(item);
    }
    return item;
  };
  return freeze(clone);
}

export function nonempty(value, name) {
  if (typeof value !== 'string' || !value.trim() || value.length > 256) throw new TypeError(`invalid_${name}`);
  return value;
}

export function epoch(value, name) {
  if (!Number.isSafeInteger(value) || value <= 0) throw new TypeError(`invalid_${name}`);
  return value;
}
