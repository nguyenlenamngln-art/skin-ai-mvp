// RGB Measurement Refinement V1.5.x UI
(function(){
  if(typeof renderResult!=='function') return
  const baseRender=renderResult
  renderResult=function(){
    baseRender()
    if(!latest || latest.modality!=='rgb' || rejectedAttempt) return
    const m=latest.metrics||{}
    const version=String(m.rgb_engine_version||'')
    if(!version.startsWith('1.5')) return
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
    note.innerHTML=`<b>RGB Measurement V${version} confidence: ${confidenceLabel}.</b> ${coverage}${pigmentCoverage?` · ${pigmentCoverage}`:''}. Low-confidence eyebrow/eye, lip/nostril and likely hair/stubble pixels are excluded from redness/pigmentation measurements.<p style="margin:8px 0 0">Regional usable-pixel confidence: ${regionalSummary}.</p>`
    body.appendChild(note)

    if(version==='1.5.1' || version==='1.5.2'){
      const eligible=Array.isArray(m.regional_trend_eligible_regions)?m.regional_trend_eligible_regions:[]
      const held=Array.isArray(m.regional_trend_held_regions)?m.regional_trend_held_regions:[]
      const refinement=document.createElement('div')
      refinement.className='scienceNote'
      if(version==='1.5.2'){
        const outer=Number(m.anatomical_outer_boundary_score)
        const support=Number(m.anatomical_skin_support_fraction)
        const outerText=Number.isFinite(outer)?`${outer.toFixed(0)}/100`:'not measured'
        const supportText=Number.isFinite(support)?`${Math.round(support*100)}%`:'not measured'
        refinement.innerHTML=`<b>Anatomical mask stabilization V1.5.2.</b> Measurement still excludes eye/eyebrow, lip/nostril and low-confidence hair pixels, while segmentation quality and the green outline use a separate stabilized outer facial envelope.<p style="margin:8px 0 0"><b>Outer-boundary stability:</b> ${outerText} · measured-skin support ${supportText}.</p><p style="margin:8px 0 0"><b>Regional trend gate:</b> ${eligible.length?`eligible — ${eligible.map(x=>x.replaceAll('_',' ')).join(', ')}`:'no regions eligible'}${held.length?`; held — ${held.map(x=>x.replaceAll('_',' ')).join(', ')}`:''}.</p>`
      }else{
        refinement.innerHTML=`<b>Segmentation refinement V1.5.1.</b> The skin mask is smoothed conservatively inside the existing face envelope; detached islands are removed and the algorithm falls back if refinement would discard too much skin.<p style="margin:8px 0 0"><b>Regional trend gate:</b> ${eligible.length?`eligible — ${eligible.map(x=>x.replaceAll('_',' ')).join(', ')}`:'no regions eligible'}${held.length?`; held — ${held.map(x=>x.replaceAll('_',' ')).join(', ')}`:''}.</p>`
      }
      body.appendChild(refinement)
    }

    if(Array.isArray(m.measurement_warnings) && m.measurement_warnings.length){
      const warning=document.createElement('div')
      warning.className='scienceNote'
      warning.innerHTML=`<b>Measurement confidence warning.</b> ${m.measurement_warnings.join(', ')}. This affects trend eligibility independently of capture quality.`
      body.appendChild(warning)
    }
  }
})()
