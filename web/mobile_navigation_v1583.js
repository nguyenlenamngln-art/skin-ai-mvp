// V1.5.8.3 — Mobile Navigation & Capture UX
// Presentation only. RGB engine V1.5.2, Capture Protocol V1.4 and study access remain unchanged.
(function(){
  const VERSION='1.5.8.3'
  const isPhone=()=>window.matchMedia('(max-width: 820px)').matches
  const titles={home:'Your skin today',progress:'Your progress',scan:'Take a skin scan',routine:'Your routine',journey:'Your journey'}
  const navLabels={home:'Today',progress:'Progress',scan:'+ Scan',routine:'Routine',journey:'Journey'}
  let scheduled=false

  function activeTab(){
    return document.querySelector('main>.view.active')?.id || 'home'
  }
  function syncTitle(tab=activeTab()){
    const el=document.querySelector('#title')
    if(el && titles[tab] && el.textContent!==titles[tab]) el.textContent=titles[tab]
  }
  function syncNavigation(){
    document.querySelectorAll('aside nav [data-tab]').forEach(button=>{
      const label=navLabels[button.dataset.tab]
      if(label && button.textContent!==label) button.textContent=label
      button.setAttribute('aria-label',button.dataset.tab==='scan'?'Take a skin scan':label||button.dataset.tab)
    })
  }
  function simplifyCapture(){
    if(!isPhone())return
    const jump=document.querySelector('#mobileScanJump')
    if(jump) jump.remove()
    document.querySelector('#scan')?.classList.remove('mobileJumpActive')

    const guide=document.querySelector('#captureGuidanceV2')
    if(guide){
      const title=guide.querySelector('.cgHeader b')
      if(title && title.textContent!=='Take a clear photo') title.textContent='Take a clear photo'
      const camera=guide.querySelector('#cgOpenCamera')
      if(camera && camera.textContent!=='Open camera') camera.textContent='Open camera'
      let hint=guide.querySelector('.uxCaptureHint')
      if(!hint){
        hint=document.createElement('small')
        hint.className='uxCaptureHint'
        guide.querySelector('.cgHeader>div')?.appendChild(hint)
      }
      if(hint && hint.textContent!=='Even light · Face centered · Hold steady') hint.textContent='Even light · Face centered · Hold steady'
    }

    const uploadTitle=document.querySelector('#uploadTitle')
    if(uploadTitle && typeof scanMode!=='undefined' && scanMode==='rgb' && uploadTitle.textContent!=='Or upload a photo') uploadTitle.textContent='Or upload a photo'
    const uploadHelp=document.querySelector('#uploadHelp')
    if(uploadHelp && typeof scanMode!=='undefined' && scanMode==='rgb' && uploadHelp.textContent!=='Neutral light · no beauty filters') uploadHelp.textContent='Neutral light · no beauty filters'
    const choose=document.querySelector('#dropContent .choose')
    if(choose && choose.textContent!=='Choose photo') choose.textContent='Choose photo'
    const tips=document.querySelector('#captureTips')
    if(tips && typeof scanMode!=='undefined' && scanMode==='rgb') tips.innerHTML='<span>For repeat scans, use similar lighting, distance and angle.</span>'
  }
  function simplifyStudyAccess(){
    if(!isPhone())return
    const study=document.querySelector('#studyModeV157')
    if(!study)return
    const header=study.querySelector('.studyHeader')
    if(header) header.setAttribute('aria-label','Optional tester study access')
  }
  function mobileEnhance(){
    scheduled=false
    document.body.classList.toggle('mobileV1583',isPhone())
    document.documentElement.dataset.mobileUxVersion=VERSION
    syncNavigation();syncTitle();simplifyCapture();simplifyStudyAccess()
  }
  function schedule(){
    if(scheduled)return
    scheduled=true
    requestAnimationFrame(mobileEnhance)
  }

  if(typeof setTab==='function'){
    const baseSetTab=setTab
    setTab=function(tab){
      baseSetTab(tab)
      syncTitle(tab)
      simplifyCapture()
      window.scrollTo({top:0,behavior:'smooth'})
    }
  }
  if(typeof applyModeUI==='function'){
    const baseApplyModeUI=applyModeUI
    applyModeUI=function(){
      baseApplyModeUI()
      simplifyCapture()
      syncTitle(activeTab())
    }
  }

  document.addEventListener('click',event=>{
    if(event.target.closest('[data-tab],[data-go],[data-mode],#cgOpenCamera,#cgCancelCamera')) setTimeout(schedule,0)
  })
  window.addEventListener('resize',schedule)
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true})
  setTimeout(mobileEnhance,0)
})()
