import {existsSync,lstatSync,mkdirSync,mkdtempSync,readFileSync,readdirSync,realpathSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {basename,dirname,join} from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
import {runGit} from './git.mjs';
import {safeName,safeRelativePath} from './paths.mjs';

const CONSTRUCT=Symbol('owned-temp-lab');
export class TemporaryWorktreeLab{
  #root;#token;#worktrees=new Map();#closed=false;
  constructor(key,root,token){
    if(key!==CONSTRUCT)throw new Error('use_temporary_factory');
    this.#root=root;this.#token=token;
  }

  static create(){
    const root=realpathSync(mkdtempSync(join(tmpdir(),'hands-on-worktrees-')));
    const token=randomUUID();const lab=new TemporaryWorktreeLab(CONSTRUCT,root,token);
    writeFileSync(join(root,'.owner.json'),JSON.stringify({version:1,token}),{mode:0o600,flag:'wx'});
    mkdirSync(join(root,'source'));mkdirSync(join(root,'trees'));
    runGit(lab.source,['init','-b','main']);
    writeFileSync(join(lab.source,'fixture.txt'),'baseline\n');
    runGit(lab.source,['add','--','fixture.txt']);
    runGit(lab.source,['-c','user.name=Hands-on Fixture','-c','user.email=fixture@example.invalid','commit','-m','Initialize synthetic fixture']);
    return lab;
  }

  get root(){return this.#root;}
  get source(){return join(this.#root,'source');}

  #owned(){
    if(this.#closed)throw new Error('lab_closed');
    if(dirname(this.#root)!==realpathSync(tmpdir())||!basename(this.#root).startsWith('hands-on-worktrees-')||lstatSync(this.#root).isSymbolicLink())throw new Error('ownership_mismatch');
    const marker=join(this.#root,'.owner.json');
    if(!existsSync(marker)||lstatSync(marker).isSymbolicLink()||JSON.parse(readFileSync(marker,'utf8')).token!==this.#token)throw new Error('ownership_mismatch');
    if(lstatSync(this.source).isSymbolicLink()||lstatSync(join(this.#root,'trees')).isSymbolicLink())throw new Error('ownership_mismatch');
  }

  #path(name){
    this.#owned();safeName(name);
    const item=this.#worktrees.get(name);
    if(!item)throw new Error('unknown_worktree');
    if(lstatSync(item.path).isSymbolicLink()||realpathSync(item.path)!==item.path)throw new Error('ownership_mismatch');
    return item.path;
  }

  create(name){
    this.#owned();safeName(name);
    if(this.#worktrees.has(name))throw new Error('duplicate_worktree');
    const path=join(this.#root,'trees',name);const branch='codex/lab-'+name;
    if(existsSync(path))throw new Error('occupied_worktree_path');
    runGit(this.source,['worktree','add','-b',branch,path,'main']);
    const record=Object.freeze({name,branch,path});this.#worktrees.set(name,record);return record;
  }

  status(name){
    const path=this.#path(name);
    const entries=runGit(path,['status','--porcelain=v1','-z','--untracked-files=all','--ignored']).split('\0').filter(Boolean);
    return Object.freeze({dirty:entries.length>0,entries:Object.freeze(entries)});
  }

  write(name,relativePath,text){
    const root=this.#path(name);const target=safeRelativePath(root,relativePath);
    if(typeof text!=='string'||Buffer.byteLength(text)>65536)throw new Error('bounded_text_required');
    mkdirSync(dirname(target),{recursive:true});writeFileSync(target,text,{mode:0o600});
  }

  read(name,relativePath){return readFileSync(safeRelativePath(this.#path(name),relativePath),'utf8');}

  commit(name,message){
    const path=this.#path(name);
    if(typeof message!=='string'||!message.trim()||message.length>200)throw new Error('invalid_commit_message');
    runGit(path,['add','--all']);
    runGit(path,['-c','user.name=Hands-on Fixture','-c','user.email=fixture@example.invalid','commit','-m',message]);
    return runGit(path,['rev-parse','HEAD']).trim();
  }

  exportSource(name,allowedPaths=['fixture.txt']){
    const path=this.#path(name);
    if(this.status(name).dirty)throw new Error('dirty_source_export');
    if(!Array.isArray(allowedPaths)||!allowedPaths.length||new Set(allowedPaths).size!==allowedPaths.length)throw new Error('invalid_export_paths');
    const files=allowedPaths.map(relativePath=>{
      safeRelativePath(path,relativePath);
      const mode=runGit(path,['ls-tree','HEAD','--',relativePath]).split(' ')[0];
      if(!['100644','100755'].includes(mode))throw new Error('regular_source_file_required');
      const content=runGit(path,['show','HEAD:'+relativePath]);
      if(Buffer.byteLength(content)>65536)throw new Error('bounded_source_required');
      return Object.freeze({path:relativePath,content,sha256:createHash('sha256').update(content).digest('hex')});
    });
    return Object.freeze({revision:runGit(path,['rev-parse','HEAD']).trim(),branch:this.#worktrees.get(name).branch,files:Object.freeze(files)});
  }

  remove(name){
    const path=this.#path(name);
    if(this.status(name).dirty)return Object.freeze({removed:false,reason:'dirty_worktree'});
    runGit(this.source,['worktree','remove',path]);this.#worktrees.delete(name);
    return Object.freeze({removed:true});
  }

  cleanup(){
    if(this.#closed)return Object.freeze({removed:true});
    this.#owned();
    if(readdirSync(this.#root).some(name=>!['.owner.json','source','trees'].includes(name)))return Object.freeze({removed:false,reason:'unknown_resource'});
    if(readdirSync(join(this.#root,'trees')).some(name=>!this.#worktrees.has(name)))return Object.freeze({removed:false,reason:'unknown_resource'});
    if(runGit(this.source,['status','--porcelain=v1','-z','--untracked-files=all','--ignored']).length)return Object.freeze({removed:false,reason:'dirty_source'});
    if([...this.#worktrees.keys()].some(name=>this.status(name).dirty))return Object.freeze({removed:false,reason:'dirty_worktree'});
    for(const name of [...this.#worktrees.keys()])this.remove(name);
    rmSync(this.#root,{recursive:true});this.#closed=true;return Object.freeze({removed:true});
  }
}
