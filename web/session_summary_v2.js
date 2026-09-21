// Session Summary V2 — deterministic, non-diagnostic interpretation for completed sessions.
function summaryPreviousComparable(current){
  if(!current?.metrics?.tracking_series_key) return null
  const cm=current.metrics
  return scans
    .filter(s=>s.id!==current.id && s.modality===current.modality && s.created_at<current.created_at)
    .filter(s=>s.metrics?.tracking_series_key===cm.tracking_series_key)
    .filter(s=>s.metrics?.scan_session_id!==cm.scan_session_id)
    .filter(s=>{
      const pm=s.metrics||{}
      if(current.modality==='uv') return cm.uv_longitudinal_eligible===true && pm.uv_longitudinal_eligible===true && cm.uv_comparison_key && cm.uv_comparison_key===pm.uv_comparison_key
      return cm.longitudinal_eligible===true && pm.longitudinal_eligible===true && String(cm.rgb_engine_version)===String(pm.rgb_engine_version)
    })
    .sort((a,b)=>b.created_at.localeCompare(a.created_at))[0]||null
}
function summaryDirection(value,threshold){ return value>threshold?1:value<-threshold?-1:0 }
function sessionRegionComparison(item,session){
  const current=item.scan || scans.find(s=>s.id===item.scan_id)
  if(!current) return {status:'baseline',label:'New baseline',current:null,previous:null,deltas:{}}
  const previous=summaryPreviousComparable(current)
  const cm=current.metrics||{}, pm=previous?.metrics||{}
  if(!previous) return {status:'baseline',label:'New baseline',current,previous:null,deltas:{}}
  if(session.modality==='uv'){
    const spots=(Number(cm.porphyrin_component_count_proxy)||0)-(Number(pm.porphyrin_component_count_proxy)||0)
    const area=((Number(cm.porphyrin_area_fraction_valid)||0)-(Number(pm.porphyrin_area_fraction_valid)||0))*100
    const sd=summaryDirection(spots,1), ad=summaryDirection(area,.5)
    let status='mixed',label='Mixed change'
    if(sd===0&&ad===0){status='stable';label='Stable'}
    else if(sd>=0&&ad>=0){status='higher';label='Higher measured signal'}
    else if(sd<=0&&ad<=0){status='lower';label='Lower measured signal'}
    return {status,label,current,previous,deltas:{spots,area}}
  }
  const redness=((Number(cm.redness_area_fraction)||0)-(Number(pm.redness_area_fraction)||0))*100
  const pigment=((Number(cm.pigmentation_area_fraction)||0)-(Number(pm.pigmentation_area_fraction)||0))*100
  const rd=summaryDirection(redness,.5), pd=summaryDirection(pigment,.5)
  let status='mixed',label='Mixed change'
  if(rd===0&&pd===0){status='stable';label='Stable'}
  else if(rd>=0&&pd>=0){status='higher';label='Higher measured signal'}
  else if(rd<=0&&pd<=0){status='lower';label='Lower measured signal'}
  return {status,label,current,previous,deltas:{redness,pigment}}
}
function sessionSummaryInterpretation(rows){
  const counts={baseline:0,stable:0,higher:0,lower:0,mixed:0}
  rows.forEach(r=>counts[r.status]=(counts[r.status]||0)+1)
  const comparable=rows.length-counts.baseline
  if(!rows.length) return {headline:'No completed captures are available.',counts,comparable}
  if(comparable===0) return {headline:'This session establishes region-specific baselines for future comparison.',counts,comparable}
  const parts=[]
  if(counts.stable) parts.push(`${counts.stable} stable`)
  if(counts.higher) parts.push(`${counts.higher} higher`)
  if(counts.lower) parts.push(`${counts.lower} lower`)
  if(counts.mixed) parts.push(`${counts.mixed} mixed`)
  if(counts.baseline) parts.push(`${counts.baseline} new baseline`)
  return {headline:`Compared with each region’s latest compatible baseline: ${parts.join(', ')}.`,counts,comparable}
}
function sessionSummaryV2Html(session){
  const rows=(session.items||[]).map(item=>({item,...sessionRegionComparison(item,session)}))
  const interpretation=sessionSummaryInterpretation(rows)
  const cards=rows.map(row=>{
    const m=row.current?.metrics||row.item.metrics||{}
    const currentValue=session.modality==='uv'?`${m.porphyrin_component_count_proxy??'—'} spots`:`${pct(m.redness_area_fraction)} redness`
    let delta='Baseline for this region'
    if(row.previous){
      if(session.modality==='uv') delta=`${signed(row.deltas.spots,0)} spots · ${signed(row.deltas.area,1)} pp area`
      else delta=`${signed(row.deltas.redness,1)} pp redness · ${signed(row.deltas.pigment,1)} pp pigment`
    }
    return `<div class="sessionV2Card ${row.status}"><div class="sessionV2CardHead"><span>${sessionRegionLabel(row.item.region_code)}</span><em>${row.label}</em></div><strong>${currentValue}</strong><small>${delta}</small></div>`
  }).join('')
  return `<div class="sessionComplete sessionV2"><div class="sessionV2Top"><div><span class="eyebrow">SESSION SUMMARY V2</span><b>Session complete</b><small>${session.items?.length||0} captures · ${interpretation.comparable} regions compared with a compatible baseline</small></div></div><div class="sessionV2Insight"><b>What changed</b><p>${interpretation.headline}</p><small>These are stored image-derived research measurements. “Higher” and “lower” describe measured signal only; they do not mean clinical improvement or worsening.</small></div><div class="sessionV2Grid">${cards}</div><div class="sessionV2Caveat">Comparisons require the same subject, region, compatible analysis/model version and accepted capture workflow.${session.modality==='uv'?' Passing the UV input gate does not independently prove UV illumination.':''}</div></div>`
}
// Override V1 summary presentation while keeping its capture/session mechanics.
sessionSummaryHtml=sessionSummaryV2Html
