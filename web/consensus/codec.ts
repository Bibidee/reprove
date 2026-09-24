export function toPlain<T=any>(value:any):T {
  if (value instanceof Map) {
    const out:Record<string,any> = {};
    for (const [k,v] of value.entries()) out[String(k)] = toPlain(v);
    return out as T;
  }
  if (Array.isArray(value)) return value.map(toPlain) as T;
  if (typeof value === "bigint") return value.toString() as T;
  if (value && typeof value === "object") {
    const out:Record<string,any> = {};
    for (const [k,v] of Object.entries(value)) out[k] = toPlain(v);
    return out as T;
  }
  return value as T;
}
