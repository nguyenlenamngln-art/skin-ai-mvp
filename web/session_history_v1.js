// Session History & Comparison V1
let sessionHistoryRows=[]
let historyMode='sessions'
let selectedHistorySessionId=null
let selectedComparisonSessionId=null

function sessionCompleted(s){ return s && (s.status==='complete' || s.progress?.complete) }
function sessionDate(s){ return new Date(s.completed_at||s.created_at) }
function sessionSubjectName(s){ return s?.subject?.display_name||'Unknown subject' }
function sessionItemScan(item){ return item?.scan||null }
function sessionRegionMap(s){
  const map={}
  ;(s?.items||[]).forEach(item=>{ if(item.region_code && item.scan) map[item.region_code]=item.scan })
  return map
}
function sessionMatchesFilters(s){
  if(!s) return false
  if(dashboardSubjectId && s.subject_id!==dashboardSubjectId) return false
  if(dashboardModality!=='all' && s.modality!==dashboardModality) return false
  if(dashboardRegionCode && !(s.items||[]).some(x=>x.region_code===dashboardRegionCode)) return false
  return true
}
function scanPairComparable(current,previous){
  if(!current||!previous||current.modality!==previous.modality) return false
  const cm=current.metrics||{}, pm=previous.metrics||{}
  if(!cm.tracking_series_key || cm.tracking_series_key!==pm.tracking_series_key) return false
  if(current.modality==='uv'){
    return cm.uv_longitudinal_eligible===true && pm.uv_longitudinal_eligible===true && !!cm.uv_comparison_key && cm.uv_comparison_key===pm.uv_comparison_key
  }
  return cm.longitudinal_eligible===true && pm.longitudinal_eligible===true && String(cm.rgb_engine_version)===String(pm.rgb_engine_version)
}
function sessionsComparable(current,previous){
  if(!sessionCompleted(current)||!sessionCompleted(previous)) return false
  if(current.id===previous.id || current.subject_id!==previous.subject_id || current.modality!==previous.modality) return false
  if(sessionDate(previous)>=sessionDate(current)) return false
  const c=sessionRegionMap(current), p=sessionRegionMap(previous)
  const codes=(current.plan||[]).filter(code=>c[code]&&p[code])
  return codes.some(code=>scanPairComparable(c[code],p[code]))
}
function previousCompatibleSessions(current){
  return sessionHistoryRows
    .filter(s=>sessionsComparable(current,s))
    .sort((a,b)=>sessionDate(b)-sessionDate(a))
}
function statusFromDelta(delta,threshold){
  if(Math.abs(delta)<=threshold) return 'stable'
  return delta>0?'higher':'lower'
}
function compareRegionPair(current,previous,regionCode){
  const c=sessionRegionMap(current)[regionCode], p=sessionRegionMap(previous)[regionCode]
  if(!scanPairComparable(c,p)) return {regionCode,status:'not_comparable',label:'Not comparable',current:c,previous:p}
  const cm=c.metrics||{}, pm=p.metrics||{}
  if(current.modality==='uv'){
    const spots=(cm.porphyrin_component_count_proxy||0)-(pm.porphyrin_component_count_proxy||0)
    const area=((cm.porphyrin_area_fraction_valid||0)-(pm.porphyrin_area_fraction_valid||0))*100
    const s1=statusFromDelta(spots,1), s2=statusFromDelta(area,0.5)
    let status='mixed'
    if(s1==='stable'&&s2==='stable') status='stable'
    else if((s1==='higher'||s1==='stable')&&(s2==='higher'||s2==='stable')) status='higher'
    else if((s1==='lower'||s1==='stable')&&(s2==='lower'||s2==='stable')) status='lower'
    return {regionCode,status,label:status==='stable'?'Stable':status==='higher'?'Higher measured signal':status==='lower'?'Lower measured signal':'Mixed change',current:c,previous:p,spotDelta:spots,areaDeltaPp:area}
  }
  const red=((cm.redness_area_fraction||0)-(pm.redness_area_fraction||0))*100
  const pigment=((cm.pigmentation_area_fraction||0)-(pm.pigmentation_area_fraction||0))*100
  const s1=statusFromDelta(red,0.5), s2=statusFromDelta(pigment,0.5)
  let status='mixed'
  if(s1==='stable'&&s2==='stable') status='stable'
  else if((s1==='higher'||s1==='stable')&&(s2==='higher'||s2==='stable')) status='higher'
  else if((s1==='lower'||s1==='stable')&&(s2==='lower'||s2==='stable')) status='lower'
  return {regionCode,status,label:status==='stable'?'Stable':status==='higher'?'Higher measured signal':status==='lower'?'Lower measured signal':'Mixed change',current:c,previous:p,redDeltaPp:red,pigmentDeltaPp:pigment}
}
function sessionHeadline(session){
  const n=session.items?.length||0
  const mode=session.modality==='uv'?'UV':'Phone RGB'
  return `${n} capture${n===1?'':'s'} · ${mode}`
}
function buildSessionHistoryUI(){
  const card=$('#history .card')
  if(!card||$('#sessionHistoryShell')) return
  const shell=document.createElement('div')
  shell.id='sessionHistoryShell'
  shell.className='sessionHistoryShell'
  shell.innerHTML=`
    <div class="historyModeTabs">
      <button type="button" class="active" data-history-mode="sessions">Sessions</button>
      <button type="button" data-history-mode="scans">Individual scans</button>
    </div>
    <div id="sessionHistoryList" class="sessionHistoryList"></div>
    <div id="sessionHistoryDetail" class="sessionHistoryDetail hidden"></div>`
  const filters=$('#historyTrackingFilters')
  if(filters) filters.insertAdjacentElement('afterend',shell)
  else card.querySelector('.section-head').insertAdjacentElement('afterend',shell)
  $$('[data-history-mode]').forEach(btn=>btn.onclick=()=>{historyMode=btn.dataset.historyMode;selectedHistorySessionId=null;selectedComparisonSessionId=null;renderSessionHistory()})
}
function renderSessionHistoryList(rows){
  const list=$('#sessionHistoryList')
  if(!list) return
  if(!rows.length){list.innerHTML='<div class="empty">No completed sessions match these filters yet.</div>';return}
  list.innerHTML=rows.map(s=>{
    const complete=sessionCompleted(s)
    const prev=previousCompatibleSessions(s)[0]
    const comparison=prev?'Previous compatible visit available':'Baseline visit'
    return `<button type="button" class="sessionHistoryRow" data-session-history-id="${s.id}">
      <div class="sessionHistoryIcon">${s.modality==='uv'?'UV':'RGB'}</div>
      <div class="sessionHistoryMain"><b>${sessionSubjectName(s)}</b><span>${sessionDate(s).toLocaleString()}</span><small>${sessionHeadline(s)} · ${comparison}</small></div>
      <div class="sessionHistoryState"><b>${complete?'Complete':'In progress'}</b><span>${s.items?.length||0}/${s.plan?.length||0} regions</span></div><span>›</span>
    </button>`
  }).join('')
  $$('[data-session-history-id]').forEach(btn=>btn.onclick=()=>{selectedHistorySessionId=btn.dataset.sessionHistoryId;selectedComparisonSessionId=null;renderSessionHistoryDetail()})
}
function regionCurrentText(scan){
  if(!scan) return '—'
  const m=scan.metrics||{}
  if(scan.modality==='uv') return `${m.porphyrin_component_count_proxy??'—'} spots · ${pct(m.porphyrin_area_fraction_valid||0)} area`
  return `${pct(m.redness_area_fraction||0)} redness · ${pct(m.pigmentation_area_fraction||0)} pigment`
}
function regionDeltaText(cmp,modality){
  if(cmp.status==='not_comparable') return 'Pipeline or identity not compatible'
  if(modality==='uv') return `${signed(cmp.spotDelta,0)} spots · ${signed(cmp.areaDeltaPp,1)} pp area`
  return `${signed(cmp.redDeltaPp,1)} pp redness · ${signed(cmp.pigmentDeltaPp,1)} pp pigment`
}
function renderSessionHistoryDetail(){
  const detail=$('#sessionHistoryDetail'), list=$('#sessionHistoryList')
  if(!detail||!list) return
  const current=sessionHistoryRows.find(s=>s.id===selectedHistorySessionId)
  if(!current){detail.classList.add('hidden');list.classList.remove('hidden');return}
  const candidates=previousCompatibleSessions(current)
  const previous=selectedComparisonSessionId?candidates.find(s=>s.id===selectedComparisonSessionId):candidates[0]
  if(previous) selectedComparisonSessionId=previous.id
  const regions=(current.plan||[]).map(code=>compareRegionPair(current,previous,code))
  const counts={stable:0,higher:0,lower:0,mixed:0,not_comparable:0}
  regions.forEach(r=>counts[r.status]=(counts[r.status]||0)+1)
  const summary=previous
    ? [counts.stable&&`${counts.stable} stable`,counts.higher&&`${counts.higher} higher`,counts.lower&&`${counts.lower} lower`,counts.mixed&&`${counts.mixed} mixed`,counts.not_comparable&&`${counts.not_comparable} not comparable`].filter(Boolean).join(' · ')
    : 'No earlier compatible session. This visit is the session baseline.'
  const options=candidates.map(s=>`<option value="${s.id}" ${previous?.id===s.id?'selected':''}>${sessionDate(s).toLocaleString()}</option>`).join('')
  detail.innerHTML=`
    <div class="sessionDetailHead"><button type="button" class="secondaryMini" id="backToSessions">← Sessions</button><div><span class="eyebrow">SESSION RECORD</span><h3>${sessionSubjectName(current)} · ${current.modality.toUpperCase()}</h3><small>${sessionDate(current).toLocaleString()}</small></div></div>
    <div class="sessionCompareControls"><label>Compare with<select id="sessionCompareSelect"><option value="">No comparison / baseline</option>${options}</select></label><div class="sessionCompareSummary"><b>${previous?'Visit-to-visit comparison':'Session baseline'}</b><span>${summary}</span></div></div>
    <div class="sessionCompareGrid">${regions.map(r=>{
      const c=r.current, p=r.previous
      return `<div class="sessionCompareCard ${r.status}"><div class="sessionCompareCardHead"><span>${sessionRegionLabel(r.regionCode)}</span><em>${r.label}</em></div><div class="sessionCompareColumns"><div><small>Previous</small><b>${p?regionCurrentText(p):'—'}</b></div><div><small>Current</small><b>${c?regionCurrentText(c):'—'}</b></div></div><small class="sessionDelta">${previous?regionDeltaText(r,current.modality):'New session baseline'}</small>${c?.media?.overlay?`<img src="${c.media.overlay}" alt="${sessionRegionLabel(r.regionCode)} current analysis"/>`:''}</div>`
    }).join('')}</div>
    <div class="scienceNote"><b>Session comparison.</b> Regions are paired only when subject, structured region, and compatible analysis pipeline match. Higher/lower describes measured image signals only and is not a clinical interpretation.</div>`
  list.classList.add('hidden');detail.classList.remove('hidden')
  $('#backToSessions').onclick=()=>{selectedHistorySessionId=null;selectedComparisonSessionId=null;renderSessionHistory()}
  $('#sessionCompareSelect').onchange=e=>{selectedComparisonSessionId=e.target.value||null;renderSessionHistoryDetail()}
}
function renderSessionHistory(){
  buildSessionHistoryUI()
  const sessionShell=$('#sessionHistoryShell'), scanList=$('#historyList'), title=$('#historyTitle')
  if(!sessionShell||!scanList) return
  $$('[data-history-mode]').forEach(b=>b.classList.toggle('active',b.dataset.historyMode===historyMode))
  if(historyMode==='scans'){
    sessionShell.classList.add('showScans');$('#sessionHistoryList')?.classList.add('hidden');$('#sessionHistoryDetail')?.classList.add('hidden');scanList.classList.remove('hidden')
    if(title) title.textContent=`${filteredTrackingScans().length} of ${scans.length} saved scans`
    return
  }
  sessionShell.classList.remove('showScans');scanList.classList.add('hidden')
  const rows=sessionHistoryRows.filter(sessionCompleted).filter(sessionMatchesFilters).sort((a,b)=>sessionDate(b)-sessionDate(a))
  if(title) title.textContent=`${rows.length} completed session${rows.length===1?'':'s'}`
  if(selectedHistorySessionId) renderSessionHistoryDetail()
  else {$('#sessionHistoryDetail')?.classList.add('hidden');$('#sessionHistoryList')?.classList.remove('hidden');renderSessionHistoryList(rows)}
}
async function refreshSessionHistory(){
  try{sessionHistoryRows=await api('/v1/sessions?limit=100');renderSessionHistory()}catch(e){showError(`Session history: ${e.message}`)}
}

const renderHistorySessionBase=renderHistory
renderHistory=function(){renderHistorySessionBase();renderSessionHistory()}

// Existing tracking filters should rerender session history too.
;['dashboardSubjectSelect','dashboardRegionSelect','dashboardModality','historySubjectSelect','historyRegionSelect','historyModality'].forEach(id=>{
  setTimeout(()=>{$(`#${id}`)?.addEventListener('change',()=>renderSessionHistory())},0)
})

buildSessionHistoryUI()
refreshSessionHistory()
