import { openSync, closeSync, fsyncSync, writeFileSync, renameSync, unlinkSync, mkdirSync, readFileSync, lstatSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

export function stateFile(file) {
  if (typeof file !== 'string' || !file || file.includes('\0')) throw new Error('Invalid state file');
  const path = resolve(file);
  try { if (lstatSync(path).isSymbolicLink()) throw new Error('State symlinks are not allowed'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
  return path;
}

// Exclusive writer ownership. A crash leaves a lock intentionally: operators must
// confirm the writer is dead before removal; lock age alone is never sufficient.
export function acquireLock(file) {
  const path = `${file}.lock`, token = randomUUID();
  const fd = openSync(path, 'wx', 0o600);
  try { writeFileSync(fd, JSON.stringify({ pid: process.pid, token })); fsyncSync(fd); }
  finally { closeSync(fd); }
  return () => {
    const held = JSON.parse(readFileSync(path, 'utf8'));
    if (held.token !== token) throw new Error('Writer lock ownership changed');
    unlinkSync(path);
  };
}

export function atomicWrite(file, value, { beforeRename } = {}) {
  const temp = `${file}.${randomUUID()}.tmp`;
  let renamed = false;
  const fd = openSync(temp, 'wx', 0o600);
  try {
    try { writeFileSync(fd, value, 'utf8'); fsyncSync(fd); }
    finally { closeSync(fd); }
    beforeRename?.();
    renameSync(temp, file); renamed = true;
    const directory = openSync(dirname(file), 'r');
    try { fsyncSync(directory); } finally { closeSync(directory); }
  } finally {
    if (!renamed) { try { unlinkSync(temp); } catch (error) { if (error.code !== 'ENOENT') throw error; } }
  }
}
