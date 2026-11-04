import {spawnSync} from 'node:child_process';

// Never use a shell or inherit GIT_DIR/GIT_WORK_TREE/global signing or hooks.
export function runGit(directory,args){
  const result=spawnSync('git',['-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false',...args],{
    cwd:directory,encoding:'utf8',timeout:15000,maxBuffer:2*1024*1024,
    env:{PATH:process.env.PATH,LANG:'C',LC_ALL:'C',GIT_CONFIG_NOSYSTEM:'1',GIT_CONFIG_GLOBAL:'/dev/null',GIT_TERMINAL_PROMPT:'0'},
  });
  if(result.error)throw new Error(`git_execution_failed:${result.error.code}`);
  if(result.status!==0)throw new Error(`git_command_failed:${args[0]}:${result.status}`);
  return result.stdout;
}
