import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ApprovalLedger } from '../src/approvals.mjs';

function setup(t) {
  const dir = mkdtempSync(join(tmpdir(), 'approval-test-'));
  t.after(() => rmSync(dir, { recursive:true, force:true }));
  const file = join(dir, 'ledger.json');
  const ledger = new ApprovalLedger(file);
  const request = { id:'a1', taskId:'task-a', ownerId:'alice', action:{tool:'save_note', arguments:{body:'draft'}}, revision:1, expiresAt:2000 };
  ledger.request(request);
  return { ledger, file, request, decision:{...request, now:1000, allow:true} };
}

test('approved request is consumed across process-style reopen', t => {
  const { ledger, file, decision } = setup(t);
  assert.equal(ledger.decide('a1', decision).allowed, true);
  assert.equal(new ApprovalLedger(file).decide('a1', decision).reason, 'already_consumed');
  assert.equal(new ApprovalLedger(file).list('task-a')[0].consumed, true);
});

test('caller and returned snapshot mutation cannot change pending action', t => {
  const { ledger, request, decision } = setup(t);
  request.action.arguments.body = 'secret';
  assert.throws(() => { ledger.list('task-a')[0].action.arguments.body = 'other'; }, TypeError);
  assert.equal(ledger.decide('a1', decision).reason, 'action_changed');
  assert.equal(ledger.list('task-a')[0].action.arguments.body, 'draft');
});

for (const [name, change, reason] of [
  ['cross owner',{ownerId:'bob'},'scope_mismatch'],
  ['cross task',{taskId:'task-b'},'scope_mismatch'],
  ['changed action',{action:{tool:'delete_note'}},'action_changed'],
  ['stale revision',{revision:0},'stale_revision'],
  ['expiry boundary',{now:2000},'expired'],
  ['non boolean allow',{allow:'true'},'invalid_allow'],
]) test(name, t => {
  const { ledger, decision } = setup(t);
  const result = ledger.decide('a1', {...decision,...change});
  assert.equal(result.allowed, false);
  assert.equal(result.reason, reason);
  assert.equal(ledger.list('task-a')[0].consumed, false);
});

test('a higher revision supersedes pending approvals and rejects new stale requests', t => {
  const { ledger, request, decision } = setup(t);
  ledger.request({...request,id:'a2',revision:2});
  assert.equal(ledger.decide('a1',decision).reason,'superseded');
  assert.throws(() => ledger.request({...request,id:'a3'}), /stale_revision/);
  assert.equal(ledger.list('task-a').length,2);
});

test('rejection is terminal while a scope mismatch does not consume owner approval', t => {
  const {ledger,decision}=setup(t);
  ledger.decide('a1',{...decision,ownerId:'mallory'});
  assert.equal(ledger.decide('a1',{...decision,allow:false}).reason,'user_rejected');
  assert.equal(ledger.decide('a1',decision).reason,'rejected');
  assert.deepEqual(ledger.list('task-b'),[]);
});

test('duplicate IDs and corrupted ledger fail without authorizing', t => {
  const {ledger,file,request,decision}=setup(t);
  assert.throws(() => ledger.request(request),/duplicate/);
  writeFileSync(file,'{"version":1,"requests":[{}]}');
  assert.throws(() => ledger.decide('a1',decision));
});
