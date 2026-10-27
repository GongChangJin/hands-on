import { HttpError } from './policy.mjs';

export async function body(req, limit = 16384) {
  if ((req.headers['content-type'] ?? '').split(';')[0].trim() !== 'application/json') throw new HttpError(415, 'json_required');
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw new HttpError(413, 'body_too_large');
    chunks.push(chunk);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); }
  catch { throw new HttpError(400, 'invalid_json'); }
}

export function reply(res, status, value) {
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
    'content-security-policy': "default-src 'none'",
  });
  res.end(JSON.stringify(value));
}
