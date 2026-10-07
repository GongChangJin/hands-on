import test from 'node:test';
import assert from 'node:assert/strict';
import { project } from '../src/projection.mjs';
const event = (type, payload = {}) => ({ type, payload });
test('unknown event and impossible completion do not silently resume work', () => {
  assert.throws(() => project([event('future.event')]), /Unsupported/);
  assert.throws(() => project([event('instruction.completed', { id: 'missing' })]), /Invalid/);
});
test('persisted resume cannot override unresolved delivery', () => {
  assert.throws(() => project([
    event('instruction.queued', { id: 'a', text: 'a' }), event('instruction.sending', { id: 'a' }),
    event('instruction.uncertain', { id: 'a' }), event('queue.resumed'),
  ]), /Unresolved/);
});
