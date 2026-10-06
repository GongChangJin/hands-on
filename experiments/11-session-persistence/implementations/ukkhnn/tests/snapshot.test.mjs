import test from 'node:test';
import assert from 'node:assert/strict';
import { encode, decode } from '../src/snapshot.mjs';

test('even checksummed data cannot skip sequence numbers or reference missing tasks', () => {
  for (const event of [{ seq: 2, taskId: 'a', type: 'data', payload: {} }, { seq: 1, taskId: 'missing', type: 'data', payload: {} }]) {
    assert.throws(() => encode({ version: 1, tasks: [{ id: 'a', projectId: 'p', ownerId: 'o' }], events: [event], nextSeq: 2 }), /sequence/);
  }
});
test('roundtrip preserves nulls and unicode without exposing mutable references', () => {
  const state = { version: 1, tasks: [{ id: 'a', projectId: 'p', ownerId: 'o' }], events: [{ seq: 1, taskId: 'a', type: 'data', payload: { text: '다음 지시', none: null } }], nextSeq: 2 };
  assert.deepEqual(decode(encode(state)), state);
});
