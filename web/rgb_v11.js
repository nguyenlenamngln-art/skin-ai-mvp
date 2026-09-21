// Phone RGB V1.1 UI refinement layer.
// Loaded after app.js so the working V1 product flow remains unchanged while
// RGB scans gain a dedicated analyzed-skin-region view.
const baseViewSrcV11 = viewSrc
viewSrc = function(scan, view){
  if(scan?.modality==='rgb' && view==='skin') return scan.media.skin_region || scan.media.overlay
  return baseViewSrcV11(scan, view)
}

const baseRenderResultV11 = renderResult
renderResult = function(){
  if(!latest || latest.modality!=='rgb') return baseRenderResultV11()
  const body=$('#resultBody'), date=$('#resultDate'), badge=$('#compareBadge')
  body.className=''; date.textContent=new Date(latest.created_at).toLocaleString()
  const prev=previousSameModality(latest), m=latest.metrics
  if(prev){
    const d=(m.redness_area_fraction-prev.metrics.redness_area_fraction)*100
    badge.textContent=Math.abs(d)<0.05?'RGB stable vs previous':`${d<0?'↓':'↑'} ${Math.abs(d).toFixed(1)} pp redness area`
    badge.className=`compareBadge ${d<0?'good':d>0?'warn':''}`
  } else badge.classList.add('hidden')

  if(!['original','skin','redness','pigmentation','combined'].includes(resultView)) resultView='combined'
  const tabs=[['original','Original'],['skin','Skin region'],['redness','Redness'],['pigmentation','Pigment'],['combined','Combined']]
  body.innerHTML=`
    <div class="viewTabs rgbV11Tabs">${tabs.map(([k,l])=>`<button data-result-view="${k}" class="${resultView===k?'active':''}">${l}</button>`).join('')}</div>
    <div class="analysisImage ${resultView}"><img src="${viewSrc(latest,resultView)}" alt="${resultView} analysis"/>${resultView==='combined'?`<div class="legend"><span><i class="dot red"></i>local redness</span><span><i class="dot violet"></i>local pigmentation</span><span><i class="dot green"></i>analyzed skin boundary</span></div>`:''}</div>
    <div class="analysisMetrics">
      ${metric('Redness area',pct(m.redness_area_fraction),'relative analyzed skin',prev?deltaText(m.redness_area_fraction,prev.metrics.redness_area_fraction,'pct'):'')}
      ${metric('Red spots',m.red_spot_count_proxy,'filtered local components')}
      ${metric('Pigmented area',pct(m.pigmentation_area_fraction),'relative analyzed skin',prev?deltaText(m.pigmentation_area_fraction,prev.metrics.pigmentation_area_fraction,'pct'):'')}
      ${metric('Pigmented spots',m.pigmented_spot_count_proxy,'filtered local dark components')}
      ${metric('Texture index',(m.texture_index_proxy||0).toFixed(3),'luminance high-frequency proxy')}
      ${metric('Capture quality',m.capture_quality||'—',(m.quality_flags||[]).join(', ')||'no capture flags')}
    </div>
    <div class="scienceNote"><b>Phone RGB V1.1 research measurement.</b> The green boundary shows the adaptive skin region used for analysis. Eyes/brows/lips and non-skin chroma are conservatively excluded. These remain relative visible-light proxies, not diagnoses or substitutes for polarized/UV imaging.</div>`
  $$('[data-result-view]').forEach(b=>b.onclick=()=>{resultView=b.dataset.resultView;renderResult()})
}
