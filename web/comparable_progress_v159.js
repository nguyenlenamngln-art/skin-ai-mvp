// V1.5.9 — Comparable Capture & Aligned Progress
// Longitudinal presentation/orchestration only. RGB measurement remains V1.5.2.
(function(){
  const VERSION='1.5.9'
  const isPhone=()=>window.matchMedia('(max-width:820px)').matches
  const t=en=>{try{return window.skinCaptureI18n?.t?.(en)||window.skinI18n?.t?.(en)||en}catch(_e){return en}}
  let scheduled=false

  function finite(v){return Number.isFinite(Number(v))}
  function pct(v){return finite(v)?`${(Number(v)*100).toFixed(1)}%`:'—'}
  function texture(v){return finite(v)?Number(v).toFixed(3):'—'}
  function comparable(){return (typeof scans!=='undefined'?scans:[]).filter(s=>s.modality==='rgb' && String(s.metrics?.rgb_engine_version)==='1.5.2' && s.metrics?.capture_quality==='good')}
  function baseline(){const rows=comparable();return rows.length?rows[rows.length-1]:null}
  function current(){return comparable()[0]||null}
  function deltaPp(a,b){return finite(a)&&finite(b)?(Number(a)-Number(b))*100:null}
  function deltaNum(a,b){return finite(a)&&finite(b)?Number(a)-Number(b):null}
  function arrow(v,threshold){if(v===null)return '—';if(Math.abs(v)<threshold)return '→';return v>0?'↑':'↓'}
  function signed(v,digits=1,suffix=' pp'){if(v===null)return '—';if(Math.abs(v)<Math.pow(10,-digits)/2)return `0${suffix}`;return `${v>0?'+':''}${v.toFixed(digits)}${suffix}`}

  function clientMatch(cur,ref){
    if(!cur||!ref)return null
    const cm=cur.metrics||{}, rm=ref.metrics||{}
    if(finite(cm.comparison_match_score)) return {score:Number(cm.comparison_match_score),label:cm.comparison_match_label||'review',eligible:cm.comparison_match_eligible!==false,guidance:cm.comparison_match_guidance||[]}
    const ca=Number(cm.face_area_fraction),ra=Number(rm.face_area_fraction),cc=Number(cm.face_center_offset_fraction),rc=Number(rm.face_center_offset_fraction)
    const cl=Number(cm.skin_luminance_median_0_255),rl=Number(rm.skin_luminance_median_0_255)
    if(![ca,ra,cc,rc,cl,rl].every(Number.isFinite)) return null
    const one=(v,g,f)=>v<=g?100:v>=f?0:100*(f-v)/(f-g)
    const scale=one(Math.abs(Math.sqrt(ca/ra)-1),.10,.35)
    const center=Math.min(one(cc,.10,.26),one(Math.abs(cc-rc),.04,.18))
    const light=finite(cm.reference_lighting_score)?Number(cm.reference_lighting_score):one(Math.abs(Math.log2(Math.max(cl,1)/Math.max(rl,1))),.25,.90)
    const cb=Number(cm.left_right_luminance_asymmetry),rb=Number(rm.left_right_luminance_asymmetry)
    const balance=Number.isFinite(cb)&&Number.isFinite(rb)?Math.min(one(Math.max(cb,rb),.16,.42),one(Math.abs(cb-rb),.08,.28)):70
    const score=.40*light+.30*scale+.20*center+.10*balance
    return {score:Math.round(score*10)/10,label:score>=80?'strong':score>=65?'usable':'review',eligible:score>=65,guidance:[]}
  }

  function enhanceSummary(){
    const root=document.querySelector('#progressRoot'),cur=current(),base=baseline()
    if(!root||!cur||!base||cur.id===base.id)return
    const box=root.querySelector('.pjProgressSummary')
    if(!box)return
    const cm=cur.metrics||{}, bm=base.metrics||{}
    const red=deltaPp(cm.redness_area_fraction,bm.redness_area_fraction)
    const pig=deltaPp(cm.pigmentation_area_fraction,bm.pigmentation_area_fraction)
    const tex=deltaNum(cm.texture_index_proxy,bm.texture_index_proxy)
    const match=clientMatch(cur,base)
    box.innerHTML=`<span class="eyebrow">FROM YOUR BASELINE</span><h2>${comparable().length} comparable scans</h2>
      <div class="v159DeltaGrid">
        <div><span>Redness</span><b>${pct(bm.redness_area_fraction)} → ${pct(cm.redness_area_fraction)}</b><small>${arrow(red,.05)} ${signed(red,1)}</small></div>
        <div><span>Pigmentation</span><b>${pct(bm.pigmentation_area_fraction)} → ${pct(cm.pigmentation_area_fraction)}</b><small>${arrow(pig,.05)} ${signed(pig,1)}</small></div>
        <div><span>Texture</span><b>${texture(bm.texture_index_proxy)} → ${texture(cm.texture_index_proxy)}</b><small>${arrow(tex,.0005)} ${tex===null?'—':signed(tex,3,'')}</small></div>
      </div>
      ${match?`<div class="v159Match ${match.label}"><div><span>Comparison match</span><b>${match.label==='strong'?'Strong':match.label==='usable'?'Usable':'Review'} · ${Math.round(match.score)}/100</b></div><small>${match.eligible?'Framing and lighting are similar enough for personal trend comparison.':'This scan is still valid on its own, but capture differences may make trend comparison unreliable.'}</small></div>`:''}
      <small class="v159Caution">Changes describe your own comparable RGB scans. Higher/lower is descriptive, not good/bad.</small>`
  }

  function alignImage(img,scan,container){
    if(!img||!scan||!container)return
    const box=scan.metrics?.face_bbox
    if(!box||!finite(box.x)||!finite(box.y)||!finite(box.w)||!finite(box.h))return
    const apply=()=>{
      const cw=container.clientWidth,ch=container.clientHeight,nw=img.naturalWidth,nh=img.naturalHeight
      if(!cw||!ch||!nw||!nh)return
      const targetW=cw*.58,scale=targetW/Number(box.w)
      const fcX=Number(box.x)+Number(box.w)/2,fcY=Number(box.y)+Number(box.h)*.54
      img.style.width=`${nw*scale}px`;img.style.height=`${nh*scale}px`;img.style.maxWidth='none';img.style.maxHeight='none'
      img.style.left=`${cw/2-fcX*scale}px`;img.style.top=`${ch*.47-fcY*scale}px`;img.style.position='absolute'
    }
    img.complete?apply():img.addEventListener('load',apply,{once:true})
    setTimeout(apply,50)
  }

  function enhanceCompare(){
    const root=document.querySelector('#progressRoot'),rows=comparable()
    if(!root||rows.length<2)return
    const cur=rows[0],base=rows[rows.length-1],frame=root.querySelector('.pjCompareFrame')
    if(!frame||frame.dataset.v159==='1')return
    frame.dataset.v159='1';frame.classList.add('v159Aligned')
    const baseImg=frame.querySelector('.pjCompareBase'),todayImg=frame.querySelector('.pjCompareReveal img')
    alignImage(baseImg,base,frame);alignImage(todayImg,cur,frame)
    const note=root.querySelector('.pjCompareNote')
    if(note) note.textContent='Photos are face-centered for easier visual comparison. Lighting, expression and head angle can still affect apparent differences.'
  }

  function addCaptureReference(){
    if(!isPhone())return
    const stage=document.querySelector('#cgCamera .cgStage'),ref=current()
    if(!stage||!ref)return
    let img=stage.querySelector('.v159Ghost')
    if(!img){img=document.createElement('img');img.className='v159Ghost';img.src=ref.media?.original||'';stage.appendChild(img);alignImage(img,ref,stage)}
    img.alt=t('Previous comparable scan alignment reference')
    let label=stage.querySelector('.v159GhostLabel')
    if(!label){label=document.createElement('span');label.className='v159GhostLabel';stage.appendChild(label)}
    label.textContent=t('Match previous framing')
  }

  function addCaptureMatchHint(){
    if(!isPhone())return
    const guide=document.querySelector('#captureGuidanceV2 .cgHeader>div'),ref=current()
    if(!guide||!ref)return
    let hint=guide.querySelector('.v159RefHint')
    if(!hint){hint=document.createElement('small');hint.className='v159RefHint';guide.appendChild(hint)}
    hint.textContent=t('We’ll compare framing and lighting with your previous good scan.')
  }

  function enhance(){scheduled=false;document.documentElement.dataset.comparisonUxVersion=VERSION;enhanceSummary();enhanceCompare();addCaptureReference();addCaptureMatchHint()}
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(enhance)}
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true})
  document.addEventListener('click',e=>{if(e.target.closest('[data-tab],#cgOpenCamera'))setTimeout(schedule,50)})
  window.addEventListener('resize',schedule)
  window.addEventListener('skin-ai:locale-change',schedule)
  window.addEventListener('skin-ai:capture-i18n-ready',schedule)
  setTimeout(enhance,0)
})()