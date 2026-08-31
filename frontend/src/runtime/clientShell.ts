export const CLIENT_VERSION='0.3.0';

export type CompatibilityWindow={
  api_version:string;
  server_version:string;
  min_client:string;
  max_client:string;
};

type ImportMetaWithEnv=ImportMeta&{env?:Record<string,string|undefined>};

export function isTauriShell():boolean{
  return typeof window!=='undefined' && '__TAURI_INTERNALS__' in (window as unknown as Record<string,unknown>);
}

function configuredBase():string{
  const env=(import.meta as ImportMetaWithEnv).env;
  return (env?.VITE_API_BASE_URL??'').trim().replace(/\/$/,'');
}

export function apiBaseUrl():string{
  const base=configuredBase();
  if(!base)return '';
  let url:URL;
  try{url=new URL(base)}catch{throw new Error('INVALID_API_BASE_URL')}
  if(url.username||url.password)throw new Error('API_BASE_URL_MUST_NOT_CONTAIN_CREDENTIALS');
  if(isTauriShell()&&url.protocol!=='https:')throw new Error('TAURI_REQUIRES_HTTPS_BACKEND');
  if(!['http:','https:'].includes(url.protocol))throw new Error('UNSUPPORTED_API_BASE_SCHEME');
  return url.origin;
}

export function apiUrl(path:string):string{
  if(!path.startsWith('/'))throw new Error('API_PATH_MUST_BE_ABSOLUTE');
  return `${apiBaseUrl()}${path}`;
}

export function websocketUrl(path:string):string{
  if(!path.startsWith('/'))throw new Error('WS_PATH_MUST_BE_ABSOLUTE');
  const base=apiBaseUrl();
  if(base){const u=new URL(base);u.protocol=u.protocol==='https:'?'wss:':'ws:';u.pathname=path;u.search='';u.hash='';return u.toString()}
  const scheme=location.protocol==='https:'?'wss:':'ws:';
  return `${scheme}//${location.host}${path}`;
}

function parseCore(version:string):[number,number,number]|null{
  const m=/^(\d+)\.(\d+)\.(\d+)$/.exec(version);
  return m?[Number(m[1]),Number(m[2]),Number(m[3])]:null;
}

export function isClientCompatible(c:CompatibilityWindow):boolean{
  if(c.api_version!=='v1')return false;
  const client=parseCore(CLIENT_VERSION); const min=parseCore(c.min_client);
  if(!client||!min)return false;
  const maxWildcard=/^(\d+)\.(\d+)\.x$/.exec(c.max_client);
  if(!maxWildcard)return false;
  const [cmj,cmi,cp]=client; const [mmj,mmi,mp]=min;
  const atLeastMin=cmj>mmj||(cmj===mmj&&(cmi>mmi||(cmi===mmi&&cp>=mp)));
  const withinMax=cmj===Number(maxWildcard[1])&&cmi===Number(maxWildcard[2]);
  return atLeastMin&&withinMax;
}
