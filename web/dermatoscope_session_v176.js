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
    panel.innerHTML=`<div><span>${tr('Capture attempts','Số lần chụp')}</span><b id="dermAttemptCount">0 / ${MAX_ATTEMPTS}</b></div><p id="dermSessionHint"></p>`
    const actions=side.querySelector('.dermActions');if(actions)side.insertBefore(panel,actions);else side.appendChild(panel)
    return panel
  }

  function render(){
    const p=position(),panel=ensurePanel();if(!p||!panel)return
    const count=attempts[p.key]||0
    panel.querySelector('#dermAttemptCount').textContent=`${count} / ${MAX_ATTEMPTS}`
    const hint=panel.querySelector('#dermSessionHint')
    if(statuses[p.key]==='accepted')hint.textContent=tr('Position accepted.','Vị trí đã đạt yêu cầu.')
    else if(statuses[p.key]==='rejected'&&count>=MAX_ATTEMPTS)hint.textContent=tr('Retry limit reached. This position is marked incomplete and the scan will continue.','Đã đạt giới hạn chụp lại. Vị trí này được đánh dấu chưa hoàn tất và lần quét sẽ tiếp tục.')
    else if(statuses[p.key]==='rejected')hint.textContent=tr('Position did not match. Reposition and try again.','Vị trí chưa khớp. Hãy điều chỉnh và chụp lại.')
    else hint.textContent=tr(`Up to ${MAX_ATTEMPTS} attempts are allowed for this position.`,`Cho phép tối đa ${MAX_ATTEMPTS} lần chụp cho vị trí này.`)
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

  function registerRejected(detail){
    const p=position();if(!p)return true
    attempts[p.key]=(attempts[p.key]||0)+1
    statuses[p.key]='rejected'
    detail.session_attempt_count=attempts[p.key]
    detail.session_retry_limit=MAX_ATTEMPTS
    detail.session_retry_allowed=attempts[p.key]<MAX_ATTEMPTS
    updatePosition(p,'rejected',detail?.capture_id)
    render()
    return detail.session_retry_allowed
  }

  async function onAccepted(event){
    const p=position();if(!p)return
    attempts[p.key]=(attempts[p.key]||0)+1
    await updatePosition(p,'accepted',event.detail?.capture_id)
    render()
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
    window.addEventListener('skin-ai:dermatoscope-retake-required',()=>setTimeout(render,0))
    const observer=new MutationObserver(()=>{
      const complete=document.querySelector('#dermComplete')
      if(complete&&!complete.hidden)finishSession(Object.values(statuses).some(s=>s==='rejected'||s==='skipped'||s==='incomplete')?'incomplete':'complete')
      render()
    })
    const scan=document.querySelector('#scan');if(scan)observer.observe(scan,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class']})
    document.documentElement.dataset.dermatoscopeSessionVersion=VERSION
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install()
  window.skinDermatoscopeSession={version:VERSION,maxAttempts:MAX_ATTEMPTS,registerRejected,state:()=>({session,region,attempts:{...attempts},statuses:{...statuses}})}
})()
