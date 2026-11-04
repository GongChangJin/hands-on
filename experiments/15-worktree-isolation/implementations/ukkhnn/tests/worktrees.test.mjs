import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync,writeFileSync,unlinkSync} from 'node:fs';
import {join} from 'node:path';
import {TemporaryWorktreeLab} from '../src/worktrees.mjs';

function setup(t){const lab=TemporaryWorktreeLab.create();t.after(()=>assert.equal(lab.cleanup().removed,true));return lab;}

test('two actual Git worktrees isolate working files and committed branches',t=>{
  const lab=setup(t);const alpha=lab.create('alpha');const beta=lab.create('beta');
  assert.notEqual(alpha.branch,beta.branch);lab.write('alpha','fixture.txt','alpha change\n');
  assert.equal(lab.read('beta','fixture.txt'),'baseline\n');
  assert.equal(readFileSync(join(lab.source,'fixture.txt'),'utf8'),'baseline\n');
  assert.equal(lab.status('alpha').dirty,true);assert.equal(lab.status('beta').dirty,false);
  const revision=lab.commit('alpha','Apply isolated change');assert.match(revision,/^[0-9a-f]{40,64}$/);
  assert.equal(lab.exportSource('alpha').files[0].content,'alpha change\n');
  assert.equal(lab.read('beta','fixture.txt'),'baseline\n');
});

test('dirty removal and whole-lab cleanup preserve files',t=>{
  const lab=setup(t);lab.create('dirty');lab.write('dirty','notes/new.txt','retain me\n');
  assert.deepEqual(lab.remove('dirty'),{removed:false,reason:'dirty_worktree'});
  assert.deepEqual(lab.cleanup(),{removed:false,reason:'dirty_worktree'});
  assert.equal(lab.read('dirty','notes/new.txt'),'retain me\n');
  assert.throws(()=>lab.exportSource('dirty'),/dirty_source_export/);
  lab.commit('dirty','Retain synthetic dirty example');
});

test('ignored files also prevent cleanup',t=>{
  const lab=setup(t);const tree=lab.create('ignored');
  lab.write('ignored','.gitignore','ignored.txt\n');lab.commit('ignored','Add fixture ignore rule');
  lab.write('ignored','ignored.txt','untracked but valuable');
  assert.equal(lab.cleanup().reason,'dirty_worktree');
  assert.equal(lab.read('ignored','ignored.txt'),'untracked but valuable');
  unlinkSync(join(tree.path,'ignored.txt'));
});

test('cleanup removes only factory-owned clean resources and is idempotent',()=>{
  const lab=TemporaryWorktreeLab.create();lab.create('clean');const root=lab.root;
  assert.deepEqual(lab.cleanup(),{removed:true});assert.equal(existsSync(root),false);
  assert.deepEqual(lab.cleanup(),{removed:true});assert.throws(()=>lab.create('late'),/closed/);
});

test('unknown resources are preserved for review',t=>{
  const lab=setup(t);const path=join(lab.root,'unknown.txt');writeFileSync(path,'retain');
  assert.equal(lab.cleanup().reason,'unknown_resource');assert.equal(readFileSync(path,'utf8'),'retain');unlinkSync(path);
});

test('source-only export contains no absolute runtime directory',t=>{
  const lab=setup(t);lab.create('export');const snapshot=lab.exportSource('export');
  assert.deepEqual(Object.keys(snapshot).sort(),['branch','files','revision']);
  assert.equal(JSON.stringify(snapshot).includes(lab.root),false);
  assert.throws(()=>snapshot.files.push({path:'outside'}),TypeError);
});
