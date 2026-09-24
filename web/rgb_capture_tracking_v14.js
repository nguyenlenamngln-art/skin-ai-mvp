// RGB Capture & Tracking V1.4
(function(){
  let distanceTimer=null
  let distanceBusy=false
  let defaultProfileId=''
  const t=en=>{try{return window.skinCaptureI18n?.t?.(en)||window.skinI18n?.t?.(en)||en}catch(_e){return en}}

  function isRgb(){ return typeof scanMode!=='undefined' && scanMode==='rgb' }

  function ensureDistanceCell(){
    const checks=document.querySelector('.cgLiveChecks')
    if(!checks) return
    let cell=checks.querySelector('[data-cg-check="distance"]')
    if(!cell){
      cell=checks.querySelector('.visual') || document.createElement('div')
      if(!cell.parentNode) checks.appendChild(cell)
      cell.classList.remove('visual')
      cell.dataset.cgCheck='distance'
      cell.innerHTML=`<span>${t('Distance')}</span><b>${t('Checking…')}</b>`
    }else{
      const span=cell.querySelector('span');if(span)span.textContent=t('Distance')
    }
    const note=document.querySelector('#cgCamera > small')
    if(note && isRgb()) note.textContent=t('Lighting, sharpness and stability are browser estimates. Distance uses a temporary low-resolution server check with the same face detector as analysis; preview frames are not saved.')
  }

  function setDistance(label,state){
    if(typeof cgSetCheck==='function') cgSetCheck('distance',t(label),state)
  }

  async function sampleDistance(){
    if(distanceBusy || !isRgb()) return
    const video=document.querySelector('#cgVideo')
    if(!video || video.readyState<2 || !video.videoWidth || !video.videoHeight) return
    distanceBusy=true
    try{
      const w=320, scale=w/video.videoWidth, h=Math.max(180,Math.round(video.videoHeight*scale))
      const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h
      canvas.getContext('2d').drawImage(video,0,0,w,h)
      const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',0.72))
      if(!blob) return
      const fd=new FormData();fd.append('image',blob,'distance-check.jpg')
      const r=await fetch('/v1/rgb/capture-check',{method:'POST',body:fd})
      const data=await r.json().catch(()=>({}))
      if(!r.ok) throw new Error('distance check failed')
      if(!data.face_detected) setDistance('Center face','warn')
      else if(data.distance_state==='good') setDistance('Distance good','good')
      else if(data.distance_state==='move_back') setDistance('Move back','warn')
      else setDistance('Move closer','warn')
    }catch(_e){
      setDistance('Use face guide','warn')
    }finally{distanceBusy=false}
  }

  function stopDistance(){if(distanceTimer){clearInterval(distanceTimer);distanceTimer=null}distanceBusy=false}
  function startDistance(){stopDistance();ensureDistanceCell();if(!isRgb())return;setDistance('Checking…','warn');setTimeout(sampleDistance,250);distanceTimer=setInterval(sampleDistance,950)}

  if(typeof cgStartCamera==='function'){
    const baseStart=cgStartCamera
    cgStartCamera=async function(){const out=await baseStart();ensureDistanceCell();startDistance();return out}
    window.cgStartCamera=cgStartCamera
  }
  if(typeof cgStopCamera==='function'){
    const baseStop=cgStopCamera
    cgStopCamera=function(){stopDistance();return baseStop()}
    window.cgStopCamera=cgStopCamera
  }

  function wireCameraButton(){
    ensureDistanceCell()
    const open=document.querySelector('#cgOpenCamera'),cancel=document.querySelector('#cgCancelCamera'),capture=document.querySelector('#cgCapture')
    if(open&&typeof cgStartCamera==='function')open.onclick=cgStartCamera
    if(cancel&&typeof cgStopCamera==='function')cancel.onclick=cgStopCamera
    if(capture&&typeof cgCaptureFrame==='function')capture.onclick=cgCaptureFrame
  }

  async function ensureDefaultProfile(){
    try{
      if(typeof api!=='function')return
      let subjects=await api('/v1/subjects')
      let mine=subjects.find(x=>x.id==='my_profile'||String(x.display_name||'').toLowerCase()==='my profile')
      if(!mine)mine=await api('/v1/subjects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:'My profile'})})
      subjects=await api('/v1/subjects');mine=subjects.find(x=>x.id===mine.id)||mine;defaultProfileId=mine.id
      if(typeof trackingSubjects!=='undefined')trackingSubjects=subjects
      applyDefaultTracking()
    }catch(_e){}
  }

  function applyDefaultTracking(){
    if(typeof trackingSubjectId==='undefined'||typeof trackingRegionCode==='undefined')return
    if(isRgb()){
      if(!trackingSubjectId&&!trackingRegionCode&&defaultProfileId){trackingSubjectId=defaultProfileId;trackingRegionCode='full_face'}
    }else if(defaultProfileId&&trackingSubjectId===defaultProfileId&&(!trackingRegionCode||trackingRegionCode==='full_face')){trackingSubjectId='';trackingRegionCode=''}
    if(typeof populateTrackingControls==='function')populateTrackingControls()
    const box=document.querySelector('#trackingContext small')
    if(box)box.textContent=t(isRgb()?'Phone RGB defaults to My profile · Full face. Choose another profile only when needed.':'Choose both profile and region for longitudinal comparison, or leave both blank for analysis-only.')
  }

  if(typeof applyModeUI==='function'){
    const baseApply=applyModeUI
    applyModeUI=function(){const out=baseApply();applyDefaultTracking();wireCameraButton();if(!isRgb())stopDistance();return out}
  }

  if(typeof renderResult==='function'){
    const baseRender=renderResult
    renderResult=function(){
      baseRender()
      if(!latest||latest.modality!=='rgb'||rejectedAttempt)return
      const warnings=latest.metrics?.quality_warnings||[],blockers=latest.metrics?.quality_blockers||[],body=document.querySelector('#resultBody')
      if(!body||(!warnings.length&&!blockers.length))return
      const note=document.createElement('div');note.className='scienceNote'
      if(blockers.length)note.innerHTML=`<b>${t('Quality blockers.')}</b> ${blockers.join(', ')}.`
      else note.innerHTML=`<b>${t('Advisory capture notes.')}</b> ${warnings.join(', ')}. ${t('These warnings do not by themselves block a good-quality scan from longitudinal tracking.')}`
      body.appendChild(note)
    }
  }

  window.addEventListener('skin-ai:locale-change',()=>{ensureDistanceCell();applyDefaultTracking();wireCameraButton()})
  wireCameraButton();setTimeout(wireCameraButton,150);setTimeout(ensureDefaultProfile,250)
})();