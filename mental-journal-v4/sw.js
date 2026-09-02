const CACHE='maeumgyeol-v4-4';
const FALLBACKS=['./manifest.json'];

self.addEventListener('install',event=>{
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(FALLBACKS)));
});

self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(key=>key.startsWith('maeumgyeol-')&&key!==CACHE).map(key=>caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch',event=>{
  const req=event.request;
  if(req.method!=='GET') return;
  const url=new URL(req.url);
  if(url.origin!==self.location.origin || url.pathname.startsWith('/api/')) return;

  // Network-first so a new deploy can never be pinned behind stale JS/CSS/HTML.
  event.respondWith((async()=>{
    try{
      const fresh=await fetch(req,{cache:'no-store'});
      if(fresh && fresh.ok){
        const cache=await caches.open(CACHE);
        cache.put(req,fresh.clone());
      }
      return fresh;
    }catch(err){
      const cached=await caches.match(req);
      if(cached) return cached;
      if(req.mode==='navigate'){
        const home=await caches.match('./');
        if(home) return home;
      }
      throw err;
    }
  })());
});
