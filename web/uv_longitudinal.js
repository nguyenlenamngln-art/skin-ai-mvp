// UV longitudinal comparison integrity V1.
// UV analysis is allowed without a series, but deltas/trends require an explicit
// subject label + anatomical site and matching analysis/model/validator metadata.

function uvLongitudinalEligible(scan){
  return !!(scan && scan.modality==='uv' && scan.metrics?.uv_longitudinal_eligible===true && scan.metrics?.uv_comparison_key)
}
function uvComparisonKey(scan){ return scan?.modality==='uv' ? (scan.metrics?.uv_comparison_key || null) : null }
function previousComparableUv(scan){
  if(!uvLongitudinalEligible(scan)) return null
  const same=scansOf('uv'), i=same.findIndex(s=>s.id===scan.id), key=uvComparisonKey(scan)
  if(i<0) return null
  for(let j=i+1;j<same.length;j++) if(uvLongitudinalEligible(same[j]) && uvComparisonKey(same[j])===key) return same[j]
  return null
}

const basePreviousSameModalityUVSeries = previousSameModality
previousSameModality = function(scan){
  if(scan?.modality==='uv') return previousComparableUv(scan)
  return basePreviousSameModalityUVSeries(scan)
}

// Add explicit comparison-series fields without changing the base capture card.
const tips=document.querySelector('#captureTips')
if(tips){
  const fields=document.createElement('div')
  fields.id='uvSeriesFields'
  fields.style.cssText='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px'
  fields.innerHTML=`
    <label style="display:grid;gap:5px;font-size:12px;color:#59625b">Subject label
      <input id="uvSubjectLabel" maxlength="80" placeholder="e.g. beta-user-01" style="padding:10px;border:1px solid #d7d9d1;border-radius:10px;background:#fff" />
    </label>
    <label style="display:grid;gap:5px;font-size:12px;color:#59625b">Anatomical site
      <input id="uvAnatomicalSite" maxlength="80" placeholder="e.g. left cheek" style="padding:10px;border:1px solid #d7d9d1;border-radius:10px;background:#fff" />
    </label>
    <small style="grid-column:1/-1;color:#687169">Both fields are required only for longitudinal UV comparison. Leave blank for analysis-only scans.</small>`
  tips.parentNode.insertBefore(fields,tips.nextSibling)
}

function updateUvSeriesVisibility(){
  const el=document.querySelector('#uvSeriesFields')
  if(el) el.style.display=scanMode==='uv'?'grid':'none'
}

const baseApplyModeUIUVSeries=applyModeUI
applyModeUI=function(){ baseApplyModeUIUVSeries(); updateUvSeriesVisibility() }
updateUvSeriesVisibility()

// Enrich only UV multipart uploads with comparison-series metadata.
const baseApiUVSeries=api
api=async function(path,options={}){
  if(path==='/v1/uv/analyze' && options.body instanceof FormData){
    const subject=(document.querySelector('#uvSubjectLabel')?.value||'').trim()
    const site=(document.querySelector('#uvAnatomicalSite')?.value||'').trim()
    if(subject) options.body.set('subject_label',subject)
    if(site) options.body.set('anatomical_site',site)
  }
  return baseApiUVSeries(path,options)
}

const baseRenderTrendUVSeries=renderTrend
renderTrend=function(){
  if(!latest || latest.modality!=='uv') return baseRenderTrendUVSeries()
  const key=uvComparisonKey(latest), svg=$('#trendSvg'), empty=$('#trendEmpty')
  $('#trendTitle').textContent='UV porphyrin spot trend'
  if(!key){
    svg.innerHTML='';empty.classList.remove('hidden')
    empty.textContent='This UV scan is analysis-only. Add the same subject label and anatomical site to repeat scans to create a longitudinal series.'
    return
  }
  const rows=trends.filter(x=>x.modality==='uv' && x.uv_comparison_key===key && x.uv_longitudinal_eligible===true)
  const vals=rows.map(x=>x.porphyrin_component_count_proxy).filter(Number.isFinite)
  if(vals.length<2){
    svg.innerHTML='';empty.classList.remove('hidden')
    empty.textContent='Run at least two UV scans in this exact comparison series to see a trend.'
    return
  }
  empty.classList.add('hidden')
  const mn=Math.min(...vals),mx=Math.max(...vals),span=Math.max(1,mx-mn)
  const pts=vals.map((v,i)=>`${20+i*(560/(vals.length-1))},${140-((v-mn)/span)*105}`).join(' ')
  svg.innerHTML=`<line x1="20" y1="140" x2="580" y2="140" stroke="#d8dbd3"/><polyline points="${pts}" fill="none" stroke="#496956" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>`
}

const baseRenderResultUVSeries=renderResult
renderResult=function(){
  if(rejectedAttempt && rejectedAttempt.mode==='uv') return baseRenderResultUVSeries()
  baseRenderResultUVSeries()
  if(!latest || latest.modality!=='uv') return
  const badge=$('#compareBadge'), m=latest.metrics, prev=previousComparableUv(latest)
  if(!uvLongitudinalEligible(latest)){
    badge.textContent='Analysis only · no comparison series'
    badge.className='compareBadge'
  } else if(!prev){
    badge.textContent='New UV series baseline'
    badge.className='compareBadge'
  } else {
    const d=m.porphyrin_component_count_proxy-prev.metrics.porphyrin_component_count_proxy
    badge.textContent=Math.abs(d)<1?'UV stable vs comparable scan':`${d<0?'↓':'↑'} ${Math.abs(d)} spots vs comparable scan`
    badge.className=`compareBadge ${d<0?'good':d>0?'warn':''}`
  }
  const note=document.createElement('div')
  note.className='scienceNote'
  if(uvLongitudinalEligible(latest)){
    note.innerHTML=`<b>UV comparison series.</b> Subject: ${m.uv_subject_label||'—'} · Site: ${m.uv_anatomical_site||'—'}. Deltas require the same series, UV analysis version, model signature, and validator profile.`
  }else{
    note.innerHTML='<b>Analysis-only UV record.</b> No longitudinal delta is shown because a subject label and anatomical site were not both supplied. This prevents unrelated UV crops from being compared.'
  }
  $('#resultBody').appendChild(note)
}
