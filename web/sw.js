const CACHE='skin-ai-beta-v14';
const CORE=['/','/app/styles.css','/app/app.js','/app/capture_guidance_mobile_v12.js?v=12','/app/mobile_ux_v11.js?v=13','/app/server_error_guard.js?v=1'];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE)).catch(()=>{}));
  self.skipWaiting();
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  event.respondWith(fetch(event.request).catch(()=>caches.match(event.request).then(r=>r||caches.match('/'))));
});
