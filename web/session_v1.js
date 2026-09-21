// Scan Session V1 — guided multi-region capture.
let activeSession=null
const SESSION_STORAGE_KEY='skin_ai_active_session_id'

function sessionRegionLabel(code){ return trackingRegions.find(r=>r.code===code)?.label || code?.replaceAll('_',' ') || 'Region' }
function sessionIsActive(){ return !!(activeSession && activeSession.status==='in_progress' && !activeSession.progress?.complete) }

function buildSessionUI(){
  const tracking=$('#trackingContext')
  if(!tracking || $('#sessionPanel')) return
  const panel=document.createElement('div')
  panel.id='sessionPanel';panel.className='sessionPanel'
  panel.innerHTML=`
    <div class="sessionHead"><div><span class="eyebrow">GUIDED SESSION</span><b id="sessionTitle">Capture regions in one visit</b></div><button id="startSessionBtn" type="button" class="secondaryMini">Start session</button></div>
    <div id="sessionBody" class="sessionBody"><small>UV sessions guide 5 regions. Phone RGB sessions use one full-face capture.</small></div>`
  tracking.insertAdjacentElement('afterend',panel)
  $('#startSessionBtn').onclick=startGuidedSession
}

async function startGuidedSession(){
  if(!trackingSubjectId){ showError('Choose a subject profile before starting a guided session.'); return }
  try{
    showError('')
    activeSession=await api('/v1/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subject_id:trackingSubjectId,modality:scanMode})})
    localStorage.setItem(SESSION_STORAGE_KEY,activeSession.id)
    syncSessionTracking(); renderSessionPanel()
  }catch(e){showError(e.message)}
}

function syncSessionTracking(){
  if(!activeSession) return
  trackingSubjectId=activeSession.subject_id
  const next=activeSession.progress?.next_region_code
  if(next) trackingRegionCode=next
  populateTrackingControls()
  const subject=$('#scanSubjectSelect'), region=$('#scanRegionSelect')
  if(subject) subject.disabled=sessionIsActive()
  if(region) region.disabled=sessionIsActive()
  $$('[data-mode]').forEach(b=>{b.disabled=sessionIsActive()})
  if(next && region){region.value=next}
}

function renderSessionPanel(){
  buildSessionUI()
  const btn=$('#startSessionBtn'), body=$('#sessionBody'), title=$('#sessionTitle')
  if(!btn||!body||!title) return
  if(!activeSession){
    title.textContent='Capture regions in one visit'
    btn.textContent='Start session';btn.disabled=false
    body.innerHTML='<small>UV sessions guide Forehead → Left cheek → Right cheek → Nose → Chin. Phone RGB uses one full-face capture.</small>'
    return
  }
  const p=activeSession.progress||{}, plan=activeSession.plan||[], completed=new Set(p.completed_regions||[]), next=p.next_region_code
  const subject=activeSession.subject?.display_name||'Subject'
  title.textContent=`${subject} · ${activeSession.modality.toUpperCase()} session`
  btn.textContent=p.complete?'Start new session':'Session active';btn.disabled=!p.complete
  if(p.complete) btn.onclick=()=>{activeSession=null;localStorage.removeItem(SESSION_STORAGE_KEY);syncSessionTracking();renderSessionPanel();startGuidedSession()}
  const steps=plan.map((code,i)=>{
    const state=completed.has(code)?'done':code===next?'current':'pending'
    const mark=state==='done'?'✓':String(i+1)
    return `<div class="sessionStep ${state}"><i>${mark}</i><span>${sessionRegionLabel(code)}</span></div>`
  }).join('')
  const summary=p.complete?sessionSummaryHtml(activeSession):`<div class="sessionNext"><b>Next: ${sessionRegionLabel(next)}</b><small>${p.completed_count||0} of ${p.total_count||plan.length} regions complete. Upload the current region below.</small></div>`
  body.innerHTML=`<div class="sessionProgress">${steps}</div>${summary}`
  if(next){
    trackingRegionCode=next; populateTrackingControls(); if($('#scanRegionSelect')) $('#scanRegionSelect').value=next
    $('#uploadTitle').textContent=`Capture ${sessionRegionLabel(next)}`
    $('#uploadHelp').textContent=activeSession.modality==='uv'?'Use the same UV device, distance and angle for every region.':'Front-facing full-face photo · neutral light · no beauty filters.'
  }
}

function sessionSummaryHtml(session){
  const cards=(session.items||[]).map(item=>{
    const m=item.metrics||{}
    const value=session.modality==='uv'?`${m.porphyrin_component_count_proxy??'—'} spots`:`${pct(m.redness_area_fraction)} redness`
    return `<div class="sessionSummaryCard"><span>${sessionRegionLabel(item.region_code)}</span><b>${value}</b><small>${new Date(item.created_at).toLocaleTimeString()}</small></div>`
  }).join('')
  return `<div class="sessionComplete"><b>Session complete</b><small>${session.items?.length||0} captures saved under one session.</small><div class="sessionSummaryGrid">${cards}</div></div>`
}

const apiSessionBase=api
api=async function(path,options={}){
  if((path==='/v1/uv/analyze'||path==='/v1/rgb/analyze') && options.body instanceof FormData && sessionIsActive()){
    const next=activeSession.progress?.next_region_code
    options.body.set('session_id',activeSession.id)
    options.body.set('subject_id',activeSession.subject_id)
    if(next) options.body.set('region_code',next)
  }
  const data=await apiSessionBase(path,options)
  if((path==='/v1/uv/analyze'||path==='/v1/rgb/analyze') && data?.session){
    activeSession=data.session
    localStorage.setItem(SESSION_STORAGE_KEY,activeSession.id)
    syncSessionTracking();renderSessionPanel()
  }
  return data
}

const applyModeSessionBase=applyModeUI
applyModeUI=function(){ applyModeSessionBase(); if(activeSession && activeSession.modality!==scanMode && sessionIsActive()) scanMode=activeSession.modality; syncSessionTracking();renderSessionPanel() }

async function restoreSession(){
  buildSessionUI()
  const id=localStorage.getItem(SESSION_STORAGE_KEY)
  if(!id){renderSessionPanel();return}
  try{
    activeSession=await api(`/v1/sessions/${id}`)
    if(activeSession.status==='complete' || activeSession.progress?.complete) localStorage.removeItem(SESSION_STORAGE_KEY)
    scanMode=activeSession.modality
    syncSessionTracking();renderSessionPanel()
  }catch(e){localStorage.removeItem(SESSION_STORAGE_KEY);activeSession=null;renderSessionPanel()}
}

restoreSession()
