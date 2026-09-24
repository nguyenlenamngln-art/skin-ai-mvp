const CACHE='skin-ai-beta-v1605';
const CORE=['/','/app/styles.css','/app/app.js','/app/capture_guidance_mobile_v12.js?v=12','/app/mobile_ux_v11.js?v=13','/app/server_error_guard.js?v=1','/app/rgb_capture_tracking_v14.js?v=14','/app/rgb_measurement_v15.js?v=152','/app/tester_result_v155.css?v=155','/app/tester_result_v155.js?v=155','/app/tester_study_v156.css?v=156','/app/tester_study_v157.css?v=157','/app/tester_study_v157.js?v=157','/app/personal_journey_v158.css?v=158','/app/personal_journey_v158.js?v=158','/app/ux_polish_v1581.css?v=1581','/app/ux_polish_v1581.js?v=1581','/app/mobile_navigation_v1583.css?v=1583','/app/mobile_navigation_v1583.js?v=1583','/app/ios_nav_hotfix_v1584.css?v=1584','/app/ios_nav_hotfix_v1584.js?v=1584','/app/comparable_progress_v159.css?v=159','/app/comparable_progress_v159.js?v=159','/app/comparison_credibility_v1591.css?v=1591','/app/comparison_credibility_v1591.js?v=1591','/app/visual_registration_v1592.css?v=1592','/app/visual_registration_v1592.js?v=1592','/app/mobile_comparison_registration_v1593.css?v=1593','/app/mobile_comparison_registration_v1593.js?v=1593','/app/i18n_v160.css?v=160','/app/i18n_v1601.js?v=1601','/app/localization_runtime_patch_v1602.js?v=1602','/researcher.html','/app/researcher_v157.css?v=157','/app/researcher_v157.js?v=157'];
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