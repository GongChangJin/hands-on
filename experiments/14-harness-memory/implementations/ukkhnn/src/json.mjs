import { createHash } from 'node:crypto';

export function canonical(value, seen=new Set()) {
  if(value===null||typeof value==='string'||typeof value==='boolean')return JSON.stringify(value);
  if(typeof value==='number'&&Number.isFinite(value))return JSON.stringify(value);
  if(typeof value!=='object'||seen.has(value))throw new TypeError('finite_json_required');
  if(!Array.isArray(value)&&Object.getPrototypeOf(value)!==Object.prototype&&Object.getPrototypeOf(value)!==null)throw new TypeError('plain_json_required');
  if(Reflect.ownKeys(value).some(k=>typeof k==='symbol'))throw new TypeError('symbol_key');
  seen.add(value);
  let result;
  if(Array.isArray(value)){
    if(Object.keys(value).length!==value.length)throw new TypeError('sparse_array');
    result='['+value.map(v=>canonical(v,seen)).join(',')+']';
  }else{
    const keys=Object.keys(value).sort();
    if(keys.some(k=>!('value' in Object.getOwnPropertyDescriptor(value,k))))throw new TypeError('accessor_not_json');
    result='{'+keys.map(k=>JSON.stringify(k)+':'+canonical(value[k],seen)).join(',')+'}';
  }
  seen.delete(value);return result;
}

export function digest(value){return createHash('sha256').update(canonical(value)).digest('hex');}
export function freezeSnapshot(value){
  const clone=JSON.parse(canonical(value));
  const freeze=item=>{if(item&&typeof item==='object'){Object.values(item).forEach(freeze);Object.freeze(item);}return item;};
  return freeze(clone);
}
export function identifier(value,label){
  if(typeof value!=='string'||!/^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$/.test(value))throw new TypeError(`invalid_${label}`);
  return value;
}
export function uniqueStrings(value,label){
  if(!Array.isArray(value))throw new TypeError(`invalid_${label}`);
  value.forEach(v=>identifier(v,label));
  if(new Set(value).size!==value.length)throw new TypeError(`duplicate_${label}`);
  return value;
}
