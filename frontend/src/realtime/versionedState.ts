export type VersionedSnapshot<T>={sequence:number;version:string;receivedAt:number;sourceTime:number;payload:T};
export type RealtimeState<T>={snapshot?:VersionedSnapshot<T>|undefined;stale:boolean;needsResync:boolean;lastDisconnectReason?:string|undefined};
export const initialRealtimeState=<T>():RealtimeState<T>=>({stale:true,needsResync:true});
export function applySnapshot<T>(_state:RealtimeState<T>,next:VersionedSnapshot<T>):RealtimeState<T>{
  return {snapshot:next,stale:false,needsResync:false};
}
export function applyIncremental<T>(state:RealtimeState<T>,next:VersionedSnapshot<T>):RealtimeState<T>{
  if(!state.snapshot)return {snapshot:undefined,stale:true,needsResync:true,lastDisconnectReason:'MISSING_INITIAL_SNAPSHOT'};
  if(next.sequence<=state.snapshot.sequence)return state;
  if(next.sequence!==state.snapshot.sequence+1)return {...state,stale:true,needsResync:true,lastDisconnectReason:'SEQUENCE_GAP'};
  if(next.version!==state.snapshot.version)return {...state,stale:true,needsResync:true,lastDisconnectReason:'VERSION_MISMATCH'};
  return {snapshot:next,stale:false,needsResync:false};
}
export function markDisconnected<T>(state:RealtimeState<T>,reason:string):RealtimeState<T>{return {...state,stale:true,needsResync:true,lastDisconnectReason:reason}}
