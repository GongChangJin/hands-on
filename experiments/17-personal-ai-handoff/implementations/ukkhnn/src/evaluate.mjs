import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { evaluateScenarios } from './scenarios.mjs';
import { reference, verifyReferenceFiles } from './reference.mjs';

const implementation=resolve(dirname(fileURLToPath(import.meta.url)),'..');
function option(name){const at=process.argv.indexOf(name);if(at<0)return undefined;if(!process.argv[at+1]||process.argv[at+1].startsWith('--'))throw new Error('missing_option_value');return process.argv[at+1];}
const output=resolve(option('--output')??join(implementation,'results'));
const referenceRoot=option('--reference-root');
const referenceCheck=referenceRoot?verifyReferenceFiles(referenceRoot):{status:'not_rechecked',revision:reference.revision,files_verified:0,application_executed:false};
const evaluatedAt=new Date().toISOString();
const cases=JSON.parse(readFileSync(new URL('../../../shared/scenarios.json',import.meta.url),'utf8'));
const results=await evaluateScenarios();
if(JSON.stringify(cases.map(item=>[item.id,item.expected]))!==JSON.stringify(results.map(item=>[item.id,item.expected])))throw new Error('scenario_manifest_drift');
const limitations=[
  'Only synthetic local HTTP and temporary real Git worktrees were executed; no model or personal-ai application was run.',
  'The coordinator writes fixed fixture content. This is not an AI coding-quality evaluation.',
  'Memory is project-scoped synthetic text inserted by the coordinator; the protocol adapter does not support native memory.',
  'Independent module stores and Git operations are not one transaction and do not guarantee exactly-once external effects.',
  'Restart restores the coordinator records while the fixture runtime remains running; host/process migration is not verified.',
  'Restart tests close stores cleanly; automatic stale-lock recovery after an abrupt process kill is not implemented.',
  'Source-only plans contain hashes and allowlisted names, not credentials, active sessions or an executable migration.',
  'Mac mini, mobile, HTTPS/Tailscale, production backup/restore and automatic Git lifecycle remain unverified.',
];
const evaluations=results.map(result=>({
  task_id:result.id,implementation_id:'ukkhnn:17:personal-ai-handoff',task_success:result.passed,latency_ms:result.latency_ms,
  cost:0,safety_violations:result.passed?[]:['expected_contract_not_observed'],failure_type:result.passed?null:'assertion_failed',
  metadata:{evaluated_at:evaluatedAt,expected:result.expected,observed:result.observed,scope:cases.find(item=>item.id===result.id).scope},
}));
const requests=results.map(result=>({
  task_id:result.id,task_type:'integration',input:{scenario:result.id,mode:'synthetic_local_composition'},
  constraints:{allowed_tools:['loopback_http_fixture','temporary_git_worktree','local_state_store'],forbidden_actions:['live_model_call','external_push','personal_ai_write','credential_export','automatic_session_resume'],max_steps:100,max_tool_calls:100},
  expected_output:{outcome:result.expected},metadata:{learning_slot:'2026-10-30',retrospective:true,evaluated_at:evaluatedAt},
}));
const agents=results.map(result=>({
  task_id:result.id,status:result.passed?'success':'failed',output:{observed:result.observed,checkpoints:result.checkpoints},
  evidence:[{source:'records.jsonl',location:result.id,claim:`Observed ${result.observed}; expected ${result.expected}.`}],
  actions:result.modules_used?['compose_experiments_10_to_16','verify_local_state_and_source_contract']:['validate_source_only_contract'],
  limitations,metadata:{product_readiness:'partial',evaluated_at:evaluatedAt},
}));
const traces=results.flatMap(result=>result.traces.map(row=>({
  task_id:result.id,tool_name:'loopback_runtime_http',input_summary:`${row.method} ${row.operation}`,
  result_summary:`${row.outcome}; HTTP ${row.status??'unknown'}`,duration_ms:row.durationMs,
  error:row.outcome==='failed'?'transport_failure':null,metadata:{synthetic:true,evaluated_at:evaluatedAt},
})));
const latencies=evaluations.map(row=>row.latency_ms).sort((a,b)=>a-b);
const summary={
  experiment:'17-personal-ai-handoff',learning_slot:'2026-10-30',retrospective:true,evaluated_at:evaluatedAt,node:process.version,
  mode:'composed_local_http_and_real_temporary_git',scenarios:evaluations.length,passed:evaluations.filter(row=>row.task_success).length,
  safety_violations:evaluations.flatMap(row=>row.safety_violations).length,live_model_calls:0,cost_usd:0,product_readiness:'partial',
  personal_ai_reference:referenceCheck,remote_device_tested:false,application_executed:false,
  latency_p50_ms:latencies[Math.ceil(latencies.length*.5)-1],latency_p95_ms:latencies[Math.ceil(latencies.length*.95)-1],limitations,
};
mkdirSync(output,{recursive:true});
const jsonl=(name,rows)=>writeFileSync(join(output,name),rows.map(row=>JSON.stringify(row)).join('\n')+'\n');
jsonl('records.jsonl',evaluations);jsonl('task-requests.jsonl',requests);jsonl('agent-results.jsonl',agents);jsonl('tool-traces.jsonl',traces);
jsonl('checkpoints.jsonl',results.filter(result=>result.checkpoints.length).map(({id,checkpoints})=>({task_id:id,checkpoints,evaluated_at:evaluatedAt})));
writeFileSync(join(output,'summary.json'),JSON.stringify(summary,null,2)+'\n');
const completed=results.find(row=>row.id==='completed-restart-handoff'&&row.passed);
if(completed)writeFileSync(join(output,'handoff-plan.json'),JSON.stringify(completed.source_plan,null,2)+'\n');
else rmSync(join(output,'handoff-plan.json'),{force:true});
writeFileSync(join(output,'report.md'),`# Personal AI Handoff 결과\n\n학습 슬롯: 2026-10-30 (회고 구성). 실제 실행: ${evaluatedAt}.\n\n로컬 합성·경계 평가 **${summary.passed}/${summary.scenarios}**. 실제 모델 호출 0회, 비용 0. personal-ai 소스 기준점: \`${reference.revision}\`; 재확인 상태: \`${referenceCheck.status}\` (${referenceCheck.files_verified}개 파일). 제품 앱을 실행한 결과가 아니다.\n\n## 합성한 흐름\n\n인증한 두 클라이언트 → 저장된 작업·지시 → 작업별 1회 승인 → 프로젝트 범위의 템플릿·기억 → 런타임 HTTP 접수 → 임시 Git worktree의 고정된 fixture 변경·커밋 → 완료 snapshot → 중앙 서비스 재시작·커서 재접속 → 소스 전용 인계 계획.\n\n접수 직후 실행 완료로 표시하지 않았다. 같은 지시는 한 번만 대기열에 들어갔고, 추가 지시는 실행 중단을 유발하지 않았다. 승인 재사용은 재시작 후에도 거부했다. 재시작 전에 전송 중이던 지시는 불확실 상태로 남겨 자동 재전송·인계를 막았다. 중단 요청 이후 런타임 idle 확인을 별도로 수행했고 대기 지시는 보존했다.\n\n## 사례\n\n| 사례 | 관찰 | 결과 |\n|---|---|---|\n${results.map(row=>`| ${row.id} | ${row.observed} | ${row.passed?'PASS':'FAIL'} |`).join('\n')}\n\n## 적용 판단\n\n**trial / 제품 준비 상태 partial**. 10–16의 작은 계약이 함께 동작한다는 근거는 확보했다. personal-ai에 가져갈 것은 모듈 경계·복구 원칙·실패 사례다. 임시 source manifest는 현재 서비스의 살아 있는 세션을 Mac mini로 이전하는 기능이 아니다. 실제 기기 접속, 장기 운영, 여섯 하네스 설정 전체와 자동 Git 흐름은 별도로 마무리해야 한다.\n\n## 한계\n\n${limitations.map(item=>'- '+item).join('\n')}\n`);
console.log(JSON.stringify(summary,null,2));
if(summary.passed!==summary.scenarios||summary.safety_violations)process.exitCode=1;
