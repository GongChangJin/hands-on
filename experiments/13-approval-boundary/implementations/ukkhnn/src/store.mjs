import { closeSync, existsSync, fsyncSync, lstatSync, mkdirSync, openSync, readFileSync, renameSync, unlinkSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

export class JsonStore {
  constructor(file) {
    this.file = resolve(file);
    mkdirSync(dirname(this.file), { recursive: true });
  }

  read() {
    if (!existsSync(this.file)) return { version: 1, requests: [] };
    if (!lstatSync(this.file).isFile() || lstatSync(this.file).isSymbolicLink()) throw new Error('unsafe_ledger_file');
    const value = JSON.parse(readFileSync(this.file, 'utf8'));
    if (value.version !== 1 || !Array.isArray(value.requests)) throw new Error('invalid_ledger');
    return value;
  }

  transaction(update) {
    const lock = this.file + '.lock';
    let lockFd;
    try { lockFd = openSync(lock, 'wx', 0o600); }
    catch (error) { if (error.code === 'EEXIST') throw new Error('ledger_busy'); throw error; }
    const temporary = this.file + '.' + randomUUID() + '.tmp';
    try {
      const state = this.read();
      const result = update(state);
      const fd = openSync(temporary, 'wx', 0o600);
      try { writeFileSync(fd, JSON.stringify(state) + '\n'); fsyncSync(fd); }
      finally { closeSync(fd); }
      renameSync(temporary, this.file);
      return result;
    } finally {
      if (existsSync(temporary)) unlinkSync(temporary);
      closeSync(lockFd);
      unlinkSync(lock);
    }
  }
}
