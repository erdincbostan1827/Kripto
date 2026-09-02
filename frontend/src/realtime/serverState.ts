import {apiUrl,websocketUrl} from '../runtime/clientShell';
import {applyIncremental,applySnapshot,initialRealtimeState,RealtimeState,VersionedSnapshot} from './versionedState';

export type ServerDashboard=Record<string,unknown>;
export type ServerStateListener=(state:RealtimeState<ServerDashboard>)=>void;

export class AuthenticatedServerState {
  private state:RealtimeState<ServerDashboard>=initialRealtimeState<ServerDashboard>();
  private ws:WebSocket|undefined;
  constructor(private readonly listener:ServerStateListener){}
  async start(){
    const response=await fetch(apiUrl('/api/v1/dashboard'),{credentials:'include',headers:{Accept:'application/json'}});
    if(!response.ok)throw new Error('INITIAL_SNAPSHOT_FAILED');
    const payload=await response.json() as ServerDashboard;
    this.state=applySnapshot(this.state,{sequence:0,version:'v1',receivedAt:Date.now(),sourceTime:Date.now(),payload});
    this.listener(this.state);
    this.ws=new WebSocket(websocketUrl('/api/v1/ws')); // same-origin cookie on web; configured HTTPS/WSS backend in the optional desktop shell.
    this.ws.onmessage=(event)=>{
      const message=JSON.parse(event.data) as {sequence:number;schema_version:number;payload:ServerDashboard};
      const next:VersionedSnapshot<ServerDashboard>={sequence:message.sequence,version:`v${message.schema_version}`,receivedAt:Date.now(),sourceTime:Date.now(),payload:message.payload};
      this.state=applyIncremental(this.state,next); this.listener(this.state);
    };
    this.ws.onclose=()=>{this.state={...this.state,stale:true,needsResync:true,lastDisconnectReason:'SOCKET_CLOSED'};this.listener(this.state)};
  }
  stop(){this.ws?.close();this.ws=undefined}
}
