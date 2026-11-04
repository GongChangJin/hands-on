const states = new Set(['queued', 'sending', 'completed', 'uncertain', 'cancelled']);

export function project(events) {
  const state = { paused: false, messages: [] };
  for (const event of events) {
    const p = object(event.payload, 'queue payload');
    if (event.type.startsWith('instruction.')) identifier(p.id, 'messageId');
    const message = state.messages.find(m => m.id === p.id);
    switch (event.type) {
      case 'instruction.queued':
        if (message || typeof p.text !== 'string' || !p.text.trim() || p.text.length > 20000) throw new Error('Invalid queue history');
        state.messages.push({ id: p.id, text: p.text, status: 'queued' }); break;
      case 'instruction.sending':
        if (state.paused || message?.status !== 'queued' || state.messages.some(m => ['sending', 'uncertain'].includes(m.status))) throw new Error('Invalid dispatch history');
        message.status = 'sending'; break;
      case 'instruction.completed':
        if (message?.status !== 'sending') throw new Error('Invalid acknowledgement history');
        message.status = 'completed'; break;
      case 'instruction.uncertain':
        if (message?.status !== 'sending') throw new Error('Invalid uncertain history');
        message.status = 'uncertain'; state.paused = true; break;
      case 'instruction.resolved':
        if (message?.status !== 'uncertain' || !['completed', 'cancelled'].includes(p.outcome) || !p.evidence) throw new Error('Invalid resolution history');
        message.status = p.outcome; message.resolution = p.evidence; break;
      case 'queue.stopped': state.paused = true; break;
      case 'queue.resumed':
        if (state.messages.some(m => ['sending', 'uncertain'].includes(m.status))) throw new Error('Unresolved history');
        state.paused = false; break;
      default: throw new Error('Unsupported queue event');
    }
  }
  if (state.messages.some(m => !states.has(m.status))) throw new Error('Invalid message state');
  return state;
}
import { identifier, object } from '../../../../11-session-persistence/implementations/ukkhnn/src/validation.mjs';
