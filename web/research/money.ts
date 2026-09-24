export function parseGen(value:string):bigint{
  const v=value.trim();
  if(!/^\d+(\.\d{0,18})?$/.test(v||"0")) throw new Error("GEN amount must be a non-negative decimal with at most 18 decimal places");
  const [whole,frac=""]=(v||"0").split(".");
  return BigInt(whole||"0")*10n**18n+BigInt((frac+"0".repeat(18)).slice(0,18));
}
export function formatGen(value:string|number|bigint, digits=4):string{
  try{
    const n=BigInt(String(value));
    const whole=n/10n**18n;const frac=(n%10n**18n).toString().padStart(18,"0").slice(0,digits).replace(/0+$/g,"");
    return frac?`${whole}.${frac}`:whole.toString();
  }catch{return"0"}
}
