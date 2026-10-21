import { digest, freezeSnapshot, identifier, uniqueStrings } from './json.mjs';

export const HARNESS_VERSION=1;
export const HARNESS_FIELDS=['prompt','model','skills','tools','memory','permissions'];

export function createHarnessSnapshot(template,{capabilities=[]}={}){
  const value=freezeSnapshot(template);
  if(!value||typeof value!=='object'||Array.isArray(value))throw new TypeError('template_object_required');
  if(value.version!==HARNESS_VERSION)throw new Error('unsupported_harness_version');
  if(Object.keys(value).sort().join(',')!==['version',...HARNESS_FIELDS].sort().join(','))throw new Error('six_fields_required');
  if(typeof value.prompt!=='string'||!value.prompt.trim()||value.prompt.length>16000)throw new Error('invalid_prompt');
  identifier(value.model?.id,'model');
  const available=new Set(uniqueStrings(capabilities,'runtime_capability'));
  const required=uniqueStrings(value.model.requiredCapabilities,'model_capability');
  if(required.some(item=>!available.has(item)))throw new Error('missing_model_capability');
  if(!Array.isArray(value.skills)||!Array.isArray(value.tools))throw new Error('skills_tools_arrays_required');
  const skills=new Set();
  for(const skill of value.skills){
    identifier(skill.id,'skill');identifier(skill.version,'skill_version');
    if(skills.has(skill.id))throw new Error('duplicate_skill');skills.add(skill.id);
    if(uniqueStrings(skill.requiredCapabilities,'skill_capability').some(item=>!available.has(item)))throw new Error('missing_skill_capability');
  }
  const tools=new Map();
  for(const tool of value.tools){
    identifier(tool.name,'tool');identifier(tool.capability,'tool_capability');
    if(tools.has(tool.name))throw new Error('duplicate_tool');
    if(!available.has(tool.capability))throw new Error('missing_tool_capability');
    if(typeof tool.sideEffect!=='boolean')throw new Error('invalid_side_effect');
    tools.set(tool.name,tool);
  }
  identifier(value.memory?.projectId,'project');
  if(typeof value.memory.enabled!=='boolean')throw new Error('invalid_memory_toggle');
  if(typeof value.permissions?.allowWrites!=='boolean')throw new Error('invalid_write_permission');
  const allowed=uniqueStrings(value.permissions.allowedTools,'allowed_tool');
  if(allowed.some(name=>!tools.has(name)))throw new Error('unconfigured_tool_permission');
  if(!value.permissions.allowWrites&&allowed.some(name=>tools.get(name).sideEffect))throw new Error('write_permission_required');
  return freezeSnapshot({version:HARNESS_VERSION,fingerprint:digest(value),template:value});
}

export const createSnapshot=createHarnessSnapshot;
