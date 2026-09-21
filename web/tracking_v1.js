// Profiles + structured regions + longitudinal dashboard V1.
let trackingSubjects=[]
let trackingRegions=[]
let trackingSubjectId=''
let trackingRegionCode=''
let dashboardSubjectId=''
let dashboardRegionCode=''
let dashboardModality='all'

function trackingScanMatches(scan, subjectId='', regionCode='', modality='all'){
  if(!scan) return false
  if(modality!=='all' && scan.modality!==modality) return false
  const m=scan.metrics||{}
  if(subjectId && m.tracking_subject_id!==subjectId) return false
  if(regionCode && m.tracking_region_code!==regionCode) return false
  return true
}
function trackingLabel(scan){
  const m=scan?.metrics||{}
  const subject=m.tracking_subject_name||'Unassigned'
  const region=m.tracking_region_label||'Legacy / unspecified region'
  return `${subject} · ${region}`
}
function structuredTrackingKey(scan){ return scan?.metrics?.tracking_series_key||null }

// Tighten RGB comparability: subject + region + version + good capture.
const previousComparableRgbTrackingBase=previousComparableRgb
previousComparableRgb=function(scan){
  if(!scan || scan.modality!=='rgb' || !rgbLongitudinalEligible(scan)) return null
  const key=structuredTrackingKey(scan)
  if(!key) return null
  const same=scansOf('rgb'), i=same.findIndex(s=>s.id===scan.id), version=rgbVersion(scan)
  if(i<0) return null
  for(let j=i+1;j<same.length;j++){
    const candidate=same[j]
    if(structuredTrackingKey(candidate)===key && rgbVersion(candidate)===version && rgbLongitudinalEligible(candidate)) return candidate
  }
  return null
}
const previousRgbAnyVersionTrackingBase=previousRgbAnyVersion
previousRgbAnyVersion=function(scan){
  if(!scan || scan.modality!=='rgb') return null
  const key=structuredTrackingKey(scan)
  if(!key) return null
  const same=scansOf('rgb'), i=same.findIndex(s=>s.id===scan.id)
  if(i<0) return null
  for(let j=i+1;j<same.length;j++) if(structuredTrackingKey(same[j])===key) return same[j]
  return null
}
const rgbEligibleTrackingBase=rgbLongitudinalEligible
rgbLongitudinalEligible=function(scan){
  return !!(rgbEligibleTrackingBase(scan) && structuredTrackingKey(scan))
}

// Tighten UV comparability to the new structured identity as well.
const uvEligibleTrackingBase=uvLongitudinalEligible
uvLongitudinalEligible=function(scan){
  return !!(uvEligibleTrackingBase(scan) && structuredTrackingKey(scan))
}
const previousComparableUvTrackingBase=previousComparableUv
previousComparableUv=function(scan){
  if(!uvLongitudinalEligible(scan)) return null
  const same=scansOf('uv'), i=same.findIndex(s=>s.id===scan.id), key=uvComparisonKey(scan), trackingKey=structuredTrackingKey(scan)
  if(i<0) return null
  for(let j=i+1;j<same.length;j++){
    const candidate=same[j]
    if(uvLongitudinalEligible(candidate) && structuredTrackingKey(candidate)===trackingKey && uvComparisonKey(candidate)===key) return candidate
  }
  return null
}

function regionOptionsFor(modality){
  return trackingRegions.filter(r=>!modality || modality==='all' || (r.modalities||[]).includes(modality))
}
function fillSelect(select, rows, value, firstLabel, getValue, getLabel){
  if(!select) return
  select.innerHTML=`<option value="">${firstLabel}</option>`+rows.map(x=>`<option value="${getValue(x)}">${getLabel(x)}</option>`).join('')
  if(rows.some(x=>getValue(x)===value)) select.value=value
}
function populateTrackingControls(){
  fillSelect($('#scanSubjectSelect'),trackingSubjects,trackingSubjectId,'Analysis only / no subject',x=>x.id,x=>x.display_name)
  fillSelect($('#scanRegionSelect'),regionOptionsFor(scanMode),trackingRegionCode,'Analysis only / no region',x=>x.code,x=>x.label)
  if(!regionOptionsFor(scanMode).some(x=>x.code===trackingRegionCode)){
    trackingRegionCode=''
    if($('#scanRegionSelect')) $('#scanRegionSelect').value=''
  }
  fillSelect($('#dashboardSubjectSelect'),trackingSubjects,dashboardSubjectId,'All subjects',x=>x.id,x=>x.display_name)
  fillSelect($('#dashboardRegionSelect'),trackingRegions,dashboardRegionCode,'All regions',x=>x.code,x=>x.label)
  fillSelect($('#historySubjectSelect'),trackingSubjects,dashboardSubjectId,'All subjects',x=>x.id,x=>x.display_name)
  fillSelect($('#historyRegionSelect'),trackingRegions,dashboardRegionCode,'All regions',x=>x.code,x=>x.label)
}

function buildTrackingUI(){
  const capture=$('.capture')
  if(capture && !$('#trackingContext')){
    const box=document.createElement('div')
    box.id='trackingContext';box.className='trackingContext'
    box.innerHTML=`
      <div class="trackingContextHead"><div><span class="eyebrow">TRACKING CONTEXT</span><b>Who and where are you scanning?</b></div><button id="addSubjectBtn" type="button" class="secondaryMini">+ Profile</button></div>
      <div class="trackingFields">
        <label>Subject<select id="scanSubjectSelect"></select></label>
        <label>Region<select id="scanRegionSelect"></select></label>
      </div>
      <small>Choose both to enable longitudinal comparison. Leave both blank for analysis-only.</small>`
    const modes=capture.querySelector('.modes')
    modes.insertAdjacentElement('afterend',box)
  }
  const oldUv=$('#uvSeriesFields'); if(oldUv) oldUv.classList.add('hidden')

  const home=$('#home')
  if(home && !$('#trackingDashboard')){
    const card=document.createElement('div')
    card.id='trackingDashboard';card.className='card trackingDashboard'
    card.innerHTML=`
      <div class="section-head dashboardHead"><div><span class="eyebrow">LONGITUDINAL DASHBOARD</span><h3>Profile & region view</h3></div>
        <div class="dashboardFilters"><select id="dashboardSubjectSelect"></select><select id="dashboardRegionSelect"></select><select id="dashboardModality"><option value="all">All modalities</option><option value="rgb">Phone RGB</option><option value="uv">UV fluorescence</option></select></div>
      </div>
      <div id="dashboardMetrics" class="metrics dashboardMetrics"></div>
      <div id="dashboardSeries" class="dashboardSeries"></div>`
    const hero=home.querySelector('.hero-grid'); hero.insertAdjacentElement('afterend',card)
  }
  const historyCard=$('#history .card')
  if(historyCard && !$('#historyTrackingFilters')){
    const filters=document.createElement('div')
    filters.id='historyTrackingFilters';filters.className='dashboardFilters historyFilters'
    filters.innerHTML=`<select id="historySubjectSelect"></select><select id="historyRegionSelect"></select><select id="historyModality"><option value="all">All modalities</option><option value="rgb">Phone RGB</option><option value="uv">UV fluorescence</option></select>`
    historyCard.querySelector('.section-head').appendChild(filters)
  }
}

async function addSubjectProfile(){
  const name=prompt('Profile name (for example: Nam, Beta user 01, Client A)')
  if(!name?.trim()) return
  try{
    const created=await api('/v1/subjects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:name.trim()})})
    trackingSubjects=await api('/v1/subjects')
    trackingSubjectId=created.id
    populateTrackingControls(); renderTrackingDashboard(); renderHistory()
  }catch(e){showError(e.message)}
}

function bindTrackingUI(){
  $('#addSubjectBtn')?.addEventListener('click',addSubjectProfile)
  $('#scanSubjectSelect')?.addEventListener('change',e=>{trackingSubjectId=e.target.value})
  $('#scanRegionSelect')?.addEventListener('change',e=>{trackingRegionCode=e.target.value})
  $('#dashboardSubjectSelect')?.addEventListener('change',e=>{dashboardSubjectId=e.target.value; syncDashboardFilters(); renderTrackingDashboard(); renderHistory()})
  $('#dashboardRegionSelect')?.addEventListener('change',e=>{dashboardRegionCode=e.target.value; syncDashboardFilters(); renderTrackingDashboard(); renderHistory()})
  $('#dashboardModality')?.addEventListener('change',e=>{dashboardModality=e.target.value; syncDashboardFilters(); renderTrackingDashboard(); renderHistory()})
  $('#historySubjectSelect')?.addEventListener('change',e=>{dashboardSubjectId=e.target.value; syncDashboardFilters(); renderTrackingDashboard(); renderHistory()})
  $('#historyRegionSelect')?.addEventListener('change',e=>{dashboardRegionCode=e.target.value; syncDashboardFilters(); renderTrackingDashboard(); renderHistory()})
  $('#historyModality')?.addEventListener('change',e=>{dashboardModality=e.target.value; syncDashboardFilters(); renderTrackingDashboard(); renderHistory()})
}
function syncDashboardFilters(){
  if($('#dashboardSubjectSelect')) $('#dashboardSubjectSelect').value=dashboardSubjectId
  if($('#dashboardRegionSelect')) $('#dashboardRegionSelect').value=dashboardRegionCode
  if($('#dashboardModality')) $('#dashboardModality').value=dashboardModality
  if($('#historySubjectSelect')) $('#historySubjectSelect').value=dashboardSubjectId
  if($('#historyRegionSelect')) $('#historyRegionSelect').value=dashboardRegionCode
  if($('#historyModality')) $('#historyModality').value=dashboardModality
}

function filteredTrackingScans(){
  return scans.filter(s=>trackingScanMatches(s,dashboardSubjectId,dashboardRegionCode,dashboardModality))
}
function eligibleForTracking(scan){
  if(scan.modality==='rgb') return rgbLongitudinalEligible(scan)
  if(scan.modality==='uv') return uvLongitudinalEligible(scan)
  return false
}
function renderTrackingDashboard(){
  const el=$('#dashboardMetrics'), series=$('#dashboardSeries'); if(!el||!series) return
  const rows=filteredTrackingScans(), eligible=rows.filter(eligibleForTracking), latestRow=rows[0]
  const subjects=new Set(rows.map(s=>s.metrics?.tracking_subject_id).filter(Boolean)).size
  const regions=new Set(rows.map(s=>s.metrics?.tracking_region_code).filter(Boolean)).size
  el.innerHTML=[
    metric('Saved scans',String(rows.length),'matching current filters'),
    metric('Trend eligible',String(eligible.length),'structured + quality compatible'),
    metric('Subjects',String(subjects),'represented in view'),
    metric('Regions',String(regions),'represented in view')
  ].join('')
  if(!rows.length){ series.innerHTML='<div class="empty dashboardEmpty">No scans match these filters yet.</div>'; return }
  const grouped={}
  eligible.forEach(s=>{const key=`${s.modality}|${structuredTrackingKey(s)}`;(grouped[key] ||= []).push(s)})
  const groups=Object.values(grouped).sort((a,b)=>new Date(b[0].created_at)-new Date(a[0].created_at))
  const cards=groups.slice(0,6).map(g=>{
    const first=g[g.length-1], last=g[0], m=last.metrics
    let signal='—',change='Baseline only'
    if(last.modality==='rgb'){
      signal=`${pct(m.redness_area_fraction)} redness`
      if(g.length>1){const d=(m.redness_area_fraction-first.metrics.redness_area_fraction)*100;change=`${signed(d,1)} pp vs first`}
    }else{
      signal=`${m.porphyrin_component_count_proxy} fluorescent spots`
      if(g.length>1){const d=m.porphyrin_component_count_proxy-first.metrics.porphyrin_component_count_proxy;change=`${signed(d,0)} spots vs first`}
    }
    return `<div class="seriesCard"><span>${last.modality.toUpperCase()} · ${m.tracking_region_label||'Region'}</span><b>${m.tracking_subject_name||'Subject'}</b><strong>${signal}</strong><small>${g.length} comparable scan${g.length===1?'':'s'} · ${change}</small></div>`
  }).join('')
  const latestInfo=latestRow?`<div class="dashboardLatest"><span>Latest in view</span><b>${trackingLabel(latestRow)}</b><small>${new Date(latestRow.created_at).toLocaleString()} · ${latestRow.modality.toUpperCase()}</small></div>`:''
  series.innerHTML=latestInfo+(cards?`<div class="seriesGrid">${cards}</div>`:'<div class="empty dashboardEmpty">Scans are saved, but none are longitudinally eligible under these filters yet.</div>')
}

// Add structured context to both multipart scan endpoints.
const apiTrackingBase=api
api=async function(path,options={}){
  if((path==='/v1/uv/analyze'||path==='/v1/rgb/analyze') && options.body instanceof FormData){
    if(trackingSubjectId) options.body.set('subject_id',trackingSubjectId); else options.body.delete('subject_id')
    if(trackingRegionCode) options.body.set('region_code',trackingRegionCode); else options.body.delete('region_code')
  }
  return apiTrackingBase(path,options)
}

// Refresh structured region choices when modality changes.
const applyModeTrackingBase=applyModeUI
applyModeUI=function(){ applyModeTrackingBase(); populateTrackingControls() }

// Filter History using the same dashboard context while preserving click behavior.
const renderHistoryTrackingBase=renderHistory
renderHistory=function(){
  renderHistoryTrackingBase()
  const filtered=filteredTrackingScans(); const ids=new Set(filtered.map(s=>s.id))
  $$('.historyRow').forEach(row=>{row.style.display=ids.has(row.dataset.id)?'grid':'none'})
  if($('#historyTitle')) $('#historyTitle').textContent=`${filtered.length} of ${scans.length} saved scans`
}

// Append structured identity to result screens.
const renderResultTrackingBase=renderResult
renderResult=function(){
  renderResultTrackingBase()
  if(rejectedAttempt || !latest) return
  const m=latest.metrics||{}, body=$('#resultBody'); if(!body) return
  const note=document.createElement('div');note.className='scienceNote trackingIdentityNote'
  if(m.tracking_series_key){
    note.innerHTML=`<b>Tracking identity.</b> ${m.tracking_subject_name||'Subject'} · ${m.tracking_region_label||'Region'}. Longitudinal comparison is restricted to this exact profile/region series plus compatible analysis versions.`
  }else{
    note.innerHTML='<b>Analysis-only identity.</b> This scan has no structured subject/region assignment, so it is excluded from longitudinal profile trends.'
  }
  body.appendChild(note)
}

async function initTrackingV1(){
  buildTrackingUI();bindTrackingUI()
  try{
    ;[trackingSubjects,trackingRegions]=await Promise.all([api('/v1/subjects'),api('/v1/regions')])
    populateTrackingControls();syncDashboardFilters();renderTrackingDashboard();renderHistory()
  }catch(e){showError(`Tracking setup: ${e.message}`)}
}
initTrackingV1()
