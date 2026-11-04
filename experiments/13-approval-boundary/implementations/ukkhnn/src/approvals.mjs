import { JsonStore } from './store.mjs';
import { epoch, fingerprint, immutable, nonempty } from './fingerprint.mjs';

function revision(value) {
  if (!Number.isSafeInteger(value) || value < 0) throw new TypeError('invalid_revision');
  return value;
}

function validateRecord(item) {
  nonempty(item.id, 'id'); nonempty(item.taskId, 'taskId'); nonempty(item.ownerId, 'ownerId');
  revision(item.revision); epoch(item.expiresAt, 'expiresAt');
  if (fingerprint(item.action) !== item.fingerprint || !['pending', 'approved', 'rejected', 'expired', 'superseded'].includes(item.status)) {
    throw new Error('corrupt_approval');
  }
  if (item.consumed !== (item.status === 'approved')) throw new Error('corrupt_consumption');
}

export class ApprovalLedger {
  constructor(file) { this.store = new JsonStore(file); }

  request({ id, taskId, ownerId, action, revision: rev, expiresAt }) {
    nonempty(id, 'id'); nonempty(taskId, 'taskId'); nonempty(ownerId, 'ownerId');
    revision(rev); epoch(expiresAt, 'expiresAt');
    const record = immutable({ id, taskId, ownerId, action, revision: rev, expiresAt,
      fingerprint: fingerprint(action), status: 'pending', consumed: false });
    return this.store.transaction(state => {
      state.requests.forEach(validateRecord);
      if (state.requests.some(item => item.id === id)) throw new Error('duplicate_approval_id');
      const related = state.requests.filter(item => item.taskId === taskId && item.ownerId === ownerId);
      if (related.some(item => item.revision > rev)) throw new Error('stale_revision');
      for (const item of related) if (item.status === 'pending' && item.revision < rev) item.status = 'superseded';
      state.requests.push(record);
      return immutable(record);
    });
  }

  decide(id, { taskId, ownerId, action, revision: rev, now, allow } = {}) {
    const denied = reason => immutable({ id: typeof id === 'string' ? id : '', allowed: false, consumed: false, reason });
    try {
      nonempty(id, 'id'); nonempty(taskId, 'taskId'); nonempty(ownerId, 'ownerId');
      revision(rev); epoch(now, 'now'); fingerprint(action);
      if (typeof allow !== 'boolean') return denied('invalid_allow');
    } catch { return denied('invalid_input'); }
    return this.store.transaction(state => {
      state.requests.forEach(validateRecord);
      const item = state.requests.find(candidate => candidate.id === id);
      if (!item) return denied('not_found');
      if (item.taskId !== taskId || item.ownerId !== ownerId) return denied('scope_mismatch');
      if (item.revision !== rev) return denied('stale_revision');
      if (item.fingerprint !== fingerprint(action)) return denied('action_changed');
      if (item.status !== 'pending') return denied(item.status === 'approved' ? 'already_consumed' : item.status);
      if (now >= item.expiresAt) { item.status = 'expired'; return denied('expired'); }
      item.status = allow ? 'approved' : 'rejected';
      item.consumed = allow;
      item.decidedAt = now;
      return immutable({ ...item, allowed: allow, reason: allow ? 'approved' : 'user_rejected' });
    });
  }

  list(taskId) {
    nonempty(taskId, 'taskId');
    const state = this.store.read();
    state.requests.forEach(validateRecord);
    return immutable(state.requests.filter(item => item.taskId === taskId));
  }
}
