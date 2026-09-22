// Mobile UX V1.1
(function(){
  const isPhone=()=>window.matchMedia('(max-width: 820px)').matches

  function refreshReadyStatus(){
    const el=document.querySelector('#status')
    if(!el) return
    if(isPhone()){
      el.classList.add('mobileReadyStatus')
      if(/ready/i.test(el.textContent||'')) el.textContent='Analysis ready'
    }else{
      el.classList.remove('mobileReadyStatus')
    }
  }

  function ensureScanJump(){
    let bar=document.querySelector('#mobileScanJump')
    const scan=document.querySelector('#scan')
    if(!scan) return null
    if(!bar){
      bar=document.createElement('div')
      bar.id='mobileScanJump'
      bar.className='mobileScanJump hidden'
      bar.innerHTML='<button type="button" data-mobile-jump="capture" class="active">Back to capture</button><button type="button" data-mobile-jump="result">View result</button>'
      document.body.appendChild(bar)
      bar.querySelector('[data-mobile-jump="capture"]').onclick=()=>{
        document.querySelector('.capture')?.scrollIntoView({behavior:'smooth',block:'start'})
        setJumpActive('capture')
      }
      bar.querySelector('[data-mobile-jump="result"]').onclick=()=>{
        document.querySelector('.result')?.scrollIntoView({behavior:'smooth',block:'start'})
        setJumpActive('result')
      }
    }
    return bar
  }

  function setJumpActive(which){
    document.querySelectorAll('#mobileScanJump [data-mobile-jump]').forEach(btn=>btn.classList.toggle('active',btn.dataset.mobileJump===which))
  }

  function resultIsMeaningful(){
    if(typeof rejectedAttempt!=='undefined' && rejectedAttempt) return true
    if(typeof latest!=='undefined' && latest && latest.modality===scanMode) return true
    const body=document.querySelector('#resultBody')
    return !!(body && !body.classList.contains('resultEmpty') && !body.classList.contains('empty'))
  }

  function refreshScanJump(){
    const bar=ensureScanJump(), scan=document.querySelector('#scan')
    if(!bar||!scan) return
    const show=isPhone() && scan.classList.contains('active') && resultIsMeaningful()
    bar.classList.toggle('hidden',!show)
    scan.classList.toggle('mobileJumpActive',show)
    if(!show) return
    const capture=document.querySelector('.capture'), result=document.querySelector('.result')
    if(capture && result){
      const midpoint=window.innerHeight*0.48
      const resultTop=result.getBoundingClientRect().top
      setJumpActive(resultTop<midpoint?'result':'capture')
    }
  }

  // Track tab switches without changing the existing router.
  document.addEventListener('click',e=>{
    if(e.target.closest('[data-tab],[data-go]')) setTimeout(refreshScanJump,0)
  })
  window.addEventListener('scroll',()=>requestAnimationFrame(refreshScanJump),{passive:true})
  window.addEventListener('resize',()=>{refreshReadyStatus();refreshScanJump()})

  // Existing render/apply hooks are deliberately wrapped only for presentation refreshes.
  if(typeof renderResult==='function'){
    const oldRenderResult=renderResult
    renderResult=function(){
      oldRenderResult()
      refreshReadyStatus()
      setTimeout(refreshScanJump,0)
    }
  }
  if(typeof applyModeUI==='function'){
    const oldApply=applyModeUI
    applyModeUI=function(){
      oldApply()
      refreshReadyStatus()
      setTimeout(refreshScanJump,0)
    }
  }

  refreshReadyStatus()
  refreshScanJump()
})();
