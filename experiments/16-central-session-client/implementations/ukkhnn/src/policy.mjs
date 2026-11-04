import { timingSafeEqual } from 'node:crypto';

export class HttpError extends Error {
  constructor(status, code) { super(code); this.status = status; this.code = code; }
}

export function identity(req, tokens, origin) {
  if (req.headers.host !== new URL(origin).host) throw new HttpError(403, 'host_denied');
  if (req.headers.origin && req.headers.origin !== origin) throw new HttpError(403, 'origin_denied');
  const authorization = req.headers.authorization ?? '';
  const presented = Buffer.from(authorization.startsWith('Bearer ') ? authorization.slice(7) : '');
  for (const [token, owner] of tokens) {
    const expected = Buffer.from(token);
    if (presented.length === expected.length && timingSafeEqual(presented, expected)) return owner;
  }
  throw new HttpError(401, 'authentication_required');
}

export function requireTask(store, taskId, ownerId) {
  let task;
  try { task = store.getTask(taskId); } catch { throw new HttpError(404, 'task_not_found'); }
  if (!task || task.ownerId !== ownerId) throw new HttpError(404, 'task_not_found');
  return task;
}

export function object(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new HttpError(400, 'object_required');
  return value;
}

export function fields(value, allowed) {
  object(value);
  if (Object.keys(value).some(key => !allowed.includes(key))) throw new HttpError(400, 'unknown_field');
  return value;
}

export function id(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(value)) throw new HttpError(400, 'invalid_id');
  return value;
}

export function cursor(value) {
  if (value === null) return 0;
  if (!/^(0|[1-9][0-9]*)$/.test(value)) throw new HttpError(400, 'invalid_cursor');
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) throw new HttpError(400, 'invalid_cursor');
  return parsed;
}
