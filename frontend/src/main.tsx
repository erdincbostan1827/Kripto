import React from 'react';
import ReactDOM from 'react-dom/client';
import {BrowserRouter} from 'react-router-dom';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {CssBaseline,ThemeProvider} from '@mui/material';
import App from './App';
import {AuthGate} from './components/AuthGate';
import {getCompatibility} from './api/client';
import {CLIENT_VERSION,isClientCompatible} from './runtime/clientShell';
import {appTheme} from './ux/theme';
const query=new QueryClient({defaultOptions:{queries:{staleTime:3000,retry:1,gcTime:300000}}});
async function boot(){
  const root=ReactDOM.createRoot(document.getElementById('root')!);
  try{
    const c=await getCompatibility();
    if(!isClientCompatible(c))throw new Error(`Uyumsuz istemci/sunucu: client ${CLIENT_VERSION}, server ${c.server_version}`);
    root.render(<React.StrictMode><ThemeProvider theme={appTheme}><CssBaseline/><QueryClientProvider client={query}><BrowserRouter><AuthGate><App/></AuthGate></BrowserRouter></QueryClientProvider></ThemeProvider></React.StrictMode>)
  }catch(e){root.render(<main style={{padding:24,fontFamily:'system-ui'}}><h1>Güvenli başlatma durduruldu</h1><p>{e instanceof Error?e.message:'Compatibility check failed'}</p><p>Risk artırıcı işlemler istemci uyumluluğu doğrulanmadan kullanılamaz.</p></main>)}
}
void boot();

if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>undefined));}
