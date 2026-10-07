import { SessionStore } from '../../../../11-session-persistence/implementations/ukkhnn/src/store.mjs';
import { identifier, object } from '../../../../11-session-persistence/implementations/ukkhnn/src/validation.mjs';
import { project } from './projection.mjs';

export class InstructionQueue {
  #store;
  constructor(file) {
    this.#store = new SessionStore(file);
    try {
      for (const task of this.#store.listTasks()) {
        if (task.projectId !== 'instruction-queue' || task.ownerId !== 'local-coordinator') throw new Error('Not an instruction queue store');
        const state = this.#state(task.id);
        for (const message of state.messages.filter(m => m.status === 'sending')) {
          this.#store.appendEvent(task.id, { type: 'instruction.uncertain', payload: { id: message.id, reason: 'process-restart' } });
        }
      }
    } catch (error) { this.#store.close(); throw error; }
  }
  #state(taskId) { identifier(taskId, 'taskId'); return project(this.#store.events(taskId)); }
  #message(taskId, id) {
    identifier(id, 'messageId');
    const message = this.#state(taskId).messages.find(m => m.id === id);
    if (!message) throw new Error('Unknown instruction');
    return message;
  }
  #append(taskId, type, payload) { return this.#store.appendEvent(taskId, { type, payload }); }
  ensureTask(taskId) {
    identifier(taskId, 'taskId');
    return this.#store.createTask({ id: taskId, projectId: 'instruction-queue', ownerId: 'local-coordinator' });
  }
  enqueue(taskId, input) {
    identifier(taskId, 'taskId'); object(input, 'instruction'); identifier(input.id, 'messageId');
    if (typeof input.text !== 'string' || !input.text.trim() || input.text.length > 20000) throw new Error('Invalid instruction text');
    this.ensureTask(taskId);
    const previous = this.#state(taskId).messages.find(m => m.id === input.id);
    if (previous) {
      if (previous.text !== input.text) throw new Error('Idempotency conflict');
      return previous;
    }
    this.#append(taskId, 'instruction.queued', { id: input.id, text: input.text });
    return this.#message(taskId, input.id);
  }
  next(taskId) {
    const state = this.#state(taskId);
    if (state.paused || state.messages.some(m => ['sending', 'uncertain'].includes(m.status))) return null;
    const next = state.messages.find(m => m.status === 'queued');
    if (!next) return null;
    // This commit must succeed BEFORE callers may invoke the runtime.
    this.#append(taskId, 'instruction.sending', { id: next.id });
    return this.#message(taskId, next.id);
  }
  acknowledge(taskId, messageId) {
    const message = this.#message(taskId, messageId);
    if (message.status === 'completed') return message;
    if (message.status !== 'sending') throw new Error('Only an active instruction can complete');
    this.#append(taskId, 'instruction.completed', { id: messageId });
    return this.#message(taskId, messageId);
  }
  markUncertain(taskId, messageId) {
    const message = this.#message(taskId, messageId);
    if (message.status === 'uncertain') return message;
    if (message.status !== 'sending') throw new Error('Only an active instruction can be uncertain');
    this.#append(taskId, 'instruction.uncertain', { id: messageId, reason: 'transport-outcome-unknown' });
    return this.#message(taskId, messageId);
  }
  stop(taskId) {
    this.#state(taskId); this.#append(taskId, 'queue.stopped', {});
    return { paused: true, active: this.list(taskId).filter(m => ['sending', 'uncertain'].includes(m.status)).map(m => m.id) };
  }
  resume(taskId) {
    if (this.#state(taskId).messages.some(m => ['sending', 'uncertain'].includes(m.status))) throw new Error('Resolve active or uncertain instruction before resume');
    this.#append(taskId, 'queue.resumed', {}); return { paused: false };
  }
  resolve(taskId, messageId, input) {
    object(input, 'resolution');
    if (!['completed', 'cancelled'].includes(input.outcome) || typeof input.evidence !== 'string' || !input.evidence.trim() || input.evidence.length > 1000) throw new Error('Resolution requires outcome and evidence');
    if (this.#message(taskId, messageId).status !== 'uncertain') throw new Error('Only an uncertain instruction can be resolved');
    this.#append(taskId, 'instruction.resolved', { id: messageId, outcome: input.outcome, evidence: input.evidence });
    return this.#message(taskId, messageId);
  }
  list(taskId) { return this.#state(taskId).messages; }
  status(taskId) { return this.#state(taskId); }
  close() { this.#store.close(); }
}
