// Mobile Capture Guidance V1.2
// Browser-side guidance only; backend remains authoritative.
// V1.6.0.5: all visible live guidance resolves through active i18n before rendering.
(function(){
  const mobileLike=()=>window.matchMedia('(max-width: 820px)').matches || /iPhone|Android|Mobile/i.test(navigator.userAgent||'')
  const t=en=>{try{return window.skinCaptureI18n?.t?.(en)||window.skinI18n?.t?.(en)||en}catch(_e){return en}}

  const baseEval=window.cgEvaluateMetrics || cgEvaluateMetrics
  window.cgEvaluateMetrics=cgEvaluateMetrics=function(m){
    if(!mobileLike()) return baseEval(m)
    const lighting=(m.mean<42||m.mean>228||m.dark>0.20||m.bright>0.20)?'poor':(m.mean<60||m.mean>210||m.dark>0.10||m.bright>0.10)?'warn':'good'
    // Phone selfie streams are softer after browser scaling/denoising.
    const sharp=m.edge<6?'poor':m.edge<11?'warn':'good'
    return {lighting,sharp}
  }

  const basePreflight=window.cgFriendlyPreflight || cgFriendlyPreflight
  window.cgFriendlyPreflight=cgFriendlyPreflight=function(m){
    if(!mobileLike()) return basePreflight(m)
    const issues=[]
    if(m.sourceWidth<420||m.sourceHeight<420)issues.push({level:'poor',label:t('Low image resolution'),help:t('Use a higher-resolution capture so small skin features are not lost.')})
    if(m.lighting==='poor')issues.push({level:'poor',label:t('Lighting outside preferred range'),help:t('Use more even illumination and avoid very dark or blown-out areas.')})
    else if(m.lighting==='warn')issues.push({level:'warn',label:t('Lighting could be more even'),help:t('Try more neutral, even light before capture.')})
    // Borderline phone sharpness is advisory and should not force a confirmation.
    if(m.sharp==='poor')issues.push({level:'poor',label:t('Image may be blurry'),help:t('Tap the face to refocus and hold steady briefly.')})
    return issues
  }

  window.cgLiveSample=cgLiveSample=function(){
    const video=document.querySelector('#cgVideo'),canvas=document.querySelector('#cgCanvas')
    if(!video||!canvas||video.readyState<2)return
    const w=160,h=Math.max(100,Math.round(160*video.videoHeight/Math.max(1,video.videoWidth)))
    canvas.width=w;canvas.height=h
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(video,0,0,w,h)
    const image=ctx.getImageData(0,0,w,h),m=cgFrameMetrics(image,w,h),q=cgEvaluateMetrics(m)
    cgSetCheck('lighting',q.lighting==='good'?t('Good'):q.lighting==='warn'?t('Adjust'):t('Poor'),q.lighting)
    cgSetCheck('sharpness',q.sharp==='good'?t('Good'):q.sharp==='warn'?t('Usable'):t('Refocus'),q.sharp)

    let stability='warn',label=t('Handheld')
    if(captureGuidePrevFrame && captureGuidePrevFrame.length===m.gray.length){
      let diff=0
      for(let i=0;i<m.gray.length;i+=8)diff+=Math.abs(m.gray[i]-captureGuidePrevFrame[i])
      diff/=Math.max(1,Math.floor(m.gray.length/8))
      if(mobileLike()){
        stability=diff<5?'good':diff<14?'warn':'poor'
        label=stability==='good'?t('Stable'):stability==='warn'?t('Move less'):t('Too much movement')
      }else{
        stability=diff<3.2?'good':diff<7?'warn':'poor'
        label=stability==='good'?t('Stable'):stability==='warn'?t('Hold steady'):t('Too much movement')
      }
    }
    captureGuidePrevFrame=m.gray
    cgSetCheck('stability',label,stability)
  }

  window.addEventListener('skin-ai:locale-change',()=>{
    try{if(document.querySelector('#cgCamera:not(.hidden)'))cgLiveSample()}catch(_e){}
  })
})();