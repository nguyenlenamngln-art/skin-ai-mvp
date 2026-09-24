// V1.5.8.1 — Tester UX polish only. No measurement or access-control changes.
// V1.6.0.4 compatibility: every generated label resolves through active i18n.
(function(){
  const PATCH='1.5.8.1'
  let scheduled=false

  function ui(en){
    try{return window.skinI18n?.t?window.skinI18n.t(en):en}catch(_e){return en}
  }
  function setText(el,en){
    const text=ui(en)
    if(el && el.textContent!==text) el.textContent=text
  }
  function button(label,go){ return `<button type="button" class="primary" data-ux-go="${go}">${ui(label)}</button>` }

  function tuneStudyAccess(){
    const box=document.querySelector('#studyModeV157')
    if(!box)return
    const title=box.querySelector('.studyHeader b')
    const toggle=box.querySelector('.studyToggle span')
    setText(title,'Tester access')
    setText(toggle,'Use study code')
  }

  function tuneCapture(){
    const capture=document.querySelector('#scan .capture')
    if(!capture)return

    const guidance=document.querySelector('#captureGuidanceV2')
    if(guidance){
      const title=guidance.querySelector('.cgHeader b')
      const camera=guidance.querySelector('#cgOpenCamera')
      setText(title,'Take a clear photo')
      setText(camera,'Open camera')
      const head=guidance.querySelector('.cgHeader>div')
      let hint=head?.querySelector('.uxCaptureHint')
      if(head && !hint){
        hint=document.createElement('small')
        hint.className='uxCaptureHint'
        head.appendChild(hint)
      }
      setText(hint,'Camera guidance checks lighting, sharpness and stability before analysis.')
    }

    const uploadTitle=document.querySelector('#uploadTitle')
    if(uploadTitle && typeof scanMode!=='undefined' && scanMode==='rgb') setText(uploadTitle,'Or upload a front-facing photo')
    const uploadHelp=document.querySelector('#uploadHelp')
    if(uploadHelp && typeof scanMode!=='undefined' && scanMode==='rgb') setText(uploadHelp,'Neutral light · no beauty filters · up to 20 MB')

    let advanced=capture.querySelector('#uxAdvancedScanToggle')
    if(!advanced){
      advanced=document.createElement('button')
      advanced.id='uxAdvancedScanToggle'
      advanced.type='button'
      advanced.className='uxAdvancedScanToggle'
      advanced.addEventListener('click',()=>{
        document.body.classList.toggle('uxShowAdvancedScan')
        setText(advanced,document.body.classList.contains('uxShowAdvancedScan')?'Hide advanced settings':'Advanced scan settings')
      })
      const tips=document.querySelector('#captureTips')
      ;(tips||capture.lastElementChild)?.insertAdjacentElement('afterend',advanced)
    }
    setText(advanced,document.body.classList.contains('uxShowAdvancedScan')?'Hide advanced settings':'Advanced scan settings')
  }

  function tuneResult(){
    const details=document.querySelector('.testerTechnical summary')
    if(details){
      const title=details.querySelector('b')
      const sub=details.querySelector('small')
      setText(title,'Advanced details')
      setText(sub,'Measurement and scan-quality details')
    }
  }

  function tuneProgress(){
    const root=document.querySelector('#progressRoot')
    if(!root)return
    const trendGrid=root.querySelector('.pjTrendGrid')
    if(!trendGrid)return
    const cards=[...trendGrid.querySelectorAll('.pjTrendCard')]
    const allEmpty=cards.length===3 && cards.every(card=>card.querySelector('.pjTrendEmpty'))
    const section=trendGrid.closest('.pjSection')
    if(allEmpty && section && !root.querySelector('.uxBaselineNext')){
      const callout=document.createElement('section')
      callout.className='uxBaselineNext card'
      callout.innerHTML=`<div><span class="eyebrow">${ui('WHAT HAPPENS NEXT')}</span><h3>${ui('Your baseline is saved')}</h3><p>${ui('Take another comparable scan later to unlock before/after comparison and trend charts.')}</p></div>${button('Take another scan','scan')}`
      section.replaceWith(callout)
    }
  }

  function tuneJourney(){
    const root=document.querySelector('#journeyRoot')
    if(!root)return
    const items=root.querySelectorAll('.pjTimelineItem')
    if(items.length===1 && !root.querySelector('.uxJourneyNext')){
      const next=document.createElement('section')
      next.className='uxJourneyNext card'
      next.innerHTML=`<div><span class="eyebrow">${ui('NEXT MILESTONE')}</span><h3>${ui('Add your second comparable scan')}</h3><p>${ui('With two scans, Journey can start showing visible changes from your personal baseline.')}</p></div>${button('Take another scan','scan')}`
      root.appendChild(next)
    }
  }

  function bindNavigation(){
    document.querySelectorAll('[data-ux-go]').forEach(el=>{
      if(el.dataset.uxBound==='1')return
      el.dataset.uxBound='1'
      el.addEventListener('click',()=>{ if(typeof setTab==='function') setTab(el.dataset.uxGo) })
    })
  }

  function enhance(){
    scheduled=false
    document.body.classList.add('uxV1581')
    document.documentElement.dataset.uxPatch=PATCH
    tuneStudyAccess();tuneCapture();tuneResult();tuneProgress();tuneJourney();bindNavigation()
  }
  function schedule(){
    if(scheduled)return
    scheduled=true
    requestAnimationFrame(enhance)
  }

  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true})
  document.addEventListener('click',event=>{
    if(event.target.closest('[data-tab],[data-go],[data-result-view],#uxAdvancedScanToggle')) setTimeout(schedule,0)
  })
  window.addEventListener('skin-ai:locale-change',schedule)
  setTimeout(enhance,0)
})()
