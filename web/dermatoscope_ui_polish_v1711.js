// V1.7.1.2 — consumer-facing close-up scan copy/branding polish hotfix.
(function(){
  const VERSION='1.7.1.2'
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const pick=(en,vi)=>locale()==='vi'?vi:en
  const setText=(el,value)=>{if(el && el.textContent!==value) el.textContent=value}
  const setAttr=(el,name,value)=>{if(el && el.getAttribute(name)!==value) el.setAttribute(name,value)}
  let applying=false

  function addStyle(href){if(!document.querySelector(`link[href*="${href.split('?')[0].split('/').pop()}"]`)){const link=document.createElement('link');link.rel='stylesheet';link.href=href;document.head.appendChild(link)}}
  function addScript(src){if(!document.querySelector(`script[src*="${src.split('?')[0].split('/').pop()}"]`)){const script=document.createElement('script');script.src=src;script.defer=true;document.body.appendChild(script)}}
  function loadHistoryAssets(){addStyle('/app/dermatoscope_history_v172.css?v=172');addScript('/app/dermatoscope_history_v172.js?v=172')}
  function loadLiveGuidanceAssets(){addStyle('/app/dermatoscope_live_guidance_v174.css?v=174');addScript('/app/dermatoscope_live_guidance_v174.js?v=174')}
  function loadPostCaptureAssets(){addStyle('/app/dermatoscope_postcapture_v175.css?v=175');addScript('/app/dermatoscope_postcapture_v175.js?v=175')}
  function loadSessionAssets(){addStyle('/app/dermatoscope_session_v176.css?v=176');addScript('/app/dermatoscope_session_v176.js?v=1761')}
  function loadResumeAssets(){addStyle('/app/dermatoscope_resume_v177.css?v=177');addScript('/app/dermatoscope_resume_v177.js?v=177')}

  function apply(){
    if(applying)return
    applying=true
    try{
      const root=document.querySelector('#dermV171')
      if(!root)return
      const intro=root.querySelector('.dermIntroCard')
      if(intro){
        setText(intro.querySelector('.eyebrow'),pick('CLOSE-UP SKIN SCAN','QUÉT DA CẬN CẢNH'))
        setText(intro.querySelector('h2'),pick('Choose a skin area to examine','Chọn vùng da cần kiểm tra'))
        setText(intro.querySelector('.dermNotice'),pick('Choose an area and the app will guide each close-up position. Images are captured automatically when the capture checks are ready.','Chọn một vùng da để kiểm tra. Ứng dụng sẽ hướng dẫn từng vị trí và tự động chụp khi hình ảnh đạt yêu cầu.'))
      }
      const setup=root.querySelector('#dermSetup')
      if(setup){setText(setup.querySelector('.eyebrow'),pick('PREPARE SKIN SCOPE','CHUẨN BỊ MÁY SOI'));setText(setup.querySelector('.dermDeviceRow h3'),'Skin AI Scope');setText(setup.querySelector('.dermDeviceRow p'),pick('Standard setup for this scan','Cấu hình chuẩn cho lần quét này'))}
      root.querySelectorAll('.dermRegion').forEach(button=>setAttr(button,'aria-pressed',button.classList.contains('active')?'true':'false'))
      setAttr(document.documentElement,'data-dermatoscope-ui-polish-version',VERSION)
    }finally{applying=false}
  }

  function watch(){
    loadHistoryAssets();loadLiveGuidanceAssets();loadPostCaptureAssets();loadSessionAssets();loadResumeAssets();apply()
    const scan=document.querySelector('#scan');if(!scan)return
    let queued=false
    const observer=new MutationObserver(()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;apply()})})
    observer.observe(scan,{childList:true,subtree:true})
  }

  window.addEventListener('skin-ai:locale-change',()=>requestAnimationFrame(apply))
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>requestAnimationFrame(watch));else requestAnimationFrame(watch)
  window.skinDermatoscopeUiPolish={version:VERSION,apply}
})()