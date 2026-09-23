// RGB V1.5.5 Tester Result Experience
// Presentation-only layer: production measurement remains RGB engine V1.5.2.
(function(){
  const TESTER_RESULT_VERSION = '1.5.5'
  const ENGINE_UNDER_TEST = '1.5.2'
  if(typeof renderResult !== 'function') return

  const baseRenderResultV155 = renderResult

  function finite(value){ return Number.isFinite(Number(value)) }
  function percent(value, digits=1){ return finite(value) ? `${(Number(value)*100).toFixed(digits)}%` : '—' }
  function pointsDelta(current, previous){
    if(!finite(current) || !finite(previous)) return null
    return (Number(current)-Number(previous))*100
  }
  function deltaCard(label, current, previous){
    const delta=pointsDelta(current, previous)
    if(delta===null) return ''
    const magnitude=Math.abs(delta)
    const direction=magnitude<0.05 ? 'Stable' : delta>0 ? 'Higher' : 'Lower'
    const symbol=magnitude<0.05 ? '→' : delta>0 ? '↑' : '↓'
    const value=magnitude<0.05 ? '<0.05 pp' : `${magnitude.toFixed(1)} pp`
    return `<div class="testerChangeCard"><span>${label}</span><strong>${symbol} ${value}</strong><small>${direction} than your previous comparable scan</small></div>`
  }
  function technicalMetric(label, value, note=''){
    return `<div class="testerTechMetric"><span>${label}</span><b>${value}</b>${note?`<small>${note}</small>`:''}</div>`
  }
  function regionName(name){ return String(name||'').replaceAll('_',' ') }

  renderResult=function(){
    baseRenderResultV155()
    if(!latest || latest.modality!=='rgb' || rejectedAttempt) return

    const body=document.querySelector('#resultBody')
    if(!body) return
    const m=latest.metrics||{}
    const version=String(m.rgb_engine_version||'')
    if(version!==ENGINE_UNDER_TEST) return

    const prev=typeof previousComparableRgb==='function' ? previousComparableRgb(latest) : null
    const priorAny=typeof previousRgbAnyVersion==='function' ? previousRgbAnyVersion(latest) : null
    const eligible=typeof rgbLongitudinalEligible==='function' ? rgbLongitudinalEligible(latest) : m.longitudinal_eligible!==false

    if(!['original','skin','redness','pigmentation','combined'].includes(resultView)) resultView='combined'
    const tabs=[['original','Original'],['skin','Skin region'],['redness','Redness'],['pigmentation','Pigment'],['combined','Combined']]

    const confidence=finite(m.measurement_confidence_score)?`${Math.round(Number(m.measurement_confidence_score))}/100`:'Not measured'
    const usable=finite(m.measurement_usable_pixel_fraction)?percent(m.measurement_usable_pixel_fraction,0):'Not measured'
    const pigmentUsable=finite(m.pigmentation_usable_pixel_fraction)?percent(m.pigmentation_usable_pixel_fraction,0):'Not measured'
    const outer=finite(m.anatomical_outer_boundary_score)?`${Math.round(Number(m.anatomical_outer_boundary_score))}/100`:'Not measured'
    const support=finite(m.anatomical_skin_support_fraction)?percent(m.anatomical_skin_support_fraction,0):'Not measured'
    const captureScore=finite(m.capture_quality_score)?`${Math.round(Number(m.capture_quality_score))}/100`:'Not measured'
    const framing=finite(m.quality_subscores?.framing)?`${Math.round(Number(m.quality_subscores.framing))}/100`:'Not measured'
    const lighting=finite(m.quality_subscores?.lighting)?`${Math.round(Number(m.quality_subscores.lighting))}/100`:'Not measured'
    const segmentation=finite(m.quality_subscores?.segmentation)?`${Math.round(Number(m.quality_subscores.segmentation))}/100`:'Not measured'

    const regions=m.regional_measurements||{}
    const regionRows=Object.entries(regions)
      .filter(([,value])=>finite(value?.confidence))
      .map(([name,value])=>`${regionName(name)} ${percent(value.confidence,0)}`)
      .join(' · ')
    const trendEligible=Array.isArray(m.regional_trend_eligible_regions)?m.regional_trend_eligible_regions.map(regionName):[]
    const trendHeld=Array.isArray(m.regional_trend_held_regions)?m.regional_trend_held_regions.map(regionName):[]
    const guidance=Array.isArray(m.quality_guidance)?m.quality_guidance:[]
    const warnings=Array.isArray(m.measurement_warnings)?m.measurement_warnings:[]

    let comparisonBlock=''
    if(prev){
      comparisonBlock=`
        <section class="testerSection">
          <div class="testerSectionHead"><span class="eyebrow">CHANGE SINCE LAST COMPARABLE SCAN</span><p>Compared only with a same-version, quality-eligible RGB scan.</p></div>
          <div class="testerChangeGrid">
            ${deltaCard('Visible redness area',m.redness_area_fraction,prev.metrics?.redness_area_fraction)}
            ${deltaCard('Visible pigmentation area',m.pigmentation_area_fraction,prev.metrics?.pigmentation_area_fraction)}
          </div>
        </section>`
    }else{
      const analysisChanged=priorAny && typeof rgbVersion==='function' && rgbVersion(priorAny)!==version
      comparisonBlock=`
        <section class="testerBaseline ${eligible?'':'testerBaselineWarn'}">
          <span class="testerBaselineIcon">${eligible?'✓':'!'}</span>
          <div><b>${analysisChanged?'New baseline after analysis update':eligible?'This scan is your baseline':'This scan is saved for review'}</b>
          <p>${analysisChanged?'Future scans using the same analysis version can be compared with this result.':eligible?'Repeat your scan under similar lighting, distance and angle to begin tracking change.':'This capture is not used for longitudinal changes. Follow the scan-quality guidance and retake when possible.'}</p></div>
        </section>`
    }

    const qualityTitle=eligible?'Good for comparison':'Not used for trend comparison'
    const qualityCopy=eligible
      ? 'This capture passed the current quality gate and can be compared with future same-version scans.'
      : 'You can review this result, but the app excludes it from longitudinal deltas and trends.'

    body.className='testerResultV155'
    body.innerHTML=`
      <section class="testerHero">
        <div><span class="eyebrow">YOUR SKIN TODAY</span><h2>Visible-light skin signals</h2><p>These measurements describe this photo and are designed primarily for tracking your own changes over time.</p></div>
        <span class="testerVersion">Result experience V${TESTER_RESULT_VERSION}</span>
      </section>

      <div class="testerSignalGrid">
        <div class="testerSignalCard"><span>Visible redness area</span><strong>${percent(m.redness_area_fraction)}</strong><small>of analyzed skin</small></div>
        <div class="testerSignalCard"><span>Visible pigmentation area</span><strong>${percent(m.pigmentation_area_fraction)}</strong><small>of analyzed skin</small></div>
        <div class="testerSignalCard"><span>Texture signal</span><strong>${finite(m.texture_index_proxy)?Number(m.texture_index_proxy).toFixed(3):'—'}</strong><small>visible-light texture proxy</small></div>
      </div>

      ${comparisonBlock}

      <section class="testerSection testerImageSection">
        <div class="testerSectionHead"><span class="eyebrow">WHAT WE DETECTED</span><p>Switch views to inspect the analyzed skin region and visible-light signal maps.</p></div>
        <div class="viewTabs rgbV11Tabs">${tabs.map(([key,label])=>`<button data-result-view="${key}" class="${resultView===key?'active':''}">${label}</button>`).join('')}</div>
        <div class="analysisImage ${resultView}"><img src="${viewSrc(latest,resultView)}" alt="${resultView} analysis"/>${resultView==='combined'?`<div class="legend"><span><i class="dot red"></i>local redness</span><span><i class="dot violet"></i>local pigmentation</span><span><i class="dot green"></i>analyzed skin boundary</span></div>`:''}</div>
      </section>

      <section class="testerQuality ${eligible?'testerQualityGood':'testerQualityWarn'}">
        <div><span class="eyebrow">SCAN QUALITY</span><h3>${qualityTitle}</h3><p>${qualityCopy}</p></div>
        <div class="testerQualityScore"><span>Capture quality</span><strong>${m.capture_quality||'—'}</strong><small>${captureScore}</small></div>
      </section>
      ${guidance.length?`<div class="testerGuidance"><b>For your next scan</b><ul>${guidance.map(item=>`<li>${item}</li>`).join('')}</ul></div>`:''}

      <details class="testerTechnical">
        <summary><span><b>Technical details</b><small>For research and validation review</small></span><span aria-hidden="true">＋</span></summary>
        <div class="testerTechnicalBody">
          <div class="testerTechGrid">
            ${technicalMetric('RGB engine',`V${version}`,'production measurement engine')}
            ${technicalMetric('Capture protocol',m.capture_protocol_version||'legacy')}
            ${technicalMetric('Measurement confidence',confidence)}
            ${technicalMetric('High-confidence skin',usable)}
            ${technicalMetric('Pigmentation-ready skin',pigmentUsable)}
            ${technicalMetric('Framing',framing)}
            ${technicalMetric('Lighting',lighting)}
            ${technicalMetric('Segmentation',segmentation)}
            ${technicalMetric('Outer-boundary stability',outer)}
            ${technicalMetric('Measured-skin support',support)}
          </div>
          <div class="testerTechNote"><b>Regional confidence</b><p>${regionRows||'Regional confidence unavailable for this scan.'}</p></div>
          <div class="testerTechNote"><b>Regional trend gate</b><p>${trendEligible.length?`Eligible: ${trendEligible.join(', ')}`:'No regions currently eligible'}${trendHeld.length?` · Held: ${trendHeld.join(', ')}`:''}</p></div>
          ${warnings.length?`<div class="testerTechNote testerTechWarning"><b>Measurement warnings</b><p>${warnings.join(', ')}</p></div>`:''}
          <div class="testerResearchNote"><b>Research measurement.</b> Phone RGB results are relative visible-light proxies for personal longitudinal tracking. They are not diagnoses and are not substitutes for polarized, UV, or clinical skin assessment.</div>
        </div>
      </details>`

    body.querySelectorAll('[data-result-view]').forEach(button=>{
      button.onclick=()=>{ resultView=button.dataset.resultView; renderResult() }
    })
  }
})()
