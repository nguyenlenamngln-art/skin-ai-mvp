// V1.7.5 — post-capture registration feedback & guided retake.
(function(){
  const VERSION='1.7.5'
  const originalFetch=window.fetch.bind(window)
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const tr=(en,vi)=>locale()==='vi'?vi:en
  let installed=false

  function speak(en,vi){
    try{
      if(!document.querySelector('#dermAudioToggle')?.checked||!('speechSynthesis' in window))return
      speechSynthesis.cancel()
      const u=new SpeechSynthesisUtterance(tr(en,vi));u.lang=locale()==='vi'?'vi-VN':'en-US';u.rate=.95;speechSynthesis.speak(u)
    }catch(_e){}
  }

  function ensureRetakePanel(){
    const side=document.querySelector('#dermV171 .dermCaptureSide')
    if(!side)return null
    let panel=document.querySelector('#dermRetakePanel')
    if(panel)return panel
    panel=document.createElement('div')
    panel.id='dermRetakePanel'
    panel.className='dermRetakePanel'
    panel.hidden=true
    panel.innerHTML=`<div class="dermRetakeIcon">↻</div><div><strong id="dermRetakeTitle"></strong><p id="dermRetakeCopy"></p></div>`
    const status=side.querySelector('.dermStatus')
    if(status)status.insertAdjacentElement('afterend',panel);else side.appendChild(panel)
    return panel
  }

  function showRetake(detail){
    const panel=ensureRetakePanel();if(!panel)return
    const score=Number.isFinite(Number(detail?.score))?Math.round(Number(detail.score)):null
    panel.hidden=false
    panel.dataset.state='required'
    panel.querySelector('#dermRetakeTitle').textContent=tr('Retake this position','Chụp lại vị trí này')
    panel.querySelector('#dermRetakeCopy').textContent=score===null
      ?tr('The captured image did not match the saved skin position closely enough. Reposition and hold still for another automatic capture.','Ảnh vừa chụp chưa khớp đủ gần với vị trí da đã lưu. Hãy đưa máy về đúng vị trí hơn và giữ yên để chụp lại tự động.')
      :tr(`Position match was ${score}%. Reposition and hold still for another automatic capture.`,`Mức khớp vị trí là ${score}%. Hãy điều chỉnh lại vị trí và giữ yên để chụp lại tự động.`)
    const status=document.querySelector('#dermStatus')
    if(status)status.textContent=tr('Retake required — return to the saved position.','Cần chụp lại — hãy trở về vị trí đã lưu.')
    const bar=document.querySelector('#dermHoldBar');if(bar)bar.style.width='0%'
    try{window.skinDermatoscopeLiveGuidance?.reset?.();window.skinDermatoscopeLiveGuidance?.sample?.()}catch(_e){}
    speak('Please retake this position. Move back toward the saved skin area.','Vui lòng chụp lại vị trí này. Hãy di chuyển về gần vùng da đã lưu.')
  }

  function clearRetake(){
    const panel=document.querySelector('#dermRetakePanel');if(panel)panel.hidden=true
  }

  function isCapturePost(input,init){
    const url=typeof input==='string'?input:(input?.url||'')
    const method=(init?.method||input?.method||'GET').toUpperCase()
    return method==='POST'&&/\/v1\/dermatoscope\/captures(?:\?|$)/.test(url)
  }

  async function validateCapture(captureId){
    const r=await originalFetch(`/v1/dermatoscope/captures/${encodeURIComponent(captureId)}/validate-position?subject_key=my_profile`,{method:'POST',cache:'no-store'})
    if(!r.ok)throw new Error(`position validation ${r.status}`)
    return r.json()
  }

  function install(){
    if(installed)return;installed=true
    ensureRetakePanel()
    window.fetch=async function(input,init){
      if(!isCapturePost(input,init))return originalFetch(input,init)
      const response=await originalFetch(input,init)
      if(!response.ok)return response
      let capture
      try{capture=await response.clone().json()}catch(_e){return response}
      if(!capture?.id)return response
      let validation
      try{validation=await validateCapture(capture.id)}catch(_e){
        // Validation failure must never trap the user; normal capture flow continues.
        return response
      }
      if(validation?.retake_required){
        window.dispatchEvent(new CustomEvent('skin-ai:dermatoscope-retake-required',{detail:validation}))
        throw new Error('dermatoscope_position_retake_required')
      }
      clearRetake()
      window.dispatchEvent(new CustomEvent('skin-ai:dermatoscope-position-accepted',{detail:validation}))
      return response
    }
    window.addEventListener('skin-ai:dermatoscope-retake-required',event=>setTimeout(()=>showRetake(event.detail),0))
    window.addEventListener('skin-ai:dermatoscope-position-accepted',()=>setTimeout(clearRetake,0))
    document.addEventListener('click',event=>{
      if(event.target.closest?.('[data-derm-region],#dermAgain,#dermCancel'))clearRetake()
    })
    document.documentElement.dataset.dermatoscopePostCaptureVersion=VERSION
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install()
  window.skinDermatoscopePostCapture={version:VERSION,install,showRetake,clearRetake}
})()
