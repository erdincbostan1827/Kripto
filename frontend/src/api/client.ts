import {apiUrl} from '../runtime/clientShell';
export type Compatibility={api_version:string;server_version:string;min_client:string;max_client:string};
export type AuthContext={user_id:string;username:string;role:string;csrf_token:string};
let csrfToken='';
export function setCsrfToken(value:string){csrfToken=value}
export function clearCsrfToken(){csrfToken=''}
export function getCsrfToken(){return csrfToken}
export async function api<T>(path:string,init?:RequestInit):Promise<T>{
  const method=(init?.method??'GET').toUpperCase();
  const mutation=!['GET','HEAD','OPTIONS'].includes(method);
  const headers:Record<string,string>={'Content-Type':'application/json'};
  if(mutation&&csrfToken)headers['X-CSRF-Token']=csrfToken;
  Object.assign(headers,init?.headers??{});
  const r=await fetch(apiUrl(path),{credentials:'include',...init,headers});
  if(!r.ok)throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>
}
export const getCompatibility=()=>api<Compatibility>('/api/v1/compatibility');
export async function restoreAuth(){const x=await api<AuthContext>('/api/v1/auth/me');setCsrfToken(x.csrf_token);return x}
export async function login(username:string,password:string,mfa_code?:string,recovery_code?:string){
  const x=await api<AuthContext>('/api/v1/auth/login',{method:'POST',body:JSON.stringify({username,password,mfa_code:mfa_code||undefined,recovery_code:recovery_code||undefined})});
  setCsrfToken(x.csrf_token);return x
}
export async function logout(){await api('/api/v1/auth/logout',{method:'POST'});clearCsrfToken()}
export type SetupSnapshot={setup_id:string;current_step:number;completed_steps:number[];non_secret_config:Record<string,unknown>;completed:boolean;startup_mode:string};
export const getSetup=()=>api<SetupSnapshot>('/api/v1/setup');
export const completeSetupStep=(step:number,data:Record<string,unknown>)=>api<SetupSnapshot>('/api/v1/setup/step',{method:'POST',body:JSON.stringify({setup_id:'default',step,data})});
export const beginMfa=(password:string)=>api<{secret:string;otpauth_uri:string;message:string}>('/api/v1/auth/mfa/enroll',{method:'POST',body:JSON.stringify({password})});
export const confirmMfa=(code:string)=>api<{enabled:boolean;recovery_codes:string[];message:string}>('/api/v1/auth/mfa/confirm',{method:'POST',body:JSON.stringify({code})});

export async function bootstrapAdmin(username:string,password:string,bootstrap_token:string){
  return api<{user_id:string;created:boolean}>('/api/v1/auth/bootstrap-admin',{method:'POST',body:JSON.stringify({username,password,bootstrap_token})})
}
