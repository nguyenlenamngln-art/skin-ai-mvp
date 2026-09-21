// Final tracking-safety layer for the profile/region milestone.
const renderTrendTrackingBase=renderTrend
renderTrend=function(){
  if(!latest || latest.modality!=='rgb') return renderTrendTrackingBase()
  const key=structuredTrackingKey(latest), svg=$('#trendSvg'), empty=$('#trendEmpty')
  $('#trendTitle').textContent=`RGB redness-area trend · ${rgbVersionLabel(latest)}`
  if(!key || !rgbLongitudinalEligible(latest)){
    svg.innerHTML='';empty.classList.remove('hidden')
    empty.textContent='This RGB scan is analysis-only or not trend eligible. Choose a subject and region and capture a good-quality scan to create a longitudinal series.'
    return
  }
  const version=rgbVersion(latest)
  const rows=trends.filter(x=>x.modality==='rgb' && x.tracking_series_key===key && String(x.rgb_engine_version||'legacy-v1')===version && x.longitudinal_eligible!==false)
  const vals=rows.map(x=>x.redness_area_fraction).filter(Number.isFinite)
  if(vals.length<2){svg.innerHTML='';empty.classList.remove('hidden');empty.textContent='Run at least two good-quality RGB scans for this same profile and region to see a trend.';return}
  empty.classList.add('hidden')
  const mn=Math.min(...vals),mx=Math.max(...vals),span=Math.max(0.000001,mx-mn)
  const pts=vals.map((v,i)=>`${20+i*(560/(vals.length-1))},${140-((v-mn)/span)*105}`).join(' ')
  svg.innerHTML=`<line x1="20" y1="140" x2="580" y2="140" stroke="#d8dbd3"/><polyline points="${pts}" fill="none" stroke="#496956" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>`
}

const renderTrackingDashboardBase=render
render=function(){
  renderTrackingDashboardBase()
  renderTrackingDashboard()
}
