import { createServer } from 'node:http';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { SessionStore } from '../../../../11-session-persistence/implementations/ukkhnn/src/store.mjs';
import { InstructionQueue } from '../../../../12-durable-instructions/implementations/ukkhnn/src/queue.mjs';
import { ApprovalLedger } from '../../../../13-approval-boundary/implementations/ukkhnn/src/approvals.mjs';
import { HttpError, identity, requireTask, fields, id, cursor } from './policy.mjs';
import { body, reply } from './protocol.mjs';

export async function openWorkspaceServer({ directory, tokens, clock = Date.now }) {
  if (!(tokens instanceof Map) || tokens.size === 0 || [...tokens].some(([token, owner]) => typeof token !== 'string' || token.length < 24 || !owner)) {
    throw new Error('explicit_fixture_tokens_required');
  }
  mkdirSync(directory, { recursive: true });
  const store = new SessionStore(join(directory, 'sessions.json'));
  let queue, approvals;
  try {
    queue = new InstructionQueue(join(directory, 'instructions.json'));
    approvals = new ApprovalLedger(join(directory, 'approvals.json'));
  } catch (error) { store.close?.(); queue?.close?.(); throw error; }
  // Queue and approval receipts remain authoritative if the secondary audit write fails.
  const audit = (taskId, event) => {
    try { store.appendEvent(taskId, event); return true; }
    catch { return false; }
  };
  let origin;
  const server = createServer(async (req, res) => {
    try {
      const ownerId = identity(req, tokens, origin);
      const url = new URL(req.url, origin);
      if (req.method === 'POST' && url.pathname === '/tasks') {
        const input = fields(await body(req), ['id', 'projectId']);
        const task = store.createTask({ id: id(input.id), projectId: id(input.projectId), ownerId });
        queue.ensureTask(task.id);
        return reply(res, 201, task);
      }
      const match = /^\/tasks\/([A-Za-z0-9_-]+)(?:\/(.*))?$/.exec(url.pathname);
      if (!match) throw new HttpError(404, 'not_found');
      const taskId = id(match[1]);
      const task = requireTask(store, taskId, ownerId);
      const route = match[2] ?? '';
      if (req.method === 'GET' && !route) return reply(res, 200, task);
      if (req.method === 'GET' && route === 'events') {
        const after = cursor(url.searchParams.get('after'));
        const events = store.events(taskId);
        if (after > (events.at(-1)?.seq ?? 0)) throw new HttpError(409, 'cursor_ahead_of_history');
        return reply(res, 200, events.filter(event => event.seq > after));
      }
      if (req.method === 'GET' && route === 'instructions') return reply(res, 200, queue.list(taskId));
      if (req.method === 'POST' && route === 'instructions') {
        const input = fields(await body(req), ['id', 'text']);
        if (typeof input.text !== 'string' || !input.text.trim() || input.text.length > 8000) throw new HttpError(400, 'invalid_text');
        const entry = queue.enqueue(taskId, {id: id(input.id), text: input.text});
        // This is a request event, not proof the runtime has executed the instruction.
        const audit_recorded = audit(taskId, { type: 'instruction.requested', payload: { messageId: input.id } });
        return reply(res, 202, {...entry, audit_recorded});
      }
      if (req.method === 'POST' && route === 'control') {
        const input = fields(await body(req), ['action']);
        if (!['stop', 'resume'].includes(input.action)) throw new HttpError(400, 'invalid_control');
        queue[input.action](taskId);
        const state = input.action === 'stop' ? 'stop_requested' : 'dispatch_resumed';
        const audit_recorded = audit(taskId, {type: state, payload: {}});
        return reply(res, 202, {state, runtimeStopped: false, audit_recorded});
      }
      if (req.method === 'GET' && route === 'approvals') return reply(res, 200, approvals.list(taskId));
      const decision = /^approvals\/([A-Za-z0-9_-]+)\/decision$/.exec(route);
      if (req.method === 'POST' && decision) {
        const input = fields(await body(req), ['action', 'revision', 'allow']);
        if (typeof input.allow !== 'boolean') throw new HttpError(400, 'boolean_required');
        const result = approvals.decide(id(decision[1]), {...input, taskId, ownerId, now: clock()});
        const audit_recorded = audit(taskId, {type: 'approval.decided', payload: {approvalId: decision[1], allowed: result.allowed}});
        return reply(res, 200, {...result, audit_recorded});
      }
      throw new HttpError(404, 'not_found');
    } catch (error) {
      // Internal errors and file paths are never reflected to clients.
      reply(res, error instanceof HttpError ? error.status : 409,
        {error: error instanceof HttpError ? error.code : 'state_conflict'});
    }
  });
  server.requestTimeout = 5000;
  server.headersTimeout = 5000;
  try {
    await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  } catch (error) { store.close?.(); queue.close?.(); approvals.close?.(); throw error; }
  origin = `http://127.0.0.1:${server.address().port}`;
  let closed = false;
  return {
    origin, store, queue, approvals,
    async close() {
      if (closed) return;
      closed = true;
      await new Promise(resolve => { server.close(resolve); server.closeAllConnections(); });
      store.close?.(); queue.close?.(); approvals.close?.();
    },
  };
}
