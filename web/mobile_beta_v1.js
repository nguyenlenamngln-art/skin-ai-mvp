// Mobile Capture & Beta Readiness V1
(function(){
  const isPhone=()=>window.matchMedia('(max-width: 820px)').matches
  document.documentElement.classList.toggle('mobileBeta',isPhone())
  window.addEventListener('resize',()=>document.documentElement.classList.toggle('mobileBeta',isPhone()))

  if('serviceWorker' in navigator){
    window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}))
  }

  function mobileModeHint(){
    let el=document.querySelector('#mobileCaptureHint')
    const capture=document.querySelector('.capture')
    if(!capture) return
    if(!el){
      el=document.createElement('div')
      el.id='mobileCaptureHint'
      el.className='mobileCaptureHint'
      capture.querySelector('.modes')?.insertAdjacentElement('afterend',el)
    }
    if(!isPhone()){el.classList.add('hidden');return}
    el.classList.remove('hidden')
    el.innerHTML=scanMode==='rgb'
      ? '<b>Phone capture ready</b><span>Hold reasonably steady, use even light, and keep the face centered. Live sharpness/stability are guidance only.</span>'
      : '<b>UV mobile workflow</b><span>Upload a supported UV fluorescence image or connect a compatible external UV camera.</span>'
  }

  const oldApply=applyModeUI
  applyModeUI=function(){oldApply();mobileModeHint()}
  mobileModeHint()

  // Mobile Capture Calibration V1.2: the live browser checks are deliberately
  // forgiving for handheld selfie cameras. They never disable Capture photo.
  if(typeof cgEvaluateMetrics==='function'){
    cgEvaluateMetrics=function(m){
      const lighting=(m.mean<38||m.mean>232||m.dark>0.24||m.bright>0.24)?'poor':(m.mean<55||m.mean>215||m.dark>0.12||m.bright>0.12)?'warn':'good'
      const sharp=m.edge<6?'poor':m.edge<11?'warn':'good'
      return {lighting,sharp}
    }
  }

  if(typeof cgLiveSample==='function'){
    cgLiveSample=function(){
      const video=document.querySelector('#cgVideo'),canvas=document.querySelector('#cgCanvas')
      if(!video||!canvas||video.readyState<2)return
      const w=160,h=Math.max(100,Math.round(160*video.videoHeight/Math.max(1,video.videoWidth)))
      canvas.width=w;canvas.height=h
      const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(video,0,0,w,h)
      const image=ctx.getImageData(0,0,w,h),m=cgFrameMetrics(image,w,h),q=cgEvaluateMetrics(m)
      cgSetCheck('lighting',cgStatusText(q.lighting,'Good','Adjust','Poor'),q.lighting)
      cgSetCheck('sharpness',cgStatusText(q.sharp,'Good','Usable','Refocus'),q.sharp)
      let stability='warn',label='Handheld'
      if(captureGuidePrevFrame && captureGuidePrevFrame.length===m.gray.length){
        let diff=0;for(let i=0;i<m.gray.length;i+=8)diff+=Math.abs(m.gray[i]-captureGuidePrevFrame[i])
        diff/=Math.max(1,Math.floor(m.gray.length/8))
        stability=diff<5.5?'good':diff<12?'warn':'poor'
        label=stability==='good'?'Stable':stability==='warn'?'Handheld':'Move less'
      }
      captureGuidePrevFrame=m.gray
      cgSetCheck('stability',label,stability)
    }
  }

  // Prevent accidental double-taps on primary capture actions while a request is running.
  document.addEventListener('click',e=>{
    const btn=e.target.closest('#cgCapture,#cgConfirmUvCamera')
    if(!btn||btn.disabled)return
    btn.dataset.mobilePressed='1'
    setTimeout(()=>{if(btn)delete btn.dataset.mobilePressed},900)
  })
})();
