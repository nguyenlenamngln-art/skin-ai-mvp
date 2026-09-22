// UV upload wording refinement.
// Keep guided-session region prompts intact; clarify the generic UV upload path.
function applyUvUploadWording(){
  const activeGuidedSession = typeof sessionIsActive==='function' && sessionIsActive()
  const completedGuidedSession = typeof sessionIsComplete==='function' && sessionIsComplete()
  if(scanMode==='uv' && !activeGuidedSession && !completedGuidedSession){
    const title=document.querySelector('#uploadTitle')
    const help=document.querySelector('#uploadHelp')
    if(title) title.textContent='Upload UV fluorescence image'
    if(help) help.textContent='From a supported UV fluorescence device · PNG or JPEG · up to 20 MB'
  }
}

const uvUploadWordingApplyModeBase=applyModeUI
applyModeUI=function(){
  uvUploadWordingApplyModeBase()
  applyUvUploadWording()
}

applyUvUploadWording()
setTimeout(applyUvUploadWording,100)
