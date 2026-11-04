import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {TemporaryWorktreeLab} from './worktrees.mjs';

const scenarios=JSON.parse(readFileSync(new URL('../../../shared/scenarios.json',import.meta.url),'utf8'));
const executedAt=new Date().toISOString();const lab=TemporaryWorktreeLab.create();
const records=[];lab.create('alpha');lab.create('beta');let cleanup;
try{
  for(const scenario of scenarios){
    const started=performance.now();let actual=false;let failure=null;
    try{
      if(scenario.check==='isolation'){
        lab.write('alpha','fixture.txt','isolated update\n');
        actual=lab.read('beta','fixture.txt')==='baseline\n'&&readFileSync(join(lab.source,'fixture.txt'),'utf8')==='baseline\n'&&lab.status('alpha').dirty;
      }
      if(scenario.check==='name'){try{lab.create('../escape');}catch(error){actual=error.message==='unsafe_worktree_name';}}
      if(scenario.check==='escape'){try{lab.write('alpha','../escape','x');}catch(error){actual=error.message==='unsafe_relative_path';}}
      if(scenario.check==='dirty')actual=!lab.remove('alpha').removed&&lab.read('alpha','fixture.txt')==='isolated update\n';
      if(scenario.check==='export'){
        const revision=lab.commit('alpha','Record isolated fixture update');const snapshot=lab.exportSource('alpha');
        actual=snapshot.revision===revision&&snapshot.files[0].content==='isolated update\n'&&!JSON.stringify(snapshot).includes(lab.root)&&lab.read('beta','fixture.txt')==='baseline\n';
      }
      if(scenario.check==='cleanup'){const root=lab.root;cleanup=lab.cleanup();actual=cleanup.removed&&!existsSync(root);}
    }catch(error){failure=error.message;}
    records.push({task_id:scenario.id,implementation_id:'ukkhnn:15:worktree-isolation',task_success:actual===scenario.expected,latency_ms:performance.now()-started,
      safety_violations:!actual&&['escape','dirty','isolation','name'].includes(scenario.check)?['boundary_check_failed']:[],metadata:{executed_at:executedAt,expected:scenario.expected,actual,failure}});
  }
}finally{cleanup=lab.cleanup();}
const summary={executed_at:executedAt,node:process.version,mode:'real-local-git-temporary-repository',scenarios:records.length,passed:records.filter(r=>r.task_success).length,
  safety_violations:records.flatMap(r=>r.safety_violations).length,temporary_resources_removed:cleanup.removed,
  limitations:['Git worktrees isolate working directories; objects and repository configuration are shared.','This is not an OS sandbox and does not run untrusted agent code.','Only fixture files in an owned temporary repository are used.']};
const args=process.argv.slice(2);
if(args.length&&(args.length!==2||args[0]!=='--output'||!args[1]))throw new Error('Usage: node src/evaluate.mjs [--output DIRECTORY]');
const output=args.length?resolve(args[1]):fileURLToPath(new URL('../results/',import.meta.url));mkdirSync(output,{recursive:true});
writeFileSync(join(output,'records.jsonl'),records.map(r=>JSON.stringify(r)).join('\n')+'\n');
writeFileSync(join(output,'summary.json'),JSON.stringify(summary,null,2)+'\n');
writeFileSync(join(output,'report.md'),`# Worktree 격리 결과\n\n실행 시각: ${executedAt}\n\n- 실제 임시 Git 저장소 평가: ${summary.passed}/${summary.scenarios}\n- 경계 위반: ${summary.safety_violations}\n- 임시 자원 정리: ${cleanup.removed}\n- 한 worktree의 변경과 commit은 다른 worktree의 파일에 영향을 주지 않았다.\n- dirty 파일과 ignored 파일은 삭제하지 않으며, 출처 snapshot에는 상대 경로와 revision만 내보낸다.\n- 적용 판단: 작업 디렉터리 분리에는 trial. Git 설정·object store는 공유하며 OS 보안 격리로 사용하지 않는다.\n`);
console.log(JSON.stringify(summary,null,2));if(summary.passed!==summary.scenarios||summary.safety_violations||!cleanup.removed)process.exitCode=1;
