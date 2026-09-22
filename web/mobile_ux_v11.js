// Mobile UX V1.1
(function(){
  const isPhone=()=>window.matchMedia('(max-width: 820px)').matches

  function applyEngineAvailability(){
    const uvButton=document.querySelector('[data-mode="uv"]')
    const rgbReady=typeof health!=='undefined' && health?.rgb_engine_available===true
    const uvReady=typeof health!=='undefined' && health?.uv_model_available===true
    if(uvButton && (rgbReady||uvReady)){
      uvButton.disabled=!uvReady
      uvButton.title=uvReady?'UV fluorescence analysis ready':'UV model checkpoint is not provisioned on this deployment yet.'
      uvButton.style.opacity=uvReady?'':'0.48'
      uvButton.style.cursor=uvReady?'':'not-allowed'
    }
    if(rgbReady && !uvReady && typeof scanMode!=='undefined' && scanMode==='uv'){
      scanMode='rgb'
    }
  }

  function refreshReadyStatus(){
    const el=document.querySelector('#status')
    if(!el) return
    const rgbReady=typeof health!=='undefined' && health?.rgb_engine_available===true
    const uvReady=typeof health!=='undefined' && health?.uv_model_available===true
    if(rgbReady||uvReady){
      el.textContent=rgbReady&&uvReady?'UV + RGB ready':rgbReady?'RGB ready · UV unavailable':'UV ready · RGB unavailable'
      el.className=`status ${rgbReady?'ready':'warn'}`
    }
    if(isPhone()) el.classList.add('mobileReadyStatus')
    else el.classList.remove('mobileReadyStatus')
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

  document.addEventListener('click',e=>{
    if(e.target.closest('[data-tab],[data-go]')) setTimeout(refreshScanJump,0)
  })
  window.addEventListener('scroll',()=>requestAnimationFrame(refreshScanJump),{passive:true})
  window.addEventListener('resize',()=>{refreshReadyStatus();refreshScanJump()})

  if(typeof renderResult==='function'){
    const oldRenderResult=renderResult
    renderResult=function(){
      oldRenderResult()
      applyEngineAvailability()
      refreshReadyStatus()
      setTimeout(refreshScanJump,0)
    }
  }
  if(typeof applyModeUI==='function'){
    const oldApply=applyModeUI
    applyModeUI=function(){
      applyEngineAvailability()
      oldApply()
      applyEngineAvailability()
      refreshReadyStatus()
      setTimeout(refreshScanJump,0)
    }
  }

  // Mobile Camera Quality V1 — phone video previews are softer and auto-exposure
  // changes can look like motion. Keep the live checks advisory and use the
  // native full-resolution still camera for the actual RGB capture.
  let mobileStabilityEma=null

  if(typeof cgEvaluateMetrics==='function'){
    const baseEvaluateMetrics=cgEvaluateMetrics
    cgEvaluateMetrics=function(m){
      if(!isPhone() || typeof scanMode==='undefined' || scanMode!=='rgb') return baseEvaluateMetrics(m)
      const lighting=(m.mean<42||m.mean>228||m.dark>0.20||m.bright>0.20)?'poor':(m.mean<60||m.mean>210||m.dark>0.10||m.bright>0.10)?'warn':'good'
      const sharp=m.edge<4.5?'poor':m.edge<9?'warn':'good'
      return {lighting,sharp}
    }
  }

  if(typeof cgLiveSample==='function'){
    const baseLiveSample=cgLiveSample
    cgLiveSample=function(){
      if(!isPhone() || typeof scanMode==='undefined' || scanMode!=='rgb') return baseLiveSample()
      const video=document.querySelector('#cgVideo'),canvas=document.querySelector('#cgCanvas')
      if(!video||!canvas||video.readyState<2)return
      const w=192,h=Math.max(120,Math.round(192*video.videoHeight/Math.max(1,video.videoWidth)))
      canvas.width=w;canvas.height=h
      const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(video,0,0,w,h)
      const image=ctx.getImageData(0,0,w,h),m=cgFrameMetrics(image,w,h),q=cgEvaluateMetrics(m)
      cgSetCheck('lighting',cgStatusText(q.lighting,'Good','Adjust','Poor'),q.lighting)
      cgSetCheck('sharpness',cgStatusText(q.sharp,'Good','Almost ready','Refocus'),q.sharp)

      let stability='warn',label='Hold briefly'
      if(captureGuidePrevFrame && captureGuidePrevFrame.length===m.gray.length){
        let deltaSum=0,count=0
        for(let i=0;i<m.gray.length;i+=8){deltaSum+=m.gray[i]-captureGuidePrevFrame[i];count++}
        const exposureShift=deltaSum/Math.max(1,count)
        let motion=0
        for(let i=0;i<m.gray.length;i+=8) motion+=Math.abs((m.gray[i]-captureGuidePrevFrame[i])-exposureShift)
        motion/=Math.max(1,count)
        mobileStabilityEma=mobileStabilityEma==null?motion:(0.65*mobileStabilityEma+0.35*motion)
        stability=mobileStabilityEma<5.5?'good':mobileStabilityEma<10?'warn':'poor'
        label=stability==='good'?'Stable':stability==='warn'?'Hold briefly':'Too much movement'
      }else{
        mobileStabilityEma=null
      }
      captureGuidePrevFrame=m.gray
      cgSetCheck('stability',label,stability)
    }
  }

  function ensureMobileStillInput(){
    let input=document.querySelector('#cgMobileStillInput')
    if(input) return input
    input=document.createElement('input')
    input.id='cgMobileStillInput'
    input.type='file'
    input.accept='image/*'
    input.setAttribute('capture','user')
    input.className='hidden'
    input.onchange=async e=>{
      const file=e.target.files?.[0]
      e.target.value=''
      if(!file)return
      if(typeof cgStopCamera==='function')cgStopCamera()
      if(typeof cgHandleFile==='function')await cgHandleFile(file)
    }
    document.body.appendChild(input)
    return input
  }

  if(typeof cgCaptureFrame==='function'){
    const baseCaptureFrame=cgCaptureFrame
    cgCaptureFrame=async function(){
      if(isPhone() && typeof scanMode!=='undefined' && scanMode==='rgb'){
        const input=ensureMobileStillInput()
        if(typeof cgStopCamera==='function')cgStopCamera()
        input.click()
        return
      }
      return baseCaptureFrame()
    }
  }

  function patchMobileCaptureButton(){
    const button=document.querySelector('#cgCapture')
    if(button && typeof cgCaptureFrame==='function'){
      button.onclick=cgCaptureFrame
      if(isPhone() && typeof scanMode!=='undefined' && scanMode==='rgb') button.textContent='Take full-resolution photo'
      else button.textContent='Capture photo'
    }
    const camera=document.querySelector('#cgCamera')
    if(camera && isPhone() && typeof scanMode!=='undefined' && scanMode==='rgb'){
      const note=camera.querySelector(':scope > small')
      if(note) note.textContent='Live checks are advisory. Tap Take full-resolution photo to open your phone camera; the backend performs the final quality check.'
    }
  }

  document.addEventListener('click',e=>{
    if(e.target.closest('[data-mode],#cgOpenCamera')) setTimeout(patchMobileCaptureButton,80)
  })
  setTimeout(patchMobileCaptureButton,100)
  setTimeout(patchMobileCaptureButton,500)

  applyEngineAvailability()
  refreshReadyStatus()
  refreshScanJump()
})();
