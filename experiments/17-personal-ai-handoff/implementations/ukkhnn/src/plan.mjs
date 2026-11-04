import { createHash } from 'node:crypto';

const HANDOFF_STEPS = Object.freeze([
  'fetch-source', 'verify-revision-and-file-hashes', 'prepare-host-with-local-auth',
  'create-new-project-and-task', 'run-local-checks', 'request-first-execution',
]);
const fail = reason => { throw new Error(reason); };
function exact(value, names, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(`${label}_object_required`);
  if (Object.keys(value).sort().join(',') !== [...names].sort().join(',')) fail(`${label}_unknown_or_missing_field`);
}
function literal(value, expected, label) { if (value !== expected) fail(label); }

export function sourcePath(path) {
  if (typeof path !== 'string' || path.length > 240 || !/^[A-Za-z0-9_][A-Za-z0-9_./-]*$/.test(path)
    || path.split('/').some(segment => !segment || segment === '.' || segment === '..' || segment.startsWith('.'))
    || /(?:^|\/)(?:auth|credentials?|secrets?|tokens?|access[-_]code)(?:[./_-]|$)/i.test(path)
    || path.split('/').slice(0,-1).some(segment=>/^(?:runtime|state|sessions?)$/i.test(segment))
    || /(?:^|\/)(?:runtime|state|sessions?|workspace)\.(?:jsonl?|db|sqlite3?|log)$/i.test(path)
    || /\.(?:pem|key|p12|pfx)$/i.test(path)) fail('unsafe_source_path');
  return path;
}

export function validateSourceManifest(input) {
  exact(input, ['repository', 'revision', 'files'], 'source');
  if (typeof input.repository !== 'string' || !/^(?:fixture:\/\/[a-z0-9-]+|https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)$/.test(input.repository)) fail('unsafe_repository');
  if (typeof input.revision !== 'string' || !/^[a-f0-9]{40}$/.test(input.revision)) fail('invalid_source_revision');
  if (!Array.isArray(input.files) || input.files.length < 1 || input.files.length > 1000) fail('source_files_required');
  const seen = new Set();
  for (const file of input.files) {
    exact(file, ['path', 'sha256'], 'source_file'); sourcePath(file.path);
    if (seen.has(file.path) || typeof file.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(file.sha256)) fail('invalid_source_digest');
    seen.add(file.path);
  }
  return structuredClone(input);
}

export function validateHandoffPlan(plan) {
  exact(plan, ['schema_version', 'kind', 'source', 'target', 'checks', 'steps'], 'plan');
  literal(plan.schema_version, 1, 'unsupported_handoff_schema');
  literal(plan.kind, 'source-only-handoff', 'unsupported_handoff_kind');
  validateSourceManifest(plan.source);
  exact(plan.target, ['requires_new_task', 'auto_resume'], 'target');
  literal(plan.target.requires_new_task, true, 'new_task_required');
  literal(plan.target.auto_resume, false, 'auto_resume_forbidden');
  exact(plan.checks, ['delivery_completed', 'queue_empty', 'runtime_idle', 'approval_consumed', 'source_clean', 'tests_passed'], 'checks');
  for (const [key, value] of Object.entries(plan.checks)) literal(value, true, `${key}_required`);
  if (!Array.isArray(plan.steps) || JSON.stringify(plan.steps) !== JSON.stringify(HANDOFF_STEPS)) fail('handoff_steps_changed');
  return structuredClone(plan);
}

// This is an export contract, not an authentication or remote deployment boundary.
// The coordinator must supply evidence from its selected runtime/task and Git worktree.
export function createHandoffPlan(input) {
  exact(input, ['source', 'completion', 'approval', 'checks'], 'evidence');
  exact(input.completion, ['runtime', 'delivery', 'pending'], 'completion');
  if (input.completion.delivery !== 'completed') fail('delivery_not_confirmed');
  if (input.completion.runtime !== 'idle') fail('runtime_not_idle');
  if (input.completion.pending !== 0) fail('instructions_remaining');
  exact(input.approval, ['allowed', 'consumed'], 'approval');
  if (input.approval.allowed !== true || input.approval.consumed !== true) fail('approval_not_consumed');
  exact(input.checks, ['source_clean', 'tests_passed'], 'checks');
  if (input.checks.source_clean !== true || input.checks.tests_passed !== true) fail('source_checks_incomplete');
  return validateHandoffPlan({
    schema_version: 1, kind: 'source-only-handoff', source: validateSourceManifest(input.source),
    target: { requires_new_task: true, auto_resume: false },
    checks: { delivery_completed: true, queue_empty: true, runtime_idle: true, approval_consumed: true, source_clean: true, tests_passed: true },
    steps: [...HANDOFF_STEPS],
  });
}

export const sha256 = value => createHash('sha256').update(value).digest('hex');
