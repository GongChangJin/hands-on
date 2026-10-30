import { readFileSync, realpathSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { isAbsolute, relative, resolve, sep } from 'node:path';
import { sourcePath, sha256, validateSourceManifest } from './plan.mjs';

export const reference = JSON.parse(readFileSync(new URL('../../../shared/reference.json', import.meta.url), 'utf8'));

export function verifyReferenceFiles(root, pinned = reference) {
  if (!pinned || typeof pinned !== 'object' || Array.isArray(pinned) || pinned.schema_version !== 1) throw new Error('invalid_reference');
  validateSourceManifest({repository:'fixture://read-only-reference',revision:pinned.revision,files:pinned.files});
  const directory = realpathSync(root);
  const git = args => execFileSync('git', ['-C', directory, ...args], {encoding:'utf8', stdio:['ignore','pipe','pipe']}).trim();
  let revision;
  try { revision = git(['rev-parse', 'HEAD']); } catch { throw new Error('reference_repository_unavailable'); }
  if (revision !== pinned.revision) throw new Error('reference_revision_changed');
  if (git(['status', '--porcelain'])) throw new Error('reference_worktree_changed');
  for (const file of pinned.files) {
    sourcePath(file.path);
    const full = realpathSync(resolve(directory, file.path));
    const local = relative(directory, full);
    if (local === '..' || local.startsWith('..' + sep) || isAbsolute(local)) throw new Error('reference_path_escape');
    if (sha256(readFileSync(full)) !== file.sha256) throw new Error('reference_digest_changed');
  }
  return { status:'verified_read_only', revision, files_verified:pinned.files.length, application_executed:false };
}
