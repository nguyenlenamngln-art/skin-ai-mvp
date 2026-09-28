// V1.7.6 — Capture session integrity & retry limits.
(function(){
  const VERSION='1.7.6'
  const MAX_ATTEMPTS=3
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const tr=(en,vi)=>locale()==='vi'?vi:en
  const SHOTS={forehead:['left','center','right'],left_cheek:['upper','middle','lower'],right_cheek:['upper','middle','lower'],nose:['center'],chin:['upper','lower'],custom:['custom']}
  let session=null
  let region=null
  let attempts={}
  let statuses={}

  function root(){return document.querySelector('#dermV171')}
  function activeRegion(){return root()?.querySelector('.dermRegion.active')?.dataset.dermRegion||region}
  function position(){
    const r=activeRegion();if(!r)return null
    const counter=root()?.querySelector('#dermCounter')?.textContent||'1 / 1'
    const index=Math.max(0,(parseInt(counter.split('/')[0])||1)-1)
    const sub=(SHOTS[r]||[])[index]
    return sub?{region:r,subregion:sub,key:`${r}/${sub}`} : null
  }

  function ensurePanel(){
    const side=root()?.querySelector('.dermCaptureSide');if(!side)return null
    let panel=document.querySelector('#dermSessionPanel')
    if(panel)return panel
    panel=document.createElement('div');panel.id='dermSessionPanel';panel.className='dermSessionPanel'
    panel.innerHTML=`<div><span>${tr('Capture attempts','Số lần chụp')}</span><b id="dermAttemptCount">0 / ${MAX_ATTEMPTS}</b></div><p id="dermSessionHint"></p><div class="dermSessionActions"><button type="button" class="secondaryMini" id="dermSkipPosition">${tr('Skip this position','Bỏ qua vị trí này')}</button></div>`
    const actions=side.querySelector('.dermActions');if(actions)side.insertBefore(panel,actions);else side.appendChild(panel)
    panel.querySelector('#dermSkipPosition').onclick=skipCurrent
    return panel
  }

  function render(){
    const p=position(),panel=ensurePanel();if(!p||!panel)return
    const count=attempts[p.key]||0
    panel.querySelector('#dermAttemptCount').textContent=`${count} / ${MAX_ATTEMPTS}`
    const hint=panel.querySelector('#dermSessionHint')
    if(statuses[p.key]==='skipped')hint.textContent=tr('This position was skipped.','Vị trí này đã được bỏ qua.')
    else if(count>=MAX_ATTEMPTS)hint.textContent=tr('Retry limit reached. You can skip this position and continue.','Đã đạt giới hạn chụp lại. Bạn có thể bỏ qua vị trí này để tiếp tục.')
    else hint.textContent=tr(`Up to ${MAX_ATTEMPTS} attempts are allowed for this position.`,`Cho phép tối đa ${MAX_ATTEMPTS} lần chụp cho vị trí này.`)
    panel.querySelector('#dermSkipPosition').hidden=count<MAX_ATTEMPTS
  }

  async function post(url,values){
    const form=new FormData();Object.entries(values).forEach(([k,v])=>form.append(k,String(v)))
    const r=await fetch(url,{method:'POST',body:form});if(!r.ok)throw new Error(`session ${r.status}`);return r.json()
  }

  async function createSession(r){
    region=r;attempts={};statuses={};session=null
    try{session=await post('/v1/dermatoscope/sessions',{region:r,simulator:true,subject_key:'my_profile'});document.documentElement.dataset.dermatoscopeSessionId=session.id}catch(_e){}
    render()
  }

  async function updatePosition(p,status,captureId){
    statuses[p.key]=status
    if(!session?.id)return
    try{session=await post(`/v1/dermatoscope/sessions/${encodeURIComponent(session.id)}/positions`,{region:p.region,subregion:p.subregion,status,attempts:attempts[p.key]||0,capture_id:captureId||''})}catch(_e){}
  }

  async function onAccepted(event){
    const p=position();if(!p)return
    attempts[p.key]=(attempts[p.key]||0)+1
    await updatePosition(p,'accepted',event.detail?.capture_id)
    render()
  }

  async function onRejected(event){
    const p=position();if(!p)return
    attempts[p.key]=(attempts[p.key]||0)+1
    statuses[p.key]='rejected'
    await updatePosition(p,'rejected',event.detail?.capture_id)
    render()
    if(attempts[p.key]>=MAX_ATTEMPTS){
      const status=document.querySelector('#dermStatus');if(status)status.textContent=tr('Retry limit reached. Skip this position or adjust and try once more after restarting the area.','Đã đạt giới hạn chụp lại. Hãy bỏ qua vị trí này hoặc điều chỉnh và bắt đầu lại vùng này.')
    }
  }

  async function skipCurrent(){
    const p=position();if(!p)return
    await updatePosition(p,'skipped',null)
    statuses[p.key]='skipped';render()
    const retake=document.querySelector('#dermRetakePanel');if(retake)retake.hidden=true
    const status=document.querySelector('#dermStatus');if(status)status.textContent=tr('Position skipped. Continue with the next position.','Đã bỏ qua vị trí này. Tiếp tục với vị trí tiếp theo.')
    window.dispatchEvent(new CustomEvent('skin-ai:dermatoscope-position-skipped',{detail:p}))
  }

  async function finishSession(finalStatus){
    if(!session?.id)return
    try{session=await post(`/v1/dermatoscope/sessions/${encodeURIComponent(session.id)}/finish`,{status:finalStatus})}catch(_e){}
  }

  function install(){
    document.addEventListener('click',event=>{
      const regionButton=event.target.closest?.('[data-derm-region]')
      if(regionButton)setTimeout(()=>createSession(regionButton.dataset.dermRegion),0)
      if(event.target.closest?.('#dermCancel'))finishSession('cancelled')
      if(event.target.closest?.('#dermAgain'))finishSession('complete')
    })
    window.addEventListener('skin-ai:dermatoscope-position-accepted',onAccepted)
    window.addEventListener('skin-ai:dermatoscope-retake-required',onRejected)
    const observer=new MutationObserver(()=>{
      const complete=document.querySelector('#dermComplete')
      if(complete&&!complete.hidden)finishSession(Object.values(statuses).some(s=>s==='skipped'||s==='rejected')?'incomplete':'complete')
      render()
    })
    const scan=document.querySelector('#scan');if(scan)observer.observe(scan,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class']})
    document.documentElement.dataset.dermatoscopeSessionVersion=VERSION
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install()
  window.skinDermatoscopeSession={version:VERSION,maxAttempts:MAX_ATTEMPTS,state:()=>({session,region,attempts:{...attempts},statuses:{...statuses}})}
})()
