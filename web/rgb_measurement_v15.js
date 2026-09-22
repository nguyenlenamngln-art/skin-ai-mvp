// RGB Measurement Refinement V1.5 UI
(function(){
  if(typeof renderResult!=='function') return
  const baseRender=renderResult
  renderResult=function(){
    baseRender()
    if(!latest || latest.modality!=='rgb' || rejectedAttempt) return
    const m=latest.metrics||{}
    if(String(m.rgb_engine_version)!=='1.5') return
    const body=document.querySelector('#resultBody')
    if(!body) return

    const score=Number(m.measurement_confidence_score)
    const usable=Number(m.measurement_usable_pixel_fraction)
    const pigmentUsable=Number(m.pigmentation_usable_pixel_fraction)
    const confidenceLabel=Number.isFinite(score)?`${score.toFixed(0)}/100`:'Not measured'
    const coverage=Number.isFinite(usable)?`${(usable*100).toFixed(0)}% high-confidence skin pixels`:'coverage unavailable'
    const pigmentCoverage=Number.isFinite(pigmentUsable)?`${(pigmentUsable*100).toFixed(0)}% pigmentation-ready pixels`:''
    const regions=m.regional_measurements||{}
    const regionalEntries=Object.entries(regions).filter(([,v])=>Number.isFinite(Number(v?.confidence)))
    const regionalSummary=regionalEntries.length
      ? regionalEntries.map(([name,v])=>`${name.replaceAll('_',' ')} ${Math.round(Number(v.confidence)*100)}%`).join(' · ')
      : 'Regional confidence unavailable for this scan.'

    const note=document.createElement('div')
    note.className='scienceNote'
    note.innerHTML=`<b>RGB Measurement V1.5 confidence: ${confidenceLabel}.</b> ${coverage}${pigmentCoverage?` · ${pigmentCoverage}`:''}. Low-confidence eyebrow/eye, lip/nostril and likely hair/stubble pixels are excluded from redness/pigmentation measurements.<p style="margin:8px 0 0">Regional usable-pixel confidence: ${regionalSummary}.</p>`
    body.appendChild(note)

    if(Array.isArray(m.measurement_warnings) && m.measurement_warnings.length){
      const warning=document.createElement('div')
      warning.className='scienceNote'
      warning.innerHTML=`<b>Measurement confidence warning.</b> ${m.measurement_warnings.join(', ')}. This affects trend eligibility independently of capture quality.`
      body.appendChild(warning)
    }
  }
})()
