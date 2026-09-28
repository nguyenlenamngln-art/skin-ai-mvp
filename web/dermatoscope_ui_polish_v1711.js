// V1.7.1.1 — consumer-facing close-up scan copy/branding polish.
(function(){
  const VERSION='1.7.1.1'
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const pick=(en,vi)=>locale()==='vi'?vi:en

  function apply(){
    const root=document.querySelector('#dermV171')
    if(!root)return

    const intro=root.querySelector('.dermIntroCard')
    if(intro){
      const eyebrow=intro.querySelector('.eyebrow')
      const title=intro.querySelector('h2')
      const notice=intro.querySelector('.dermNotice')
      if(eyebrow)eyebrow.textContent=pick('CLOSE-UP SKIN SCAN','QUÉT DA CẬN CẢNH')
      if(title)title.textContent=pick('Choose a skin area to examine','Chọn vùng da cần kiểm tra')
      if(notice)notice.textContent=pick(
        'Choose an area and the app will guide each close-up position. Images are captured automatically when the capture checks are ready.',
        'Chọn một vùng da để kiểm tra. Ứng dụng sẽ hướng dẫn từng vị trí và tự động chụp khi hình ảnh đạt yêu cầu.'
      )
    }

    const setup=root.querySelector('#dermSetup')
    if(setup){
      const eyebrow=setup.querySelector('.eyebrow')
      const name=setup.querySelector('.dermDeviceRow h3')
      const desc=setup.querySelector('.dermDeviceRow p')
      if(eyebrow)eyebrow.textContent=pick('PREPARE SKIN SCOPE','CHUẨN BỊ MÁY SOI')
      if(name)name.textContent='Skin AI Scope'
      if(desc)desc.textContent=pick('Standard setup for this scan','Cấu hình chuẩn cho lần quét này')
    }

    root.querySelectorAll('.dermRegion').forEach(button=>{
      button.setAttribute('aria-pressed',button.classList.contains('active')?'true':'false')
    })

    document.documentElement.dataset.dermatoscopeUiPolishVersion=VERSION
  }

  function watch(){
    apply()
    const scan=document.querySelector('#scan')
    if(!scan)return
    const observer=new MutationObserver(()=>apply())
    observer.observe(scan,{childList:true,subtree:true})
  }

  window.addEventListener('skin-ai:locale-change',()=>setTimeout(apply,0))
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(watch,0))
  else setTimeout(watch,0)
  window.skinDermatoscopeUiPolish={version:VERSION,apply}
})()
