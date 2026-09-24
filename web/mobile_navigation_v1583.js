// V1.5.8.3 — Mobile Navigation & Capture UX
// Presentation only. RGB engine V1.5.2, Capture Protocol V1.4 and study access remain unchanged.
(function(){
  const VERSION='1.5.8.3'
  const isPhone=()=>window.matchMedia('(max-width: 820px)').matches
  const titles={home:'Your skin today',progress:'Your progress',scan:'Take a skin scan',routine:'Your routine',journey:'Your journey'}
  const navLabels={home:'Today',progress:'Progress',scan:'+ Scan',routine:'Routine',journey:'Journey'}
  let scheduled=false

  function ui(en){
    try{return window.skinI18n?.t?window.skinI18n.t(en):en}catch(_e){return en}
  }
  function activeTab(){
    return document.querySelector('main>.view.active')?.id || 'home'
  }
  function syncTitle(tab=activeTab()){
    const el=document.querySelector('#title')
    const target=titles[tab]?ui(titles[tab]):''
    if(el && target && el.textContent!==target) el.textContent=target
  }
  function syncNavigation(){
    document.querySelectorAll('aside nav [data-tab]').forEach(button=>{
      const label=navLabels[button.dataset.tab]
      const target=label?ui(label):''
      if(target && button.textContent!==target) button.textContent=target
      const aria=button.dataset.tab==='scan'?ui('Take a skin scan'):(target||button.dataset.tab)
      if(button.getAttribute('aria-label')!==aria) button.setAttribute('aria-label',aria)
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
      const titleText=ui('Take a clear photo')
      if(title && title.textContent!==titleText) title.textContent=titleText
      const camera=guide.querySelector('#cgOpenCamera')
      const cameraText=ui('Open camera')
      if(camera && camera.textContent!==cameraText) camera.textContent=cameraText
      let hint=guide.querySelector('.uxCaptureHint')
      if(!hint){
        hint=document.createElement('small')
        hint.className='uxCaptureHint'
        guide.querySelector('.cgHeader>div')?.appendChild(hint)
      }
      const hintText=ui('Even light · Face centered · Hold steady')
      if(hint && hint.textContent!==hintText) hint.textContent=hintText
    }

    const uploadTitle=document.querySelector('#uploadTitle')
    const uploadTitleText=ui('Or upload a photo')
    if(uploadTitle && typeof scanMode!=='undefined' && scanMode==='rgb' && uploadTitle.textContent!==uploadTitleText) uploadTitle.textContent=uploadTitleText
    const uploadHelp=document.querySelector('#uploadHelp')
    const uploadHelpText=ui('Neutral light · no beauty filters')
    if(uploadHelp && typeof scanMode!=='undefined' && scanMode==='rgb' && uploadHelp.textContent!==uploadHelpText) uploadHelp.textContent=uploadHelpText
    const choose=document.querySelector('#dropContent .choose')
    const chooseText=ui('Choose photo')
    if(choose && choose.textContent!==chooseText) choose.textContent=chooseText
    const tips=document.querySelector('#captureTips')
    if(tips && typeof scanMode!=='undefined' && scanMode==='rgb'){
      const tip=ui('For repeat scans, use similar lighting, distance and angle.')
      const current=tips.querySelector('span')?.textContent||''
      if(current!==tip) tips.innerHTML=`<span>${tip}</span>`
    }
  }
  function simplifyStudyAccess(){
    if(!isPhone())return
    const study=document.querySelector('#studyModeV157')
    if(!study)return
    const header=study.querySelector('.studyHeader')
    if(header){
      const label=ui('Optional tester study access')
      if(header.getAttribute('aria-label')!==label) header.setAttribute('aria-label',label)
    }
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
  window.addEventListener('skin-ai:locale-change',schedule)
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true})
  setTimeout(mobileEnhance,0)
})()
