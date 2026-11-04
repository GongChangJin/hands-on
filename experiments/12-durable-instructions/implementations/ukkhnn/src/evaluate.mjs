import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve, join } from 'node:path';
import { scenarios, runScenario } from './scenarios.mjs';

const specification = JSON.parse(readFileSync(new URL('../../../shared/scenarios.json', import.meta.url), 'utf8'));
if (JSON.stringify(specification.cases.map(c => c.id).sort()) !== JSON.stringify(Object.keys(scenarios).sort())) throw new Error('Scenario catalog does not match executable cases');
const args = process.argv.slice(2);
if (args.length && (args.length !== 2 || !['--out', '--output'].includes(args[0]))) throw new Error('Usage: node src/evaluate.mjs [--output DIRECTORY]');
const output = args.length ? resolve(args[1]) : fileURLToPath(new URL('../results/', import.meta.url));
const executedAt = new Date().toISOString();
const records = [];
for (const scenario of specification.cases) {
  const start = performance.now(); let observed, passed = false;
  try { observed = await runScenario(scenario.id); passed = true; }
  catch (error) { observed = `Evaluation failed (${error.name}); rerun npm test for local diagnostic details.`; }
  records.push({ scenario: scenario.id, passed, expected: scenario.expected, observed, durationMs: Number((performance.now() - start).toFixed(3)), executedAt, evidenceMode: specification.evidenceMode });
}
const timings = records.map(r => r.durationMs).sort((a,b) => a-b);
const summary = {
  experiment: specification.experiment, learningSlot: specification.learningSlot, executedAt,
  provenance: 'Retrospective learning sequence; executedAt is the actual evaluation time, not the learning slot.',
  evidenceMode: specification.evidenceMode, scope: specification.scope, runtime: process.version,
  total: records.length, passed: records.filter(r => r.passed).length, failed: records.filter(r => !r.passed).length,
  p50Ms: timings[Math.ceil(timings.length * 0.5) - 1], p95Ms: timings[Math.ceil(timings.length * 0.95) - 1],
  apiCostUsd: 0, externalModelCalls: 0,
};
mkdirSync(output, { recursive: true });
writeFileSync(join(output, 'records.jsonl'), records.map(r => JSON.stringify(r)).join('\n') + '\n');
writeFileSync(join(output, 'summary.json'), JSON.stringify(summary, null, 2) + '\n');
const report = [
  `# ${summary.experiment} 실행 결과`, '',
  `- 실제 평가 시각: ${executedAt}`, `- 재구성 학습 슬롯: ${summary.learningSlot} (실행일 주장 아님)`,
  `- 결과: ${summary.passed}/${summary.total}, 실패 ${summary.failed}`, `- 실행 환경: ${process.version}`,
  `- 범위: ${summary.scope}`, `- 외부 모델 호출: 0, API 비용: $0`, '',
  '| 시나리오 | 결과 | 직접 확인한 동작 |', '|---|---|---|',
  ...records.map(r => `| ${r.scenario} | ${r.passed ? 'PASS' : 'FAIL'} | ${r.observed} |`), '',
  '## 판단과 한계', '',
  '제한된 로컬 실행 경계의 trial 근거다. 기대한 차단도 검증 성공에 포함된다. 모델 품질, 실제 OpenCode 버전 호환성, Mac mini 운영, 다중 기기 실사용, 전원 장애 복구 완료를 뜻하지 않는다.',
  '실패는 숨기거나 pass로 대체하지 않는다. 원시 상태는 운영체제 임시 폴더에 만들고 정리하며, 기록에는 사용자 경로·메시지·인증정보를 넣지 않는다.', '',
];
writeFileSync(join(output, 'report.md'), report.join('\n'));
console.log(JSON.stringify(summary, null, 2));
if (summary.failed) process.exitCode = 1;
