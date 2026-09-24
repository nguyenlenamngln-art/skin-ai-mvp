// V1.5.9.1 — Comparison Credibility Patch
// Presentation/longitudinal credibility only. RGB measurement remains V1.5.2.
(function(){
  const VERSION='1.5.9.1'
  let scheduled=false

  const finite=v=>Number.isFinite(Number(v))
  const round=(v,d)=>Number(Number(v).toFixed(d))
  const pctDisplay=v=>finite(v)?round(Number(v)*100,1):null
  const textureDisplay=v=>finite(v)?round(Number(v),4):null
  const fmtPct=v=>v===null?'—':`${v.toFixed(1)}%`
  const fmtTexture=v=>v===null?'—':v.toFixed(4)
  const fmtSigned=(v,d=1,suffix=' pp')=>{
    if(v===null)return '—'
    const r=round(v,d)
    if(Math.abs(r)<Math.pow(10,-d)/2)return `0${suffix}`
    return `${r>0?'+':''}${r.toFixed(d)}${suffix}`
  }
  const arrow=(v,threshold)=>v===null?'—':Math.abs(v)<threshold?'→':v>0?'↑':'↓'
  const dateShort=value=>value?new Date(value).toLocaleDateString(undefined,{month:'short',day:'numeric'}):'—'

  function rows(){
    return (typeof scans!=='undefined'?scans:[]).filter(s=>
      s.modality==='rgb' &&
      String(s.metrics?.rgb_engine_version)==='1.5.2' &&
      s.metrics?.capture_quality==='good' &&
      s.metrics?.longitudinal_eligible!==false
    )
  }
  function baseline(){const r=rows();return r.length?r[r.length-1]:null}
  function current(){return rows()[0]||null}

  function one(value,good,fail){return value<=good?100:value>=fail?0:100*(fail-value)/(fail-good)}
  function bboxAspect(m){
    const b=m?.face_bbox
    if(!b||!finite(b.w)||!finite(b.h)||Number(b.h)<=0)return null
    return Number(b.w)/Number(b.h)
  }
  function normalizedGeometry(m){
    const b=m?.face_bbox,w=Number(m?.capture_image_width_px),h=Number(m?.capture_image_height_px)
    if(!b||![b.x,b.y,b.w,b.h,w,h].every(finite)||w<=0||h<=0)return null
    return {cx:(Number(b.x)+Number(b.w)/2)/w,cy:(Number(b.y)+Number(b.h)/2)/h,w:Number(b.w)/w,h:Number(b.h)/h}
  }

  function strictMatch(cur,ref){
    if(!cur||!ref)return null
    const c=cur.metrics||{},r=ref.metrics||{}
    const ca=Number(c.face_area_fraction),ra=Number(r.face_area_fraction)
    const cc=Number(c.face_center_offset_fraction),rc=Number(r.face_center_offset_fraction)
    const cl=Number(c.skin_luminance_median_0_255),rl=Number(r.skin_luminance_median_0_255)
    if(![ca,ra,cc,rc,cl,rl].every(Number.isFinite))return null

    const scaleDelta=Math.abs(Math.sqrt(Math.max(ca,1e-9)/Math.max(ra,1e-9))-1)
    const scale=one(scaleDelta,.07,.25)
    const cg=normalizedGeometry(c),rg=normalizedGeometry(r)
    const complete=!!(cg&&rg)
    let geometry=70,centering,centerVector=null,sizeDelta=null
    if(complete){
      centerVector=Math.hypot(cg.cx-rg.cx,cg.cy-rg.cy)
      sizeDelta=Math.max(Math.abs(cg.w/Math.max(rg.w,1e-9)-1),Math.abs(cg.h/Math.max(rg.h,1e-9)-1))
      geometry=Math.min(one(centerVector,.025,.12),one(sizeDelta,.07,.24))
      centering=Math.min(one(cc,.08,.20),one(rc,.08,.20),one(centerVector,.025,.12))
    }else{
      centering=Math.min(one(cc,.08,.20),one(rc,.08,.20),one(Math.abs(cc-rc),.025,.10))
    }
    const ev=Math.abs(Math.log2(Math.max(cl,1)/Math.max(rl,1)))
    const lighting=one(ev,.20,.70)
    const cb=Number(c.left_right_luminance_asymmetry),rb=Number(r.left_right_luminance_asymmetry)
    const balance=Number.isFinite(cb)&&Number.isFinite(rb)?Math.min(one(Math.max(cb,rb),.12,.32),one(Math.abs(cb-rb),.05,.18)):65
    const caa=bboxAspect(c),raa=bboxAspect(r)
    const aspect=caa!==null&&raa!==null?one(Math.abs(Math.log(Math.max(caa,1e-9)/Math.max(raa,1e-9))),.05,.18):65
    const components={lighting,face_scale:scale,centering,balance,bbox_aspect:aspect,bbox_geometry:geometry}
    let score=.20*lighting+.20*scale+.20*centering+.10*balance+.10*aspect+.20*geometry
    if(!complete)score=Math.min(score,79)
    const floor=Math.min(lighting,scale,centering,geometry)
    const eligible=score>=72&&floor>=45
    const strong=eligible&&complete&&score>=88&&Math.min(...Object.values(components))>=70
    return {score:Math.round(score),label:strong?'strong':eligible?'usable':'review',eligible,complete,components,centerVector,sizeDelta}
  }

  function exactDelta(rawBase,rawCurrent,type){
    if(type==='pct'){
      const b=pctDisplay(rawBase),c=pctDisplay(rawCurrent)
      return {base:b,current:c,delta:b===null||c===null?null:round(c-b,1),threshold:.05}
    }
    const b=textureDisplay(rawBase),c=textureDisplay(rawCurrent)
    return {base:b,current:c,delta:b===null||c===null?null:round(c-b,4),threshold:.00005}
  }

  function enhanceSummary(){
    const root=document.querySelector('#progressRoot'),cur=current(),base=baseline()
    if(!root||!cur||!base||cur.id===base.id)return
    const box=root.querySelector('.pjProgressSummary')
    if(!box)return
    const c=cur.metrics||{},b=base.metrics||{}
    const red=exactDelta(b.redness_area_fraction,c.redness_area_fraction,'pct')
    const pig=exactDelta(b.pigmentation_area_fraction,c.pigmentation_area_fraction,'pct')
    const tex=exactDelta(b.texture_index_proxy,c.texture_index_proxy,'texture')
    const match=strictMatch(cur,base)
    box.dataset.credibilityPatch=VERSION
    box.innerHTML=`<span class="eyebrow">FROM YOUR BASELINE</span><h2>${rows().length} comparable scans</h2>
      <div class="v159DeltaGrid v1591DeltaGrid">
        <div><span>Redness</span><b>${fmtPct(red.base)} → ${fmtPct(red.current)}</b><small>${arrow(red.delta,red.threshold)} ${fmtSigned(red.delta,1)}</small></div>
        <div><span>Pigmentation</span><b>${fmtPct(pig.base)} → ${fmtPct(pig.current)}</b><small>${arrow(pig.delta,pig.threshold)} ${fmtSigned(pig.delta,1)}</small></div>
        <div><span>Texture</span><b>${fmtTexture(tex.base)} → ${fmtTexture(tex.current)}</b><small>${arrow(tex.delta,tex.threshold)} ${fmtSigned(tex.delta,4,'')}</small></div>
      </div>
      ${match?`<div class="v159Match ${match.label}"><div><span>Comparison match</span><b>${match.label==='strong'?'Strong':match.label==='usable'?'Usable':'Review'} · ${match.score}/100</b></div><small>${match.eligible?(match.complete?'Framing and lighting are similar enough for personal trend comparison.':'Usable for comparison, but older scans lack full framing metadata; confidence is intentionally capped.'):'This scan is valid on its own, but capture differences make trend comparison less reliable.'}</small></div>`:''}
      <small class="v159Caution">Changes use the values shown above, so displayed endpoints and displayed deltas always agree. Higher/lower is descriptive, not good/bad.</small>`
  }

  function twoPointCard(label,key,type,base,cur){
    const b=base.metrics||{},c=cur.metrics||{}
    const d=exactDelta(b[key],c[key],type)
    const baseText=type==='pct'?fmtPct(d.base):fmtTexture(d.base)
    const curText=type==='pct'?fmtPct(d.current):fmtTexture(d.current)
    const deltaText=type==='pct'?fmtSigned(d.delta,1):fmtSigned(d.delta,4,'')
    const symbol=arrow(d.delta,d.threshold)
    return `<article class="v1591TwoPointCard"><div class="v1591TwoPointHead"><div><b>${label}</b><small>${dateShort(base.created_at)} → ${dateShort(cur.created_at)}</small></div><strong>${curText}</strong></div><div class="v1591Endpoints"><span><small>Baseline</small><b>${baseText}</b></span><i>→</i><span><small>Latest</small><b>${curText}</b></span></div><div class="v1591Change"><b>${symbol} ${deltaText}</b><small>${symbol==='→'?'No meaningful change at the displayed precision':'Change from displayed baseline'}</small></div></article>`
  }

  function replaceTwoPointTrends(){
    const root=document.querySelector('#progressRoot'),r=rows()
    if(!root||r.length!==2)return
    const grid=root.querySelector('.pjTrendGrid')
    if(!grid||grid.dataset.credibilityPatch===VERSION)return
    const cur=r[0],base=r[1]
    grid.dataset.credibilityPatch=VERSION
    grid.classList.add('v1591TwoPointGrid')
    grid.innerHTML=[
      twoPointCard('Redness','redness_area_fraction','pct',base,cur),
      twoPointCard('Pigmentation','pigmentation_area_fraction','pct',base,cur),
      twoPointCard('Texture','texture_index_proxy','texture',base,cur),
    ].join('')
    const section=grid.closest('.pjSection')
    const heading=section?.querySelector('h3')
    if(heading)heading.textContent='Your change from baseline'
    const count=section?.querySelector('.pjSectionHead>span')
    if(count)count.textContent='2 scans · start to latest'
  }

  function enhance(){
    scheduled=false
    document.documentElement.dataset.comparisonCredibilityVersion=VERSION
    enhanceSummary()
    replaceTwoPointTrends()
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(enhance)}
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true})
  document.addEventListener('click',e=>{if(e.target.closest('[data-tab]'))setTimeout(schedule,30)})
  setTimeout(enhance,0)
})()
