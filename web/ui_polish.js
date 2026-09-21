// Small UI polish layer: reset successful uploads while keeping rejected previews visible.
function resetSuccessfulUploadChooser(){
  const input=$('#fileInput')
  const preview=$('#preview')
  const dropContent=$('#dropContent')
  const dropzone=$('#dropzone')
  if(preview){
    const oldSrc=preview.getAttribute('src')||''
    if(oldSrc.startsWith('blob:')){
      try{ URL.revokeObjectURL(oldSrc) }catch(_e){}
    }
    preview.removeAttribute('src')
    preview.classList.add('hidden')
  }
  if(dropContent) dropContent.classList.remove('hidden')
  if(dropzone) dropzone.classList.remove('busy')
  if(input) input.value=''
}

const apiUploadResetBase=api
api=async function(path,options={}){
  const data=await apiUploadResetBase(path,options)
  if((path==='/v1/uv/analyze'||path==='/v1/rgb/analyze') && options.body instanceof FormData){
    // Only successful requests reach this point. Failed captures intentionally keep
    // their preview visible so the user can see what needs to be retaken.
    resetSuccessfulUploadChooser()
  }
  return data
}
