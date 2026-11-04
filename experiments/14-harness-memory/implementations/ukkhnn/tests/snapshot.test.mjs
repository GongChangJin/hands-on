import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHarnessSnapshot} from '../src/snapshot.mjs';
const template=()=>JSON.parse(readFileSync(new URL('../../../shared/harness.json',import.meta.url),'utf8'));
const options={capabilities:['structured-output','local-files']};

test('six-field snapshot is detached and recursively immutable',()=>{
  const source=template();const snapshot=createHarnessSnapshot(source,options);
  source.model.id='changed';source.permissions.allowedTools.push('delete');
  assert.equal(snapshot.template.model.id,'fixture-model');
  assert.throws(()=>snapshot.template.permissions.allowedTools.push('delete'),TypeError);
  assert.equal(createHarnessSnapshot(template(),options).fingerprint,snapshot.fingerprint);
});
for(const [name,mutate,expected]of[
  ['unsupported version',t=>t.version=2,/unsupported/],
  ['missing field',t=>delete t.memory,/six_fields/],
  ['extra field',t=>t.unreviewed='x',/six_fields/],
  ['unavailable model',t=>t.model.requiredCapabilities=['vision'],/missing_model/],
  ['unavailable skill',t=>t.skills[0].requiredCapabilities=['remote'],/missing_skill/],
  ['unknown allowed tool',t=>t.permissions.allowedTools=['delete'],/unconfigured/],
  ['write without permission',t=>t.tools[0].sideEffect=true,/write_permission/],
  ['duplicate tools',t=>t.tools.push(t.tools[0]),/duplicate_tool/],
])test(name,()=>{const source=template();mutate(source);assert.throws(()=>createHarnessSnapshot(source,options),expected);});
test('lossy config values cannot disappear during snapshot creation',()=>{
  const source=template();source.permissions.extra=undefined;
  assert.throws(()=>createHarnessSnapshot(source,options),/finite_json/);
});
