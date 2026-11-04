import {lstatSync,realpathSync} from 'node:fs';
import {isAbsolute,join,relative,sep} from 'node:path';

export function safeName(name){
  if(typeof name!=='string'||!/^[a-z][a-z0-9-]{0,31}$/.test(name)||['main','source','trees'].includes(name))throw new Error('unsafe_worktree_name');
  return name;
}

export function safeRelativePath(root,value){
  if(typeof value!=='string'||!value||value.includes('\\')||value.includes('\0')||isAbsolute(value))throw new Error('unsafe_relative_path');
  const parts=value.split('/');
  if(parts.some(part=>!part||part==='.'||part==='..'||part.toLowerCase()==='.git'))throw new Error('unsafe_relative_path');
  const canonicalRoot=realpathSync(root);let current=canonicalRoot;
  for(const part of parts){
    current=join(current,part);
    let stat;
    try{stat=lstatSync(current);}catch(error){if(error.code!=='ENOENT')throw error;}
    if(stat?.isSymbolicLink())throw new Error('symlink_path');
    if(stat?.isFile()&&stat.nlink>1)throw new Error('hardlink_path');
  }
  const rel=relative(canonicalRoot,current);
  if(rel==='..'||rel.startsWith('..'+sep)||isAbsolute(rel))throw new Error('outside_worktree');
  return current;
}
