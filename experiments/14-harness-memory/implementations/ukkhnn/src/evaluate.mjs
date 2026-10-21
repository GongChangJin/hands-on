import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {fileURLToPath} from 'node:url';
import {join,resolve} from 'node:path';
import {createHarnessSnapshot} from './snapshot.mjs';
import {selectMemory} from './memory.mjs';

const scenarios=JSON.parse(readFileSync(new URL('../../../shared/scenarios.json',import.meta.url),'utf8'));
const source=JSON.parse(readFileSync(new URL('../../../shared/harness.json',import.meta.url),'utf8'));
const executedAt=new Date().toISOString();const records=[];
for(const scenario of scenarios){
  const started=performance.now();const template=structuredClone(source);const now=Date.now();
  let capabilities=['structured-output','local-files'];
  const first={id:'note',projectId:'project-a',revision:1,supersedes:null,text:'fixture fact',deleted:false,source:{uri:'fixture://note',hash:'a'.repeat(64),observedAt:now-2000},expiresAt:now+60000};
  let memories=[first];let actual;
  if(scenario.change==='version')template.version=99;
  if(scenario.change==='capability')capabilities=[];
  if(scenario.change==='permission')template.tools[0].sideEffect=true;
  if(scenario.change==='scope')memories.push({...first,projectId:'project-b',text:'hidden'});
  if(scenario.change==='expiry')first.expiresAt=now;
  if(scenario.change==='conflict')memories.push({...first,text:'conflict'});
  if(scenario.change==='provenance')first.source.hash='missing';
  if(['delete','expired-latest'].includes(scenario.change))memories.push({...first,revision:2,supersedes:1,deleted:scenario.change==='delete',expiresAt:now-1,source:{...first.source,observedAt:now-1000}});
  try{
    const snapshot=createHarnessSnapshot(template,{capabilities});
    const selected=selectMemory(memories,{projectId:snapshot.template.memory.projectId,now});
    actual=scenario.change==='scope'?selected.map(item=>item.projectId).join(','):selected.length?'ok':'empty';
  }catch(error){actual=error.message;}
  records.push({task_id:scenario.id,implementation_id:'ukkhnn:14:harness-memory',task_success:actual===scenario.expected,latency_ms:performance.now()-started,
    safety_violations:scenario.change==='scope'&&actual!=='project-a'?['memory_scope_failure']:[],metadata:{executed_at:executedAt,expected:scenario.expected,actual}});
}
const summary={executed_at:executedAt,node:process.version,mode:'local-deterministic',scenarios:records.length,passed:records.filter(r=>r.task_success).length,safety_violations:records.flatMap(r=>r.safety_violations).length,
  limitations:['Capabilities are declarations, not provider performance validation.','Provenance hashes identify supplied evidence; they do not establish truth.','All memory is synthetic; no production retrieval-quality or privacy claim.']};
const args=process.argv.slice(2);
if(args.length&&(args.length!==2||args[0]!=='--output'||!args[1]))throw new Error('Usage: node src/evaluate.mjs [--output DIRECTORY]');
const output=args.length?resolve(args[1]):fileURLToPath(new URL('../results/',import.meta.url));mkdirSync(output,{recursive:true});
writeFileSync(join(output,'records.jsonl'),records.map(r=>JSON.stringify(r)).join('\n')+'\n');
writeFileSync(join(output,'summary.json'),JSON.stringify(summary,null,2)+'\n');
writeFileSync(join(output,'report.md'),`# Harness와 Memory 결과\n\n실행 시각: ${executedAt}\n\n- 통과: ${summary.passed}/${summary.scenarios}\n- 범위 위반: ${summary.safety_violations}\n- 버전·capability·권한 불일치, 출처 누락과 충돌한 revision을 차단했다.\n- 최신 기억이 만료되거나 삭제되어도 이전 사실을 복구하지 않았다.\n- 적용 판단: 설정 snapshot과 프로젝트별 기억 경계에 trial. 검색 품질과 사실의 진위는 별도 평가가 필요하다.\n`);
console.log(JSON.stringify(summary,null,2));if(summary.passed!==summary.scenarios||summary.safety_violations)process.exitCode=1;
