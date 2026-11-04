import test from 'node:test';
import assert from 'node:assert/strict';
import {symlinkSync,linkSync,unlinkSync,readFileSync,writeFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {TemporaryWorktreeLab} from '../src/worktrees.mjs';
import {safeName} from '../src/paths.mjs';

test('only bounded single-component worktree names are accepted',()=>{
  for(const name of ['../x','/tmp/x','--force','a/b','a b','main','source','a'.repeat(40),'x\n'])assert.throws(()=>safeName(name));
  assert.equal(safeName('task-123'),'task-123');
});
test('caller cannot adopt or clean an arbitrary repository',()=>{
  assert.throws(()=>new TemporaryWorktreeLab(null,'/tmp/foreign','x'),/factory/);
});
test('path traversal and Git metadata changes are denied',t=>{
  const lab=TemporaryWorktreeLab.create();t.after(()=>assert.equal(lab.cleanup().removed,true));lab.create('safe');
  for(const path of ['../source/fixture.txt','/tmp/escaped','.git/config','folder/../../x','x\\y','folder/.GIT/config','a\0b']){
    assert.throws(()=>lab.write('safe',path,'unsafe'));
  }
  assert.equal(lab.read('safe','fixture.txt'),'baseline\n');assert.equal(lab.status('safe').dirty,false);
});
test('symlink path cannot escape the owned worktree',t=>{
  const lab=TemporaryWorktreeLab.create();t.after(()=>assert.equal(lab.cleanup().removed,true));const tree=lab.create('safe');
  const link=join(tree.path,'link');symlinkSync(lab.source,link);
  try{assert.throws(()=>lab.write('safe','link/fixture.txt','escape'),/symlink/);}
  finally{unlinkSync(link);}
  assert.equal(readFileSync(join(lab.source,'fixture.txt'),'utf8'),'baseline\n');
});
test('marker tampering fails closed and does not remove the resource',t=>{
  const lab=TemporaryWorktreeLab.create();t.after(()=>assert.equal(lab.cleanup().removed,true));
  const marker=join(lab.root,'.owner.json');const original=readFileSync(marker,'utf8');
  writeFileSync(marker,JSON.stringify({token:'different-owner'}));
  try{assert.throws(()=>lab.cleanup(),/ownership_mismatch/);assert.equal(readFileSync(marker,'utf8'),'{"token":"different-owner"}');}
  finally{writeFileSync(marker,original);}
});
test('dangling symlinks and hardlinks cannot redirect a write',t=>{
  const lab=TemporaryWorktreeLab.create();t.after(()=>assert.equal(lab.cleanup().removed,true));const tree=lab.create('safe');
  const dangling=join(tree.path,'dangling');const outside=join(lab.source,'not-created.txt');
  symlinkSync(outside,dangling);
  try{assert.throws(()=>lab.write('safe','dangling','escape'),/symlink/);assert.equal(existsSync(outside),false);}
  finally{unlinkSync(dangling);}
  const hard=join(tree.path,'hard');linkSync(join(lab.source,'fixture.txt'),hard);
  try{assert.throws(()=>lab.write('safe','hard','escape'),/hardlink/);assert.equal(readFileSync(join(lab.source,'fixture.txt'),'utf8'),'baseline\n');}
  finally{unlinkSync(hard);}
});
