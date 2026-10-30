#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const repo=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const index=process.argv.indexOf('--output');
const output=index<0?join(repo,'integration/results/workspace-bridge-v1'):resolve(process.argv[index+1]);
const referenceIndex=process.argv.indexOf('--reference-root');
const referenceRoot=referenceIndex<0?null:resolve(process.argv[referenceIndex+1]);
const experiments=readdirSync(join(repo,'experiments')).filter(name=>/^(1[0-7])-/.test(name)).sort();
if(experiments.length!==8) throw new Error('eight_bridge_experiments_required');
mkdirSync(output,{recursive:true});
const results=[];
const childEnv=Object.fromEntries(['PATH','HOME','TMPDIR','LANG','LC_ALL'].filter(key=>process.env[key]).map(key=>[key,process.env[key]]));
for(const experiment of experiments){
  const cwd=join(repo,'experiments',experiment,'implementations/ukkhnn');
  const tests=readdirSync(join(cwd,'tests')).filter(name=>name.endsWith('.test.mjs')).map(name=>join('tests',name));
  const test=spawnSync(process.execPath,['--test',...tests],{cwd,env:childEnv,encoding:'utf8',timeout:120000});
  const destination=join(output,experiment);
  const referenceArgs=experiment.startsWith('17-')&&referenceRoot?['--reference-root',referenceRoot]:[];
  const evaluation=spawnSync(process.execPath,['src/evaluate.mjs','--output',destination,...referenceArgs],{cwd,env:childEnv,encoding:'utf8',timeout:120000});
  let summary=null;
  try{summary=JSON.parse(readFileSync(join(destination,'summary.json'),'utf8'));}catch{}
  const result={experiment,tests_exit:test.status,evaluation_exit:evaluation.status,tests_count:Number(/# tests (\d+)/.exec(test.stdout??'')?.[1]??0),passed:test.status===0&&evaluation.status===0&&summary!==null,summary};
  results.push(result);
  console.log(`${experiment}: tests=${test.status}, evaluation=${evaluation.status}`);
  if(test.status!==0) console.error((test.stderr||test.stdout||'').slice(-3000));
  if(evaluation.status!==0) console.error((evaluation.stderr||evaluation.stdout||'').slice(-3000));
  if(summary===null) console.error(`${experiment}: evaluation summary is missing`);
}
const summary={evaluated_at:new Date().toISOString(),node:process.version,experiments:results.length,passed:results.filter(row=>row.passed).length,tests_count:results.reduce((n,row)=>n+row.tests_count,0),mode:'local_fixture_and_real_io',live_model_calls:0,remote_device_tested:false,results};
writeFileSync(join(output,'summary.json'),JSON.stringify(summary,null,2)+'\n');
writeFileSync(join(output,'report.md'),`# Workspace Bridge 통합 재현\n\n실행 시각: ${summary.evaluated_at}\n\n실험 ${summary.passed}/${summary.experiments}, 자동 테스트 ${summary.tests_count}개.\n\n| 실험 | 테스트 | 평가 |\n|---|---:|---|\n${results.map(row=>`| ${row.experiment} | ${row.tests_count} | ${row.passed?'PASS':'FAIL'} |`).join('\n')}\n\n로컬 HTTP·저장·Git 파일 조작은 실제 실행했다. 모델 응답은 fixture이고 외부 모델 비용은 없다. Mac mini 배포와 실제 다른 기기의 접속은 검증하지 않았다. 제품 연결과 미검증 범위는 docs/personal-ai-learning-path.md 및 17 결과를 참고한다.\n`);
if(summary.passed!==summary.experiments) process.exitCode=1;
