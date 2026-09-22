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
      ? '<b>Phone capture ready</b><span>For repeat scans, use the same camera, lighting, distance and angle.</span>'
      : '<b>UV mobile workflow</b><span>Upload a supported UV fluorescence image or connect a compatible external UV camera.</span>'
  }

  const oldApply=applyModeUI
  applyModeUI=function(){oldApply();mobileModeHint()}
  mobileModeHint()

  // Prevent accidental double-taps on primary capture actions while a request is running.
  document.addEventListener('click',e=>{
    const btn=e.target.closest('#cgCapture,#cgConfirmUvCamera')
    if(!btn||btn.disabled)return
    btn.dataset.mobilePressed='1'
    setTimeout(()=>{if(btn)delete btn.dataset.mobilePressed},900)
  })
})();
