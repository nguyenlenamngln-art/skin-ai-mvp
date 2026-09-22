// Capture Guidance V2.1 — modality-aware camera UX.
// Keeps Capture Guidance V2 measurements unchanged; clarifies which camera path is valid.
let cgUvConfirmOpen=false

function cgEnsureModeNote(){
  const header=document.querySelector('#captureGuidanceV2 .cgHeader > div')
  if(!header) return null
  let note=document.querySelector('#cgModeNote')
  if(!note){
    note=document.createElement('small')
    note.id='cgModeNote'
    note.className='cgModeNote'
    header.appendChild(note)
  }
  return note
}

function cgEnsureUvConfirm(){
  const panel=document.querySelector('#captureGuidanceV2')
  if(!panel) return null
  let box=document.querySelector('#cgUvCameraConfirm')
  if(!box){
    box=document.createElement('div')
    box.id='cgUvCameraConfirm'
    box.className='cgUvCameraConfirm hidden'
    box.innerHTML=`
      <div class="cgUvConfirmIcon">UV</div>
      <div class="cgUvConfirmCopy">
        <b>External UV fluorescence camera required</b>
        <p>Your built-in webcam is normally an RGB camera and cannot create a genuine UV-fluorescence capture.</p>
        <small>Continue only when a compatible external UV camera is connected and selected as the browser camera source.</small>
      </div>
      <div class="cgUvConfirmActions">
        <button type="button" class="secondaryMini" id="cgChooseUvFile">Upload UV image</button>
        <button type="button" class="primary" id="cgConfirmUvCamera">Continue with external UV camera</button>
        <button type="button" class="cgTextButton" id="cgCancelUvCamera">Cancel</button>
      </div>`
    const header=panel.querySelector('.cgHeader')
    header?.insertAdjacentElement('afterend',box)
    box.querySelector('#cgChooseUvFile').onclick=()=>{
      cgHideUvConfirm()
      document.querySelector('#fileInput')?.click()
    }
    box.querySelector('#cgCancelUvCamera').onclick=cgHideUvConfirm
    box.querySelector('#cgConfirmUvCamera').onclick=async()=>{
      cgHideUvConfirm()
      await cgStartCameraOriginal()
    }
  }
  return box
}

function cgShowUvConfirm(){
  cgStopCamera?.()
  const box=cgEnsureUvConfirm()
  if(!box) return
  cgUvConfirmOpen=true
  box.classList.remove('hidden')
}
function cgHideUvConfirm(){
  cgUvConfirmOpen=false
  document.querySelector('#cgUvCameraConfirm')?.classList.add('hidden')
}

function cgApplyModalityCopy(){
  if(!document.querySelector('#captureGuidanceV2')) return
  const button=document.querySelector('#cgOpenCamera')
  const note=cgEnsureModeNote()
  cgEnsureUvConfirm()
  if(!button||!note) return
  cgHideUvConfirm()
  if(scanMode==='uv'){
    button.textContent='Use UV camera'
    button.classList.add('uvCameraButton')
    note.innerHTML='<b>External UV device required.</b> Built-in webcams are RGB only.'
    button.onclick=cgShowUvConfirm
  }else{
    button.textContent='Use camera'
    button.classList.remove('uvCameraButton')
    note.innerHTML='<b>Built-in webcam or phone camera supported.</b> Live guidance checks lighting, sharpness and stability.'
    button.onclick=cgStartCameraOriginal
  }
}

// Preserve the V2 camera implementation and put the guard in front of it only for UV.
const cgStartCameraOriginal=cgStartCamera

const cgBuildUIOriginal=cgBuildUI
cgBuildUI=function(){
  cgBuildUIOriginal()
  cgApplyModalityCopy()
}

const cgApplyModeV21Base=applyModeUI
applyModeUI=function(){
  cgApplyModeV21Base()
  cgApplyModalityCopy()
}

// If the user changes scan modality while a camera/confirmation is open, close it first.
document.querySelectorAll('[data-mode]').forEach(btn=>{
  btn.addEventListener('click',()=>{
    cgStopCamera?.()
    cgHideUvConfirm()
    setTimeout(cgApplyModalityCopy,0)
  })
})

cgApplyModalityCopy()
setTimeout(cgApplyModalityCopy,100)
