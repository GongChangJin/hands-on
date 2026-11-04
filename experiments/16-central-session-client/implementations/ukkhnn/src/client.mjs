export class WorkspaceClient {
  constructor(origin, token) {
    const url = new URL(origin);
    if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
      throw new Error('loopback_fixture_only');
    }
    this.origin = url.origin;
    this.token = token;
    this.cursors = new Map();
  }
  async request(path, {method = 'GET', data, headers = {}} = {}) {
    if (!path.startsWith('/') || path.startsWith('//')) throw new Error('relative_path_required');
    const response = await fetch(this.origin + path, {
      method, headers: {authorization: `Bearer ${this.token}`, origin: this.origin, ...data !== undefined ? {'content-type': 'application/json'} : {}, ...headers},
      body: data === undefined ? undefined : JSON.stringify(data),
      redirect: 'error', signal: AbortSignal.timeout(5000),
    });
    const value = await response.json();
    if (!response.ok) throw Object.assign(new Error(value.error ?? 'request_failed'), {status: response.status});
    return value;
  }
  async events(taskId) {
    const after = this.cursors.get(taskId) ?? 0;
    const rows = await this.request(`/tasks/${encodeURIComponent(taskId)}/events?after=${after}`);
    let last = after;
    for (const row of rows) {
      if (row.taskId !== taskId || !Number.isSafeInteger(row.seq) || row.seq <= last) throw new Error('invalid_event_order');
      last = row.seq;
    }
    this.cursors.set(taskId, last);
    return rows;
  }
}
