// Capture Guidance V2 — browser-side acquisition assistance.
// These checks are advisory. Backend quality/modality gates remain authoritative.
let captureGuideStream=null
let captureGuideTimer=null
let captureGuidePrevFrame=null
let captureGuidePendingFile=null
const cgT=en=>{try{return window.skinCaptureI18n?.t?.(en)||window.skinI18n?.t?.(en)||en}catch(_e){return en}}

function cgClamp(v,min,max){return Math.max(min,Math.min(max,v))}
function cgCurrentRegion(){
  if(typeof activeSession!=='undefined' && activeSession?.progress?.next_region_code) return activeSession.progress.next_region_code
  if(typeof trackingRegionCode!=='undefined' && trackingRegionCode) return trackingRegionCode
  return scanMode==='rgb'?'full_face':'skin_closeup'
}
function cgRegionLabel(){
  const code=cgCurrentRegion()
  try{return typeof sessionRegionLabel==='function'?sessionRegionLabel(code):code.replaceAll('_',' ')}catch(_e){return code.replaceAll('_',' ')}
}
function cgInstruction(){
  if(scanMode==='rgb') return cgT('Center the full face in the guide. Keep the phone level and use even frontal light.')
  const label=cgRegionLabel()
  return cgT(`Position the ${label.toLowerCase()} close-up inside the guide. Keep device distance and angle consistent with prior captures.`)
}
function cgBuildUI(){
  const capture=document.querySelector('.capture')
  const dropzone=document.querySelector('#dropzone')
  if(!capture||!dropzone||document.querySelector('#captureGuidanceV2')) return
  const panel=document.createElement('div')
  panel.id='captureGuidanceV2'
  panel.className='captureGuidanceV2'
  panel.innerHTML=`
    <div class="cgHeader"><div><span class="eyebrow">${cgT('CAPTURE GUIDANCE V2')}</span><b>${cgT('Improve repeatability before analysis')}</b></div><button type="button" class="secondaryMini" id="cgOpenCamera">${cgT('Use camera')}</button></div>
    <div id="cgPreflight" class="cgPreflight hidden"></div>
    <div id="cgCamera" class="cgCamera hidden">
      <div class="cgStage">
        <video id="cgVideo" autoplay playsinline muted></video>
        <div id="cgGuide" class="cgGuide"><span id="cgGuideLabel">${cgT('Position region')}</span></div>
      </div>
      <div class="cgLiveChecks">
        <div data-cg-check="lighting"><span>${cgT('Lighting')}</span><b>${cgT('Checking…')}</b></div>
        <div data-cg-check="sharpness"><span>${cgT('Sharpness')}</span><b>${cgT('Checking…')}</b></div>
        <div data-cg-check="stability"><span>${cgT('Stability')}</span><b>${cgT('Checking…')}</b></div>
        <div class="visual"><span>${cgT('Position')}</span><b>${cgT('Visual guide')}</b></div>
      </div>
      <p id="cgInstruction"></p>
      <div class="cgCameraActions"><button type="button" class="secondaryMini" id="cgCancelCamera">${cgT('Cancel')}</button><button type="button" class="primary" id="cgCapture">${cgT('Capture photo')}</button></div>
      <small>${cgT('Lighting, sharpness and stability are browser-side estimates. Position and distance remain visual guidance; the backend performs the final quality check.')}</small>
      <canvas id="cgCanvas" class="hidden"></canvas>
    </div>`
  dropzone.insertAdjacentElement('beforebegin',panel)
  document.querySelector('#cgOpenCamera').onclick=cgStartCamera
  document.querySelector('#cgCancelCamera').onclick=cgStopCamera
  document.querySelector('#cgCapture').onclick=cgCaptureFrame
}

function cgSetCheck(name,label,state){
  const el=document.querySelector(`[data-cg-check="${name}"]`)
  if(!el)return
  el.classList.remove('good','warn','poor');el.classList.add(state)
  el.querySelector('b').textContent=label
}
function cgFrameMetrics(data,w,h){
  const px=data.data
  let sum=0,dark=0,bright=0,edge=0,n=0
  const gray=new Float32Array(w*h)
  for(let i=0,p=0;i<px.length;i+=4,p++){
    const y=0.2126*px[i]+0.7152*px[i+1]+0.0722*px[i+2]
    gray[p]=y;sum+=y;n++
    if(y<25)dark++;if(y>245)bright++
  }
  for(let y=1;y<h;y+=2){for(let x=1;x<w;x+=2){
    const i=y*w+x
    edge+=Math.abs(gray[i]-gray[i-1])+Math.abs(gray[i]-gray[i-w])
  }}
  const samples=Math.max(1,Math.floor((w-1)/2)*Math.floor((h-1)/2))
  return {mean:sum/Math.max(1,n),dark:dark/Math.max(1,n),bright:bright/Math.max(1,n),edge:edge/samples,gray}
}
function cgEvaluateMetrics(m){
  const lighting=(m.mean<45||m.mean>225||m.dark>0.18||m.bright>0.18)?'poor':(m.mean<65||m.mean>205||m.dark>0.08||m.bright>0.08)?'warn':'good'
  const sharp=m.edge<10?'poor':m.edge<18?'warn':'good'
  return {lighting,sharp}
}
function cgStatusText(state,good,warn,poor){return state==='good'?good:state==='warn'?warn:poor}

async function cgStartCamera(){
  cgBuildUI();cgStopCamera()
  const camera=document.querySelector('#cgCamera'),video=document.querySelector('#cgVideo')
  try{
    captureGuideStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:{ideal:1280},height:{ideal:960}},audio:false})
    video.srcObject=captureGuideStream
    camera.classList.remove('hidden')
    document.querySelector('#cgGuideLabel').textContent=cgRegionLabel()
    document.querySelector('#cgInstruction').textContent=cgInstruction()
    await video.play()
    captureGuideTimer=setInterval(cgLiveSample,350)
  }catch(e){
    showError(cgT('Camera access was not available. You can still choose an image from your device.'))
    cgStopCamera()
  }
}
function cgStopCamera(){
  if(captureGuideTimer){clearInterval(captureGuideTimer);captureGuideTimer=null}
  if(captureGuideStream){captureGuideStream.getTracks().forEach(t=>t.stop());captureGuideStream=null}
  captureGuidePrevFrame=null
  const camera=document.querySelector('#cgCamera');if(camera)camera.classList.add('hidden')
  const video=document.querySelector('#cgVideo');if(video)video.srcObject=null
}
function cgLiveSample(){
  const video=document.querySelector('#cgVideo'),canvas=document.querySelector('#cgCanvas')
  if(!video||!canvas||video.readyState<2)return
  const w=160,h=Math.max(100,Math.round(160*video.videoHeight/Math.max(1,video.videoWidth)))
  canvas.width=w;canvas.height=h
  const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(video,0,0,w,h)
  const image=ctx.getImageData(0,0,w,h),m=cgFrameMetrics(image,w,h),q=cgEvaluateMetrics(m)
  cgSetCheck('lighting',q.lighting==='good'?cgT('Good'):q.lighting==='warn'?cgT('Adjust'):cgT('Poor'),q.lighting)
  cgSetCheck('sharpness',q.sharp==='good'?cgT('Good'):q.sharp==='warn'?cgT('Hold steady'):cgT('Refocus'),q.sharp)
  let stability='warn',label=cgT('Hold steady')
  if(captureGuidePrevFrame && captureGuidePrevFrame.length===m.gray.length){
    let diff=0;for(let i=0;i<m.gray.length;i+=8)diff+=Math.abs(m.gray[i]-captureGuidePrevFrame[i])
    diff/=Math.max(1,Math.floor(m.gray.length/8))
    stability=diff<3.2?'good':diff<7?'warn':'poor'
    label=stability==='good'?cgT('Stable'):stability==='warn'?cgT('Hold steady'):cgT('Too much movement')
  }
  captureGuidePrevFrame=m.gray
  cgSetCheck('stability',label,stability)
}
async function cgCaptureFrame(){
  const video=document.querySelector('#cgVideo'),canvas=document.querySelector('#cgCanvas')
  if(!video||!canvas||video.readyState<2)return
  const maxW=1280,scale=Math.min(1,maxW/video.videoWidth)
  canvas.width=Math.max(1,Math.round(video.videoWidth*scale));canvas.height=Math.max(1,Math.round(video.videoHeight*scale))
  canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height)
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',0.92))
  if(!blob)return
  const file=new File([blob],`camera-${scanMode}-${Date.now()}.jpg`,{type:'image/jpeg'})
  cgStopCamera();await cgHandleFile(file)
}

async function cgImageMetrics(file){
  const img=await createImageBitmap(file)
  const scale=Math.min(1,640/img.width),w=Math.max(1,Math.round(img.width*scale)),h=Math.max(1,Math.round(img.height*scale))
  const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h
  const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0,w,h);img.close?.()
  const data=ctx.getImageData(0,0,w,h),m=cgFrameMetrics(data,w,h),q=cgEvaluateMetrics(m)
  return {...m,...q,width:w,height:h,sourceWidth:Math.round(w/scale),sourceHeight:Math.round(h/scale)}
}
function cgFriendlyPreflight(m){
  const issues=[]
  if(m.sourceWidth<480||m.sourceHeight<480)issues.push({level:'poor',label:cgT('Low image resolution'),help:cgT('Use a higher-resolution capture so small skin features are not lost.')})
  if(m.lighting==='poor')issues.push({level:'poor',label:cgT('Lighting outside preferred range'),help:cgT('Use more even illumination and avoid very dark or blown-out areas.')})
  else if(m.lighting==='warn')issues.push({level:'warn',label:cgT('Lighting could be more even'),help:cgT('Try more neutral, even light before capture.')})
  if(m.sharp==='poor')issues.push({level:'poor',label:cgT('Image may be blurry'),help:cgT('Refocus and hold the phone steady.')})
  else if(m.sharp==='warn')issues.push({level:'warn',label:cgT('Sharpness is borderline'),help:cgT('Hold steady and refocus before capture.')})
  return issues
}
function cgRenderPreflight(file,m,issues){
  const box=document.querySelector('#cgPreflight');if(!box)return
  const severe=issues.some(x=>x.level==='poor')
  box.classList.remove('hidden','good','warn','poor');box.classList.add(severe?'poor':issues.length?'warn':'good')
  if(!issues.length){
    box.innerHTML=`<div><span class="eyebrow">${cgT('PRE-CAPTURE CHECK')}</span><b>${cgT('Ready for backend quality check')}</b><small>${m.sourceWidth}×${m.sourceHeight} · ${cgT('exposure and sharpness look acceptable.')}</small></div>`
    setTimeout(()=>box.classList.add('hidden'),1400);return
  }
  box.innerHTML=`<div class="cgPreflightHead"><div><span class="eyebrow">${cgT('PRE-CAPTURE CHECK')}</span><b>${cgT(severe?'Retake recommended':'Capture can be improved')}</b></div><span>${issues.length} ${cgT(issues.length===1?'issue':'issues')}</span></div>
    <div class="cgIssueList">${issues.map(x=>`<div class="${x.level}"><b>${x.label}</b><small>${x.help}</small></div>`).join('')}</div>
    <div class="cgPreflightActions"><button type="button" class="secondaryMini" id="cgRetake">${cgT('Choose another image')}</button><button type="button" class="primary" id="cgContinue">${cgT('Analyze anyway')}</button></div>
    <small>${cgT('These browser checks are advisory. The server-side RGB/UV quality gates remain authoritative.')}</small>`
  document.querySelector('#cgRetake').onclick=()=>{captureGuidePendingFile=null;box.classList.add('hidden');document.querySelector('#fileInput')?.click()}
  document.querySelector('#cgContinue').onclick=()=>{const pending=captureGuidePendingFile;captureGuidePendingFile=null;box.classList.add('hidden');if(pending)cgRunBaseUpload(pending)}
}

let cgBaseUploadHandler=null
async function cgRunBaseUpload(file){
  if(!cgBaseUploadHandler)return
  const mock={target:{files:[file],value:''}}
  await cgBaseUploadHandler(mock)
}
async function cgHandleFile(file){
  try{
    const m=await cgImageMetrics(file),issues=cgFriendlyPreflight(m)
    captureGuidePendingFile=file
    cgRenderPreflight(file,m,issues)
    if(!issues.length){captureGuidePendingFile=null;await cgRunBaseUpload(file)}
  }catch(_e){captureGuidePendingFile=null;await cgRunBaseUpload(file)}
}
function cgInstallUploadPreflight(){
  const input=document.querySelector('#fileInput');if(!input||input.dataset.cgV2==='1')return
  input.dataset.cgV2='1';cgBaseUploadHandler=input.onchange
  input.onchange=async e=>{const file=e.target.files?.[0];e.target.value='';if(!file)return;await cgHandleFile(file)}
}

const cgApplyModeBase=applyModeUI
applyModeUI=function(){
  cgApplyModeBase();cgBuildUI()
  const label=document.querySelector('#cgGuideLabel');if(label)label.textContent=cgRegionLabel()
  const inst=document.querySelector('#cgInstruction');if(inst)inst.textContent=cgInstruction()
}

function cgRelocalizeActiveUI(){
  const panel=document.querySelector('#captureGuidanceV2');if(!panel)return
  const pairs=[['.cgHeader .eyebrow','CAPTURE GUIDANCE V2'],['.cgHeader b','Improve repeatability before analysis'],['#cgOpenCamera','Use camera'],['[data-cg-check="lighting"] span','Lighting'],['[data-cg-check="sharpness"] span','Sharpness'],['[data-cg-check="stability"] span','Stability'],['.visual span','Position'],['.visual b','Visual guide'],['#cgCancelCamera','Cancel'],['#cgCapture','Capture photo']]
  pairs.forEach(([selector,en])=>{const el=panel.querySelector(selector);if(el)el.textContent=cgT(en)})
  const label=panel.querySelector('#cgGuideLabel');if(label)label.textContent=cgRegionLabel()
  const inst=panel.querySelector('#cgInstruction');if(inst)inst.textContent=cgInstruction()
  const note=panel.querySelector('#cgCamera > small');if(note)note.textContent=cgT('Lighting, sharpness and stability are browser-side estimates. Position and distance remain visual guidance; the backend performs the final quality check.')
  try{if(captureGuideStream)cgLiveSample()}catch(_e){}
}
window.addEventListener('skin-ai:locale-change',cgRelocalizeActiveUI)
window.addEventListener('skin-ai:capture-i18n-ready',cgRelocalizeActiveUI)

cgBuildUI();cgInstallUploadPreflight()
setTimeout(()=>{cgBuildUI();cgInstallUploadPreflight()},100)
