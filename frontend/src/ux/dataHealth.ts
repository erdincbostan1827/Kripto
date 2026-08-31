export type DataHealth={stale:boolean;needsResync:boolean;ageMs:number;reason?:string};
export type DataHealthPresentation={severity:'success'|'warning'|'error';label:string;blocking:boolean};

export function dataHealthPresentation(h:DataHealth):DataHealthPresentation{
  if(h.needsResync)return {severity:'error',label:`VERİ SENKRONİZASYONU GEREKLİ${h.reason?`: ${h.reason}`:''}`,blocking:true};
  if(h.stale)return {severity:'warning',label:`VERİ GÜNCEL DEĞİL (${Math.max(0,Math.round(h.ageMs/1000))} sn)`,blocking:true};
  return {severity:'success',label:'Market Data: Fresh',blocking:false};
}
