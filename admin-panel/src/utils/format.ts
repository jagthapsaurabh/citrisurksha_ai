export function formatIndianDate(value:any){
  if(!value) return 'Not available';
  const d = new Date(value);
  if(Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString('en-IN',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:true});
}
export function isIdKey(k:string){return k==='id'||k.endsWith('_id')||k==='user_id'||k==='pest_id'}
export function isDateKey(k:string){return k.includes('date')||k.endsWith('_at')}
