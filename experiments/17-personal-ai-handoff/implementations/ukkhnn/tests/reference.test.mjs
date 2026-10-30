import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { TemporaryWorktreeLab } from '../../../../15-worktree-isolation/implementations/ukkhnn/src/worktrees.mjs';
import { runGit } from '../../../../15-worktree-isolation/implementations/ukkhnn/src/git.mjs';
import { verifyReferenceFiles, reference } from '../src/reference.mjs';
import { sha256 } from '../src/plan.mjs';

test('reference verifier pins a real Git revision and file hashes without running the application',()=>{
  const lab=TemporaryWorktreeLab.create();
  try{
    const pinned={schema_version:1,revision:runGit(lab.source,['rev-parse','HEAD']).trim(),files:[{path:'fixture.txt',sha256:sha256(readFileSync(join(lab.source,'fixture.txt')))}]};
    assert.deepEqual(verifyReferenceFiles(lab.source,pinned),{status:'verified_read_only',revision:pinned.revision,files_verified:1,application_executed:false});
    assert.throws(()=>verifyReferenceFiles(lab.source,{...pinned,revision:'b'.repeat(40)}),/reference_revision_changed/);
    assert.throws(()=>verifyReferenceFiles(lab.source,{...pinned,files:[{path:'fixture.txt',sha256:'b'.repeat(64)}]}),/reference_digest_changed/);
  }finally{assert.equal(lab.cleanup().removed,true);}
});
test('product reference explicitly preserves implemented and pending scope',()=>{
  assert.equal(reference.application_executed,false);
  assert.equal(reference.live_model_calls,0);
  assert.ok(reference.mappings.some(item=>item.id==='git-automation'&&item.status==='planned'));
  assert.ok(reference.mappings.some(item=>item.id==='harness-memory'&&item.status==='partial'));
  const files=new Set(reference.files.map(item=>item.path));
  assert.ok(reference.mappings.every(item=>item.evidence.every(path=>files.has(path))));
});
test('reference verification rejects empty, malformed, duplicated and private file pins before reading disk',()=>{
  const pinned={schema_version:1,revision:'a'.repeat(40),files:[]};
  assert.throws(()=>verifyReferenceFiles('/not-read',pinned),/source_files_required/);
  pinned.files=[{path:'README.md',sha256:'b'.repeat(64)}];
  assert.throws(()=>verifyReferenceFiles('/not-read',{...pinned,revision:['a'.repeat(40)]}),/invalid_source_revision/);
  assert.throws(()=>verifyReferenceFiles('/not-read',{...pinned,files:[{path:'README.md',sha256:['b'.repeat(64)]}]}),/invalid_source_digest/);
  assert.throws(()=>verifyReferenceFiles('/not-read',{...pinned,files:[...pinned.files,...pinned.files]}),/invalid_source_digest/);
  assert.throws(()=>verifyReferenceFiles('/not-read',{...pinned,files:[{path:'state/workspace.json',sha256:'b'.repeat(64)}]}),/unsafe_source_path/);
  assert.throws(()=>verifyReferenceFiles('/not-read',{...pinned,files:[{...pinned.files[0],auth:'unexpected'}]}),/source_file_unknown_or_missing_field/);
});
