const $=q=>document.querySelector(q)
const pct=v=>Number.isFinite(Number(v))?`${(Number(v)*100).toFixed(1)}%`:'—'
const fmtCv=v=>Number.isFinite(Number(v))?`${(Number(v)*100).toFixed(1)}%`:'—'
const fmtDate=v=>v?new Date(v).toLocaleString():'—'

async function api(path,options={}){
  const response=await fetch(path,{credentials:'same-origin',...options})
  const data=await response.json().catch(()=>({}))
  if(!response.ok){
    const message=typeof data.detail==='string'?data.detail:(data.detail?.message||`Request failed (${response.status})`)
    const err=new Error(message);err.status=response.status;err.detail=data.detail;throw err
  }
  return data
}

function showLogin(message=''){
  $('#loginView').classList.remove('hidden')
  $('#dashboardView').classList.add('hidden')
  $('#logoutBtn').classList.add('hidden')
  $('#loginError').textContent=message
  $('#loginError').classList.toggle('hidden',!message)
}
function showDashboard(){
  $('#loginView').classList.add('hidden')
  $('#dashboardView').classList.remove('hidden')
  $('#logoutBtn').classList.remove('hidden')
}

function summaryCard(label,value,note=''){
  return `<div class="summaryCard"><span>${label}</span><strong>${value}</strong>${note?`<small>${note}</small>`:''}</div>`
}

function participantCard(row){
  const access=row.has_access_code?'Access ready':'Needs access code'
  return `<article class="participantCard" data-tester="${row.tester_id}">
    <div class="participantTop"><strong>${row.tester_id}</strong><span class="pill">${access}</span></div>
    <div class="participantStats">
      <div><span>Sessions</span><b>${row.session_count}</b></div>
      <div><span>Captures</span><b>${row.capture_count}</b></div>
      <div><span>Eligible</span><b>${row.eligible_capture_count}</b></div>
    </div>
    <div class="participantStats">
      <div><span>Redness CV</span><b>${fmtCv(row.redness_cv)}</b></div>
      <div><span>Pigment CV</span><b>${fmtCv(row.pigmentation_cv)}</b></div>
      <div><span>Avg quality</span><b>${row.mean_capture_quality_score??'—'}</b></div>
    </div>
    <p style="margin-top:12px;color:var(--muted);font-size:11px">Latest: ${fmtDate(row.latest_at)}</p>
  </article>`
}

function scanCard(scan,index){
  const image=scan.media?.overlay||scan.media?.original||''
  return `<article class="scanCard">
    ${image?`<img src="${image}" alt="Study capture ${index+1}">`:''}
    <div class="scanBody">
      <h3>Session ${scan.session_id?String(scan.session_id).slice(0,8):index+1}</h3>
      <div class="scanMeta">${fmtDate(scan.created_at)}<br>${scan.rgb_engine_version?`RGB V${scan.rgb_engine_version}`:''}${scan.capture_protocol_version?` · Protocol ${scan.capture_protocol_version}`:''}</div>
      <div class="scanMetrics">
        <div><span>Redness</span><b>${pct(scan.redness_area_fraction)}</b></div>
        <div><span>Pigmentation</span><b>${pct(scan.pigmentation_area_fraction)}</b></div>
        <div><span>Texture</span><b>${Number.isFinite(Number(scan.texture_index_proxy))?Number(scan.texture_index_proxy).toFixed(3):'—'}</b></div>
        <div><span>Quality</span><b>${scan.capture_quality||'—'} ${scan.capture_quality_score??''}</b></div>
        <div><span>Confidence</span><b>${scan.measurement_confidence_score??'—'}</b></div>
        <div><span>Skin support</span><b>${pct(scan.anatomical_skin_support_fraction)}</b></div>
      </div>
    </div>
  </article>`
}

async function loadDashboard(){
  try{
    const summary=await api('/v1/researcher/study/summary')
    showDashboard()
    $('#summaryCards').innerHTML=[
      summaryCard('Participants',summary.participant_count),
      summaryCard('Sessions',summary.session_count),
      summaryCard('Captures',summary.capture_count),
      summaryCard('Trend eligible',summary.eligible_capture_count)
    ].join('')
    $('#participantGrid').innerHTML=summary.participants.length?summary.participants.map(participantCard).join(''):'<div class="empty">No study participants yet. Create P001 to begin.</div>'
    document.querySelectorAll('[data-tester]').forEach(card=>card.onclick=()=>loadParticipant(card.dataset.tester))
  }catch(err){
    if(err.status===401||err.status===503)showLogin(err.status===503?err.message:'')
    else showLogin(err.message)
  }
}

async function loadParticipant(testerId){
  try{
    const detail=await api(`/v1/researcher/study/participants/${encodeURIComponent(testerId)}`)
    const panel=$('#participantDetail')
    panel.classList.remove('hidden')
    panel.innerHTML=`<div class="card">
      <div class="detailHead"><div><span class="eyebrow">PARTICIPANT</span><h2>${detail.tester_id}</h2><p>${detail.session_count} session${detail.session_count===1?'':'s'} · ${detail.capture_count} capture${detail.capture_count===1?'':'s'} · ${detail.eligible_capture_count} trend eligible</p></div><button id="rotateAccessBtn" class="ghost" type="button">Rotate access code</button></div>
      <div class="participantStats" style="max-width:640px">
        <div><span>Redness CV</span><b>${fmtCv(detail.redness_cv)}</b></div>
        <div><span>Pigment CV</span><b>${fmtCv(detail.pigmentation_cv)}</b></div>
        <div><span>Avg capture quality</span><b>${detail.mean_capture_quality_score??'—'}</b></div>
      </div>
      ${detail.scans.length?`<div class="scanGrid">${detail.scans.map(scanCard).join('')}</div>`:'<div class="empty">No RGB study captures yet.</div>'}
    </div>`
    $('#rotateAccessBtn').onclick=()=>rotateAccess(detail.tester_id)
    panel.scrollIntoView({behavior:'smooth',block:'start'})
  }catch(err){alert(err.message)}
}

function showCredential(data){
  const panel=$('#credentialPanel')
  panel.classList.remove('hidden')
  panel.innerHTML=`<span class="eyebrow">TESTER CREDENTIALS · SAVE NOW</span><strong>${data.tester_id}</strong><div class="credentialRow"><span>Tester ID <span class="credentialCode">${data.tester_id}</span></span><span>Access code <span class="credentialCode">${data.access_code}</span></span></div><p>${data.message||'Share these privately with the tester.'}</p><button id="copyCredentialBtn" class="ghost" type="button">Copy credentials</button>`
  $('#copyCredentialBtn').onclick=async()=>{
    await navigator.clipboard.writeText(`Tester ID: ${data.tester_id}\nAccess code: ${data.access_code}`)
    $('#copyCredentialBtn').textContent='Copied'
  }
  panel.scrollIntoView({behavior:'smooth',block:'center'})
}

async function createTester(){
  const requested=prompt('Tester ID (leave blank to automatically create the next code, e.g. P001):','')
  if(requested===null)return
  try{
    const data=await api('/v1/researcher/study/participants',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tester_id:requested.trim()})})
    showCredential(data)
    await loadDashboard()
  }catch(err){alert(err.message)}
}

async function rotateAccess(testerId){
  if(!confirm(`Generate a new access code for ${testerId}? Their previous study cookie will stop working.`))return
  try{
    const data=await api(`/v1/researcher/study/participants/${encodeURIComponent(testerId)}/rotate-access`,{method:'POST'})
    showCredential(data)
  }catch(err){alert(err.message)}
}

async function exportManifest(){
  try{
    const manifest=await api('/v1/researcher/study/manifest')
    const blob=new Blob([JSON.stringify(manifest,null,2)],{type:'application/json'})
    const url=URL.createObjectURL(blob)
    const link=document.createElement('a')
    link.href=url;link.download=`skin-ai-study-v154-manifest-${new Date().toISOString().slice(0,10)}.json`;link.click()
    setTimeout(()=>URL.revokeObjectURL(url),500)
  }catch(err){alert(err.message)}
}

$('#loginForm').addEventListener('submit',async event=>{
  event.preventDefault()
  const key=$('#researcherKey').value
  $('#loginError').classList.add('hidden')
  try{
    await api('/v1/researcher/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})})
    $('#researcherKey').value=''
    await loadDashboard()
  }catch(err){showLogin(err.message)}
})
$('#logoutBtn').onclick=async()=>{try{await api('/v1/researcher/logout',{method:'POST'})}catch(_e){}showLogin('')}
$('#createTesterBtn').onclick=createTester
$('#exportBtn').onclick=exportManifest

loadDashboard()
