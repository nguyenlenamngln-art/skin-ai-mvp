// Phone RGB longitudinal safety layer.
const baseViewSrcV11 = viewSrc
viewSrc = function(scan, view){
  if(scan?.modality==='rgb' && view==='skin') return scan.media.skin_region || scan.media.overlay
  return baseViewSrcV11(scan, view)
}

function rgbVersion(scan){ if(!scan || scan.modality!=='rgb') return null; return String(scan.metrics?.rgb_engine_version || 'legacy-v1') }
function rgbVersionLabel(scan){ const v=rgbVersion(scan); return v==='legacy-v1' ? 'RGB V1 legacy' : `RGB V${v}` }
function rgbLongitudinalEligible(scan){
  if(!scan || scan.modality!=='rgb') return false
  if(scan.metrics?.longitudinal_eligible !== undefined) return !!scan.metrics.longitudinal_eligible
  return scan.metrics?.capture_quality === 'good'
}
function previousComparableRgb(scan){
  if(!scan || scan.modality!=='rgb' || !rgbLongitudinalEligible(scan)) return null
  const same=scansOf('rgb'), i=same.findIndex(s=>s.id===scan.id), version=rgbVersion(scan)
  if(i<0) return null
  for(let j=i+1;j<same.length;j++) if(rgbVersion(same[j])===version && rgbLongitudinalEligible(same[j])) return same[j]
  return null
}
function previousRgbAnyVersion(scan){
  if(!scan || scan.modality!=='rgb') return null
  const same=scansOf('rgb'), i=same.findIndex(s=>s.id===scan.id)
  return i>=0 && i<same.length-1 ? same[i+1] : null
}
function scoreDisplay(value){ return Number.isFinite(value)?`${Math.round(value)}/100`:'Not measured' }
function scoreNote(value, fallback){ return Number.isFinite(value)?fallback:'not available in this capture protocol' }

const basePreviousSameModalityV12 = previousSameModality
previousSameModality = function(scan){ if(scan?.modality==='rgb') return previousComparableRgb(scan); return basePreviousSameModalityV12(scan) }

const baseRenderV12 = render
render = function(){
  baseRenderV12()
  if(latest?.modality==='rgb'){
    const m=latest.metrics, comparable=previousComparableRgb(latest), priorAny=previousRgbAnyVersion(latest)
    const score=Number.isFinite(m.capture_quality_score)?` · quality ${m.capture_quality_score}/100`:''
    $('#latestCopy').textContent=`Phone ${rgbVersionLabel(latest)} baseline · ${m.capture_quality}${score}.`
    if(!rgbLongitudinalEligible(latest)) $('#insightText').textContent='This scan was saved for review but is excluded from longitudinal deltas and trends. Retake it using the capture guidance for a comparable baseline.'
    else if(!comparable && priorAny && rgbVersion(priorAny)!==rgbVersion(latest)) $('#insightText').textContent=`Analysis changed from ${rgbVersionLabel(priorAny)} to ${rgbVersionLabel(latest)}. This scan starts a new baseline; cross-version deltas are intentionally hidden.`
  }
}

const baseRenderTrendV12 = renderTrend
renderTrend = function(){
  if(!latest || latest.modality!=='rgb') return baseRenderTrendV12()
  const version=rgbVersion(latest)
  const rows=trends.filter(x=>x.modality==='rgb' && String(x.rgb_engine_version || 'legacy-v1')===version && x.longitudinal_eligible!==false)
  const vals=rows.map(x=>x.redness_area_fraction).filter(Number.isFinite), svg=$('#trendSvg'), empty=$('#trendEmpty')
  $('#trendTitle').textContent=`RGB redness-area trend · ${rgbVersionLabel(latest)}`
  if(vals.length<2){svg.innerHTML='';empty.classList.remove('hidden');empty.textContent='Run at least two good-quality RGB scans with the same analysis version to see a trend.';return}
  empty.classList.add('hidden')
  const mn=Math.min(...vals),mx=Math.max(...vals),span=Math.max(0.000001,mx-mn)
  const pts=vals.map((v,i)=>`${20+i*(560/(vals.length-1))},${140-((v-mn)/span)*105}`).join(' ')
  svg.innerHTML=`<line x1="20" y1="140" x2="580" y2="140" stroke="#d8dbd3"/><polyline points="${pts}" fill="none" stroke="#496956" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>`
}

renderHistory = function(){
  $('#historyTitle').textContent=`${scans.length} saved scans`
  $('#historyList').innerHTML=scans.length?scans.map(s=>{
    const m=s.metrics, thumb=s.media.overlay||s.media.original
    const summary=s.modality==='rgb'?`${pct(m.redness_area_fraction)} redness · ${pct(m.pigmentation_area_fraction)} pigment`:`${m.porphyrin_component_count_proxy} spots · ${pct(m.artifact_area_fraction)} artifacts`
    const version=s.modality==='rgb'?` · ${rgbVersionLabel(s)}`:''
    const eligibility=s.modality==='rgb' && !rgbLongitudinalEligible(s)?' · not in trend':''
    const score=s.modality==='rgb' && Number.isFinite(m.capture_quality_score)?` ${m.capture_quality_score}/100`:''
    return `<button class="historyRow" data-id="${s.id}"><img src="${thumb}"/><div><b>${new Date(s.created_at).toLocaleString()}</b><span>${s.modality.toUpperCase()}${version}${eligibility} · ${s.source_name||'scan'}</span></div><div class="historyStat"><b>${s.modality==='rgb'?(m.capture_quality||'—')+score:m.porphyrin_component_count_proxy}</b><span>${summary}</span></div><span>›</span></button>`
  }).join(''):'<div class="empty">No scans yet.</div>'
  $$('.historyRow').forEach(b=>b.onclick=()=>{rejectedAttempt=null;showError('');latest=scans.find(s=>s.id===b.dataset.id);scanMode=latest.modality;resultView='combined';applyModeUI();renderResult();setTab('scan')})
}

const baseRenderResultV12 = renderResult
renderResult = function(){
  if(rejectedAttempt && rejectedAttempt.mode===scanMode) return baseRenderResultV12()
  if(!latest || latest.modality!=='rgb') return baseRenderResultV12()
  const body=$('#resultBody'), date=$('#resultDate'), badge=$('#compareBadge')
  body.className=''; date.textContent=new Date(latest.created_at).toLocaleString()
  const prev=previousComparableRgb(latest), priorAny=previousRgbAnyVersion(latest), m=latest.metrics, eligible=rgbLongitudinalEligible(latest)
  if(!eligible){ badge.textContent='Saved · not eligible for trend'; badge.className='compareBadge warn' }
  else if(prev){
    const d=(m.redness_area_fraction-prev.metrics.redness_area_fraction)*100
    badge.textContent=Math.abs(d)<0.05?'RGB stable vs comparable scan':`${d<0?'↓':'↑'} ${Math.abs(d).toFixed(1)} pp redness area`; badge.className=`compareBadge ${d<0?'good':d>0?'warn':''}`
  } else if(priorAny && rgbVersion(priorAny)!==rgbVersion(latest)){ badge.textContent='New baseline after analysis update'; badge.className='compareBadge' }
  else { badge.textContent='New RGB baseline'; badge.className='compareBadge' }

  if(!['original','skin','redness','pigmentation','combined'].includes(resultView)) resultView='combined'
  const tabs=[['original','Original'],['skin','Skin region'],['redness','Redness'],['pigmentation','Pigment'],['combined','Combined']]
  const deltaRed=prev?deltaText(m.redness_area_fraction,prev.metrics.redness_area_fraction,'pct'):''
  const deltaPigment=prev?deltaText(m.pigmentation_area_fraction,prev.metrics.pigmentation_area_fraction,'pct'):''
  const score=Number.isFinite(m.capture_quality_score)?`${m.capture_quality_score}/100`:'Not measured'
  const framing=m.quality_subscores?.framing
  const lighting=m.quality_subscores?.lighting
  const segmentation=m.quality_subscores?.segmentation
  const ev=Number.isFinite(m.reference_exposure_delta_ev)?`${m.reference_exposure_delta_ev>0?'+':''}${m.reference_exposure_delta_ev.toFixed(2)} EV vs baseline`:(m.reference_capture_used===false?'no reference yet':Number.isFinite(lighting)?'absolute exposure check':'not measured by this protocol')
  const guidance=(m.quality_guidance||[]).map(x=>`<li>${x}</li>`).join('')
  const qualityNote=eligible?'Eligible for longitudinal comparison.':'Saved for review only; excluded from longitudinal deltas and trends.'
  body.innerHTML=`
    <div class="viewTabs rgbV11Tabs">${tabs.map(([k,l])=>`<button data-result-view="${k}" class="${resultView===k?'active':''}">${l}</button>`).join('')}</div>
    <div class="analysisImage ${resultView}"><img src="${viewSrc(latest,resultView)}" alt="${resultView} analysis"/>${resultView==='combined'?`<div class="legend"><span><i class="dot red"></i>local redness</span><span><i class="dot violet"></i>local pigmentation</span><span><i class="dot green"></i>analyzed skin boundary</span></div>`:''}</div>
    <div class="analysisMetrics">
      ${metric('Redness area',pct(m.redness_area_fraction),'relative analyzed skin',deltaRed)}
      ${metric('Pigmented area',pct(m.pigmentation_area_fraction),'relative analyzed skin',deltaPigment)}
      ${metric('Texture index',(m.texture_index_proxy||0).toFixed(3),'luminance high-frequency proxy')}
      ${metric('Capture quality',m.capture_quality||'—',`score ${score}`)}
      ${metric('Framing',scoreDisplay(framing),scoreNote(framing,'face size in frame'))}
      ${metric('Lighting',scoreDisplay(lighting),Number.isFinite(lighting)?ev:'not available in this capture protocol')}
      ${metric('Segmentation',scoreDisplay(segmentation),scoreNote(segmentation,'skin-boundary stability'))}
    </div>
    <div class="scienceNote"><b>Capture protocol ${m.capture_protocol_version||'legacy'}.</b> ${qualityNote}${guidance?`<ul style="margin:8px 0 0 18px;padding:0">${guidance}</ul>`:''}</div>
    <div class="scienceNote"><b>Phone ${rgbVersionLabel(latest)} research measurement.</b> RGB deltas and trends only use same-version, good-quality captures. These remain relative visible-light proxies, not diagnoses or substitutes for polarized/UV imaging.</div>`
  $$('[data-result-view]').forEach(b=>b.onclick=()=>{resultView=b.dataset.resultView;renderResult()})
}
