import { readFileSync, writeFileSync, mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { performance } from 'node:perf_hooks';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ApprovalLedger } from './approvals.mjs';

const fixtures=JSON.parse(readFileSync(new URL('../../../shared/scenarios.json',import.meta.url),'utf8'));
const args=process.argv.slice(2);
if(args.length&&(args.length!==2||args[0]!=='--output'||!args[1]))throw new Error('Usage: node src/evaluate.mjs [--output DIRECTORY]');
const output=args.length?resolve(args[1]):fileURLToPath(new URL('../results/',import.meta.url));
const dir=mkdtempSync(join(tmpdir(),'approval-evaluation-'));
const executedAt=new Date().toISOString(); const records=[];
try {
  for (const scenario of fixtures) {
    const started=performance.now(); const now=Date.now();
    const ledger=new ApprovalLedger(join(dir,scenario.id+'.json'));
    const request={id:'request',taskId:'task-a',ownerId:'alice',action:{tool:'save_note',arguments:{body:'fixture'}},revision:1,expiresAt:now+60000};
    ledger.request(request);
    const decision={...request,now,allow:true};
    if(scenario.change==='owner') decision.ownerId='bob';
    if(scenario.change==='task') decision.taskId='task-b';
    if(scenario.change==='action') decision.action={tool:'delete_note'};
    if(scenario.change==='revision') decision.revision=0;
    if(scenario.change==='expiry') decision.now=request.expiresAt;
    if(scenario.change==='reuse') ledger.decide('request',decision);
    if(scenario.change==='reject') decision.allow=false;
    if(scenario.change==='invalid') decision.allow='yes';
    if(scenario.change==='supersede') ledger.request({...request,id:'new-request',revision:2});
    const actual=new ApprovalLedger(join(dir,scenario.id+'.json')).decide('request',decision);
    records.push({task_id:scenario.id,implementation_id:'ukkhnn:13:approval-boundary',task_success:actual.reason===scenario.expected&&actual.allowed===scenario.allowed,
      latency_ms:performance.now()-started,safety_violations:actual.allowed&&!scenario.allowed?['unauthorized_approval']:[],
      metadata:{executed_at:executedAt,expected:scenario.expected,actual:actual.reason,allowed:actual.allowed}});
  }
} finally { rmSync(dir,{recursive:true,force:true}); }
mkdirSync(output,{recursive:true});
const summary={executed_at:executedAt,mode:'local-deterministic',node:process.version,scenarios:records.length,passed:records.filter(r=>r.task_success).length,
  safety_violations:records.flatMap(r=>r.safety_violations).length,limitations:['Trusted caller supplies owner and time; no authentication server.','Single-use authorization is consumed before an external effect; it does not guarantee exactly-once effects.','Crash-left lock requires manual recovery; no multi-host durability claim.']};
writeFileSync(join(output,'records.jsonl'),records.map(r=>JSON.stringify(r)).join('\n')+'\n');
writeFileSync(join(output,'summary.json'),JSON.stringify(summary,null,2)+'\n');
writeFileSync(join(output,'report.md'),`# Approval boundary 결과\n\n실행 시각: ${executedAt}\n\n- 통과: ${summary.passed}/${summary.scenarios}\n- 승인 경계 위반: ${summary.safety_violations}\n- 조건이 다른 요청과 재사용을 차단하고 재시작 후에도 승인 상태를 유지했다.\n- 외부 효과는 실행하지 않았다. 승인 소비 이후 crash가 나면 재승인이 필요하므로 정확히 한 번 실행 보장은 아니다.\n- 적용 판단: 인증된 서버 경계 안에서 제한적 trial.\n`);
console.log(JSON.stringify(summary,null,2));
if(summary.passed!==summary.scenarios||summary.safety_violations)process.exitCode=1;
