// Session Comparison UX V1.1 — presentation-only override.
function comparisonMedia(scan){
  if(!scan?.media) return null
  return scan.media.overlay||scan.media.original||scan.media.skin_region||null
}
function comparisonMetricRows(scan){
  if(!scan) return []
  const m=scan.metrics||{}
  if(scan.modality==='uv'){
    return [
      ['Fluorescent spots',String(m.porphyrin_component_count_proxy??'—')],
      ['Fluorescent area',pct(m.porphyrin_area_fraction_valid||0)],
    ]
  }
  return [
    ['Redness area',pct(m.redness_area_fraction||0)],
    ['Pigmented area',pct(m.pigmentation_area_fraction||0)],
  ]
}
function comparisonMetricBlock(scan,label){
  const rows=comparisonMetricRows(scan)
  return `<div class="comparisonMetricBlock"><small>${label}</small>${rows.map(([k,v])=>`<div><span>${k}</span><b>${v}</b></div>`).join('')}</div>`
}
function comparisonThumb(scan,label,region){
  const src=comparisonMedia(scan)
  if(!src) return `<div class="comparisonThumb emptyThumb"><small>${label}</small><span>No image</span></div>`
  return `<figure class="comparisonThumb"><figcaption>${label}</figcaption><img src="${src}" alt="${region} ${label.toLowerCase()} analysis"/></figure>`
}
function comparisonDeltaClass(status){ return ['stable','higher','lower','mixed','not_comparable'].includes(status)?status:'not_comparable' }

const renderSessionHistoryDetailV10=renderSessionHistoryDetail
renderSessionHistoryDetail=function(){
  const detail=$('#sessionHistoryDetail'), list=$('#sessionHistoryList')
  if(!detail||!list) return renderSessionHistoryDetailV10()
  const current=sessionHistoryRows.find(s=>s.id===selectedHistorySessionId)
  if(!current) return renderSessionHistoryDetailV10()
  const candidates=previousCompatibleSessions(current)
  const previous=selectedComparisonSessionId?candidates.find(s=>s.id===selectedComparisonSessionId):candidates[0]
  if(previous) selectedComparisonSessionId=previous.id
  const regions=(current.plan||[]).map(code=>compareRegionPair(current,previous,code))
  const counts={stable:0,higher:0,lower:0,mixed:0,not_comparable:0}
  regions.forEach(r=>counts[r.status]=(counts[r.status]||0)+1)
  const options=candidates.map(s=>`<option value="${s.id}" ${previous?.id===s.id?'selected':''}>${sessionDate(s).toLocaleString()}</option>`).join('')
  const summaryItems=[
    ['Stable',counts.stable,'stable'],['Higher',counts.higher,'higher'],['Lower',counts.lower,'lower'],['Mixed',counts.mixed,'mixed']
  ]
  if(counts.not_comparable) summaryItems.push(['Not comparable',counts.not_comparable,'not_comparable'])
  detail.innerHTML=`
    <div class="comparisonTopbar">
      <button type="button" class="secondaryMini" id="backToSessions">← Sessions</button>
      <div><span class="eyebrow">SESSION COMPARISON</span><h3>${sessionSubjectName(current)} · ${current.modality.toUpperCase()}</h3></div>
    </div>
    <div class="comparisonVisitBar">
      <div class="comparisonVisit"><small>Current visit</small><b>${sessionDate(current).toLocaleString()}</b></div>
      <div class="comparisonVisit comparisonVisitSelect"><label>Compared with<select id="sessionCompareSelect"><option value="">No comparison / baseline</option>${options}</select></label></div>
    </div>
    <div class="comparisonSummaryV11">
      <div><span class="eyebrow">VISIT SUMMARY</span><b>${previous?'Region-by-region measured change':'Session baseline'}</b><small>${previous?'Compared only with the selected compatible visit.':'No earlier compatible visit selected.'}</small></div>
      <div class="comparisonSummaryStats">${summaryItems.map(([label,value,cls])=>`<div class="comparisonSummaryStat ${cls}"><strong>${value}</strong><span>${label}</span></div>`).join('')}</div>
    </div>
    <div class="comparisonRegionList">${regions.map(r=>{
      const c=r.current,p=r.previous,region=sessionRegionLabel(r.regionCode)
      const delta=previous?regionDeltaText(r,current.modality):'New session baseline'
      return `<section class="comparisonRegionCard ${comparisonDeltaClass(r.status)}">
        <div class="comparisonRegionHead"><div><span class="eyebrow">${region.toUpperCase()}</span><h4>${region}</h4></div><em>${r.label}</em></div>
        <div class="comparisonRegionMetrics">
          ${comparisonMetricBlock(p,'Previous')}
          <div class="comparisonDeltaBox"><small>Change</small><b>${delta}</b></div>
          ${comparisonMetricBlock(c,'Current')}
        </div>
        <div class="comparisonThumbGrid">
          ${comparisonThumb(p,'Previous',region)}
          ${comparisonThumb(c,'Current',region)}
        </div>
      </section>`
    }).join('')}</div>
    <div class="scienceNote"><b>Session comparison.</b> Regions are paired only when subject, structured region, and compatible analysis pipeline match. Higher/lower describes measured image signals only and is not a clinical interpretation.</div>`
  list.classList.add('hidden');detail.classList.remove('hidden')
  $('#backToSessions').onclick=()=>{selectedHistorySessionId=null;selectedComparisonSessionId=null;renderSessionHistory()}
  $('#sessionCompareSelect').onchange=e=>{selectedComparisonSessionId=e.target.value||null;renderSessionHistoryDetail()}
}
