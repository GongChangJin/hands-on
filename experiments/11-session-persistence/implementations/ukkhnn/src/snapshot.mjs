import { createHash } from 'node:crypto';
import { identifier, payload, cursor, object } from './validation.mjs';

export function validateState(data) {
  object(data, 'state');
  if (data.version !== 1 || !Array.isArray(data.tasks) || !Array.isArray(data.events)) throw new Error('Unsupported snapshot schema');
  if (data.tasks.length > 1000 || data.events.length > 10000) throw new Error('Snapshot capacity exceeded');
  const ids = new Set();
  for (const task of data.tasks) {
    object(task, 'task'); identifier(task.id); identifier(task.projectId, 'projectId'); identifier(task.ownerId, 'ownerId');
    if (ids.has(task.id)) throw new Error('Duplicate task identity'); ids.add(task.id);
  }
  for (const [index, event] of data.events.entries()) {
    object(event, 'event'); identifier(event.taskId); identifier(event.type, 'type'); payload(event.payload);
    if (event.seq !== index + 1 || !ids.has(event.taskId)) throw new Error('Broken event sequence or task reference');
  }
  cursor(data.nextSeq);
  if (data.nextSeq !== data.events.length + 1) throw new Error('Broken next cursor');
  return data;
}

export function encode(data) {
  validateState(data);
  const serialized = JSON.stringify(data);
  return JSON.stringify({ checksum: createHash('sha256').update(serialized).digest('hex'), data }, null, 2) + '\n';
}

export function decode(text) {
  if (Buffer.byteLength(text) > 10 * 1024 * 1024) throw new Error('Snapshot too large');
  const envelope = JSON.parse(text); object(envelope, 'snapshot');
  const checksum = createHash('sha256').update(JSON.stringify(envelope.data) ?? '').digest('hex');
  if (checksum !== envelope.checksum) throw new Error('Snapshot checksum mismatch');
  return validateState(envelope.data);
}
