// Mobile Capture Guidance V1.2
// Browser-side guidance only; backend remains authoritative.
(function(){
  const mobileLike=()=>window.matchMedia('(max-width: 820px)').matches || /iPhone|Android|Mobile/i.test(navigator.userAgent||'')

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
    if(m.sourceWidth<420||m.sourceHeight<420)issues.push({level:'poor',label:'Low image resolution',help:'Use a higher-resolution capture so small skin features are not lost.'})
    if(m.lighting==='poor')issues.push({level:'poor',label:'Lighting outside preferred range',help:'Use more even illumination and avoid very dark or blown-out areas.'})
    else if(m.lighting==='warn')issues.push({level:'warn',label:'Lighting could be more even',help:'Try more neutral, even light before capture.'})
    // Borderline phone sharpness is advisory and should not force a confirmation.
    if(m.sharp==='poor')issues.push({level:'poor',label:'Image may be blurry',help:'Tap the face to refocus and hold steady briefly.'})
    return issues
  }

  window.cgLiveSample=cgLiveSample=function(){
    const video=document.querySelector('#cgVideo'),canvas=document.querySelector('#cgCanvas')
    if(!video||!canvas||video.readyState<2)return
    const w=160,h=Math.max(100,Math.round(160*video.videoHeight/Math.max(1,video.videoWidth)))
    canvas.width=w;canvas.height=h
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(video,0,0,w,h)
    const image=ctx.getImageData(0,0,w,h),m=cgFrameMetrics(image,w,h),q=cgEvaluateMetrics(m)
    cgSetCheck('lighting',cgStatusText(q.lighting,'Good','Adjust','Poor'),q.lighting)
    cgSetCheck('sharpness',q.sharp==='good'?'Good':q.sharp==='warn'?'Usable':'Refocus',q.sharp)

    let stability='warn',label='Handheld'
    if(captureGuidePrevFrame && captureGuidePrevFrame.length===m.gray.length){
      let diff=0
      for(let i=0;i<m.gray.length;i+=8)diff+=Math.abs(m.gray[i]-captureGuidePrevFrame[i])
      diff/=Math.max(1,Math.floor(m.gray.length/8))
      if(mobileLike()){
        stability=diff<5?'good':diff<14?'warn':'poor'
        label=stability==='good'?'Stable':stability==='warn'?'Handheld':'Too much movement'
      }else{
        stability=diff<3.2?'good':diff<7?'warn':'poor'
        label=stability==='good'?'Stable':stability==='warn'?'Hold steady':'Too much movement'
      }
    }
    captureGuidePrevFrame=m.gray
    cgSetCheck('stability',label,stability)
  }
})();
