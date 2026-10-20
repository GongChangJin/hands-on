import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fingerprint } from '../src/fingerprint.mjs';
import { ApprovalLedger } from '../src/approvals.mjs';

test('canonical fingerprints ignore object order but preserve values and array order', () => {
  assert.equal(fingerprint({b:2,a:1}),fingerprint({a:1,b:2}));
  assert.notEqual(fingerprint({a:[1,2]}),fingerprint({a:[2,1]}));
});
test('lossy JSON, getters and cycles are rejected before persistence', () => {
  const cycle={}; cycle.self=cycle;
  for (const value of [{a:undefined},{a:NaN},{a:Infinity},{a:1n},{a:new Date()},cycle,{a:[,1]}]) {
    assert.throws(() => fingerprint(value));
  }
  assert.throws(() => fingerprint({get a(){throw new Error('getter ran');}}), /accessor_not_json/);
});
test('exclusive lock fails closed without replacing an existing state', t => {
  const dir=mkdtempSync(join(tmpdir(),'approval-lock-'));
  t.after(()=>rmSync(dir,{recursive:true,force:true}));
  const file=join(dir,'ledger.json'); const ledger=new ApprovalLedger(file);
  const req={id:'a',taskId:'t',ownerId:'o',action:{tool:'save'},revision:1,expiresAt:5000};
  ledger.request(req); const original=readFileSync(file,'utf8');
  writeFileSync(file+'.lock','owned elsewhere');
  assert.throws(()=>ledger.decide('a',{...req,now:1000,allow:true}),/ledger_busy/);
  assert.equal(readFileSync(file,'utf8'),original);
});
