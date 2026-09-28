// V1.7.1.2 — consumer-facing close-up scan copy/branding polish hotfix.
(function(){
  const VERSION='1.7.1.2'
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const pick=(en,vi)=>locale()==='vi'?vi:en
  const setText=(el,value)=>{if(el && el.textContent!==value) el.textContent=value}
  const setAttr=(el,name,value)=>{if(el && el.getAttribute(name)!==value) el.setAttribute(name,value)}
  let applying=false

  function loadHistoryAssets(){
    if(!document.querySelector('link[href*="dermatoscope_history_v172.css"]')){
      const link=document.createElement('link')
      link.rel='stylesheet';link.href='/app/dermatoscope_history_v172.css?v=172';document.head.appendChild(link)
    }
    if(!document.querySelector('script[src*="dermatoscope_history_v172.js"]')){
      const script=document.createElement('script')
      script.src='/app/dermatoscope_history_v172.js?v=172';script.defer=true;document.body.appendChild(script)
    }
  }

  function apply(){
    if(applying)return
    applying=true
    try{
      const root=document.querySelector('#dermV171')
      if(!root)return

      const intro=root.querySelector('.dermIntroCard')
      if(intro){
        const eyebrow=intro.querySelector('.eyebrow')
        const title=intro.querySelector('h2')
        const notice=intro.querySelector('.dermNotice')
        setText(eyebrow,pick('CLOSE-UP SKIN SCAN','QUÉT DA CẬN CẢNH'))
        setText(title,pick('Choose a skin area to examine','Chọn vùng da cần kiểm tra'))
        setText(notice,pick(
          'Choose an area and the app will guide each close-up position. Images are captured automatically when the capture checks are ready.',
          'Chọn một vùng da để kiểm tra. Ứng dụng sẽ hướng dẫn từng vị trí và tự động chụp khi hình ảnh đạt yêu cầu.'
        ))
      }

      const setup=root.querySelector('#dermSetup')
      if(setup){
        const eyebrow=setup.querySelector('.eyebrow')
        const name=setup.querySelector('.dermDeviceRow h3')
        const desc=setup.querySelector('.dermDeviceRow p')
        setText(eyebrow,pick('PREPARE SKIN SCOPE','CHUẨN BỊ MÁY SOI'))
        setText(name,'Skin AI Scope')
        setText(desc,pick('Standard setup for this scan','Cấu hình chuẩn cho lần quét này'))
      }

      root.querySelectorAll('.dermRegion').forEach(button=>{
        setAttr(button,'aria-pressed',button.classList.contains('active')?'true':'false')
      })

      setAttr(document.documentElement,'data-dermatoscope-ui-polish-version',VERSION)
    } finally {
      applying=false
    }
  }

  function watch(){
    loadHistoryAssets()
    apply()
    const scan=document.querySelector('#scan')
    if(!scan)return
    let queued=false
    const observer=new MutationObserver(()=>{
      if(queued)return
      queued=true
      requestAnimationFrame(()=>{
        queued=false
        apply()
      })
    })
    observer.observe(scan,{childList:true,subtree:true})
  }

  window.addEventListener('skin-ai:locale-change',()=>requestAnimationFrame(apply))
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>requestAnimationFrame(watch))
  else requestAnimationFrame(watch)
  window.skinDermatoscopeUiPolish={version:VERSION,apply}
})()
