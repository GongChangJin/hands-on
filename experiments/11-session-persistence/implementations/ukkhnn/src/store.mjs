import { readFileSync } from 'node:fs';
import { stateFile, acquireLock, atomicWrite } from './atomic.mjs';
import { encode, decode } from './snapshot.mjs';
import { identifier, payload, cursor, object } from './validation.mjs';

export class SessionStore {
  #data; #release; #closed = false; #failed = false;
  constructor(file) {
    this.file = stateFile(file); this.#release = acquireLock(this.file);
    try {
      try { this.#data = decode(readFileSync(this.file, 'utf8')); }
      catch (error) {
        if (error.code !== 'ENOENT') throw error;
        this.#data = { version: 1, tasks: [], events: [], nextSeq: 1 };
        atomicWrite(this.file, encode(this.#data));
      }
    } catch (error) { this.#release(); this.#closed = true; throw error; }
  }
  #assertOpen() { if (this.#closed || this.#failed) throw new Error('Store closed or write outcome uncertain'); }
  #commit(data) {
    this.#assertOpen(); const encoded = encode(data);
    if (Buffer.byteLength(encoded) > 10 * 1024 * 1024) throw new Error('Snapshot too large');
    try { atomicWrite(this.file, encoded); this.#data = data; }
    catch (error) { this.#failed = true; throw error; }
  }
  createTask(input) {
    this.#assertOpen(); object(input, 'task');
    const task = { id: identifier(input.id), projectId: identifier(input.projectId, 'projectId'), ownerId: identifier(input.ownerId, 'ownerId') };
    const found = this.#data.tasks.find(t => t.id === task.id);
    if (found) {
      if (found.projectId !== task.projectId || found.ownerId !== task.ownerId) throw new Error('Task identity conflict');
      return structuredClone(found);
    }
    const next = structuredClone(this.#data); next.tasks.push(task); this.#commit(next);
    return structuredClone(task);
  }
  getTask(id) {
    this.#assertOpen(); identifier(id);
    const task = this.#data.tasks.find(t => t.id === id);
    if (!task) throw new Error('Unknown task');
    return structuredClone(task);
  }
  listTasks() { this.#assertOpen(); return structuredClone(this.#data.tasks); }
  appendEvent(taskId, input) {
    this.getTask(taskId); object(input, 'event');
    const event = { seq: this.#data.nextSeq, taskId, type: identifier(input.type, 'type'), payload: payload(input.payload) };
    const next = structuredClone(this.#data); next.events.push(event); next.nextSeq++;
    this.#commit(next); return structuredClone(event);
  }
  events(taskId, afterSeq = 0) {
    this.getTask(taskId); cursor(afterSeq);
    return structuredClone(this.#data.events.filter(e => e.taskId === taskId && e.seq > afterSeq));
  }
  close() { if (!this.#closed) { this.#release(); this.#closed = true; } }
}
