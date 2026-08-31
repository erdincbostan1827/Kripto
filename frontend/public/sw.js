const CACHE='ctp-shell-v1'; const SHELL=['/','/manifest.webmanifest'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL))));
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return; const u=new URL(e.request.url); if(u.pathname.startsWith('/api/')||u.pathname.includes('ws'))return; e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));});
// This worker is a read-only shell cache. It never submits orders, stores secrets, or acts as a trading engine.
