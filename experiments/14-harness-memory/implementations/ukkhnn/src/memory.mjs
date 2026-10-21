import { digest, freezeSnapshot, identifier } from './json.mjs';

export function createMemoryRecord(input){
  const value=freezeSnapshot(input);
  identifier(value.id,'memory_id');identifier(value.projectId,'project');
  if(!Number.isSafeInteger(value.revision)||value.revision<1)throw new Error('invalid_memory_revision');
  if(value.revision===1?value.supersedes!==null:!Number.isSafeInteger(value.supersedes)||value.supersedes<1||value.supersedes>=value.revision)throw new Error('invalid_supersession');
  if(typeof value.text!=='string'||!value.text.trim()||value.text.length>16000)throw new Error('invalid_memory_text');
  if(typeof value.deleted!=='boolean')throw new Error('invalid_deleted_flag');
  if(!value.source||typeof value.source.uri!=='string'||!value.source.uri.trim()||!/^[a-f0-9]{64}$/.test(value.source.hash))throw new Error('missing_provenance');
  if(!Number.isSafeInteger(value.source.observedAt)||value.source.observedAt<=0)throw new Error('invalid_observed_at');
  if(value.expiresAt!==null&&(!Number.isSafeInteger(value.expiresAt)||value.expiresAt<=value.source.observedAt))throw new Error('invalid_expiry');
  return value;
}

// Resolve revision history before expiry/deletion filtering: never resurrect an old fact.
export function selectMemory(records,{projectId,now,limit=20}){
  identifier(projectId,'project');
  if(!Array.isArray(records)||!Number.isSafeInteger(now)||now<=0||!Number.isSafeInteger(limit)||limit<0||limit>1000)throw new Error('invalid_selection');
  const groups=new Map();
  for(const raw of records){
    if(raw?.projectId!==projectId)continue;
    const record=createMemoryRecord(raw);
    if(record.source.observedAt>now)throw new Error('future_provenance');
    if(!groups.has(record.id))groups.set(record.id,new Map());
    const revisions=groups.get(record.id);
    if(revisions.has(record.revision)&&digest(revisions.get(record.revision))!==digest(record))throw new Error('conflicting_revision');
    revisions.set(record.revision,record);
  }
  const selected=[];
  for(const revisions of groups.values()){
    const ordered=[...revisions.values()].sort((a,b)=>a.revision-b.revision);
    for(let i=0;i<ordered.length;i++){
      const record=ordered[i];
      if(i===0&&record.revision!==1)throw new Error('missing_revision_history');
      if(i>0&&(record.supersedes!==ordered[i-1].revision||record.source.observedAt<ordered[i-1].source.observedAt))throw new Error('forked_revision_history');
    }
    const latest=ordered.at(-1);
    if(!latest.deleted&&(latest.expiresAt===null||now<latest.expiresAt))selected.push(latest);
  }
  selected.sort((a,b)=>b.source.observedAt-a.source.observedAt||a.id.localeCompare(b.id));
  return freezeSnapshot(selected.slice(0,limit));
}

export function memoryForHarness(snapshot,records,now){
  if(!snapshot?.template?.memory?.enabled)return Object.freeze([]);
  return selectMemory(records,{projectId:snapshot.template.memory.projectId,now});
}
