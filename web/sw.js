const CACHE='skin-ai-beta-v156';
const CORE=['/','/app/styles.css','/app/app.js','/app/capture_guidance_mobile_v12.js?v=12','/app/mobile_ux_v11.js?v=13','/app/server_error_guard.js?v=1','/app/rgb_capture_tracking_v14.js?v=14','/app/rgb_measurement_v15.js?v=152','/app/tester_result_v155.css?v=155','/app/tester_result_v155.js?v=155','/app/tester_study_v156.css?v=156','/app/tester_study_v156.js?v=156'];
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
