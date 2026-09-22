// HTTPS Beta Deployment V1 — make cloud engine availability explicit.
(function(){
  function applyDeploymentReadiness(){
    const status=document.querySelector('#status')
    const uvButton=document.querySelector('[data-mode="uv"]')
    const rgbReady=health?.rgb_engine_available===true
    const uvReady=health?.uv_model_available===true
    if(status){
      status.textContent=rgbReady&&uvReady?'UV + RGB ready':rgbReady?'RGB ready · UV unavailable':'Analysis unavailable'
      status.className=`status ${rgbReady?'ready':'warn'}`
    }
    if(uvButton){
      uvButton.disabled=!uvReady
      uvButton.title=uvReady?'UV fluorescence analysis ready':'UV model checkpoint is not provisioned on this deployment yet.'
      uvButton.style.opacity=uvReady?'':'0.48'
      uvButton.style.cursor=uvReady?'':'not-allowed'
    }
    if(!uvReady && scanMode==='uv'){
      scanMode='rgb'
      applyModeUI()
    }
  }

  const originalRefresh=refresh
  refresh=async function(){
    const out=await originalRefresh()
    applyDeploymentReadiness()
    return out
  }
  applyDeploymentReadiness()
  setTimeout(applyDeploymentReadiness,250)
})();
