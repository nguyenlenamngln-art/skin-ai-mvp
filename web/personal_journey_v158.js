// RGB V1.5.8 — Personal Skin Journey & Simplified UX
// Presentation/product layer only. Measurement remains RGB engine V1.5.2 / Capture Protocol V1.4.
(function(){
  const VERSION='1.5.8'
  const ENGINE='1.5.2'
  const NOTES_KEY='skin_ai_context_notes_v158'
  const CONTEXT_OPTIONS=['New product','Outdoor / sun','Shaving','Makeup','Poor sleep','Other']

  if(typeof render!=='function' || typeof setTab!=='function') return

  titles.home='Your skin today'
  titles.progress='Your progress'
  titles.scan='Take a skin scan'
  titles.routine='Your routine'
  titles.journey='Your journey'

  function finite(value){return Number.isFinite(Number(value))}
  function pctValue(value,digits=1){return finite(value)?`${(Number(value)*100).toFixed(digits)}%`:'—'}
  function num(value,digits=3){return finite(value)?Number(value).toFixed(digits):'—'}
  function dateShort(value){
    if(!value)return '—'
    return new Date(value).toLocaleDateString(undefined,{month:'short',day:'numeric'})
  }
  function dateLong(value){
    if(!value)return '—'
    return new Date(value).toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'})
  }
  function versionOf(scan){return String(scan?.metrics?.rgb_engine_version||'')}
  function eligible(scan){
    if(!scan || scan.modality!=='rgb' || versionOf(scan)!==ENGINE)return false
    if(typeof rgbLongitudinalEligible==='function') return rgbLongitudinalEligible(scan)
    return scan.metrics?.longitudinal_eligible!==false && scan.metrics?.capture_quality!=='poor'
  }
  function comparableScans(){return scans.filter(eligible)}
  function latestRgb(){return scans.find(s=>s.modality==='rgb')||null}
  function latestComparable(){return comparableScans()[0]||null}
  function baselineComparable(){const rows=comparableScans();return rows.length?rows[rows.length-1]:null}
  function previousComparable(){const rows=comparableScans();return rows.length>1?rows[1]:null}
  function ppDelta(current,previous){
    if(!finite(current)||!finite(previous))return null
    return (Number(current)-Number(previous))*100
  }
  function numericDelta(current,previous){
    if(!finite(current)||!finite(previous))return null
    return Number(current)-Number(previous)
  }
  function direction(delta,threshold=0.05,unit='pp'){
    if(delta===null)return {symbol:'—',label:'No comparison',value:'—'}
    const magnitude=Math.abs(delta)
    if(magnitude<threshold)return {symbol:'→',label:'Stable',value:unit==='pp'?'<0.05 pp':'Stable'}
    return {symbol:delta>0?'↑':'↓',label:delta>0?'Higher':'Lower',value:unit==='pp'?`${magnitude.toFixed(1)} pp`:magnitude.toFixed(3)}
  }
  function qualityLabel(scan){
    if(!scan)return 'No scan'
    if(eligible(scan))return 'Good for comparison'
    return 'Saved, not used for trends'
  }
  function signalCard(label,value,deltaInfo,caption){
    return `<article class="pjSignalCard"><span>${label}</span><strong>${value}</strong><div class="pjDelta ${deltaInfo?.symbol==='→'?'stable':''}"><b>${deltaInfo?.symbol||'—'} ${deltaInfo?.label||'Baseline'}</b>${deltaInfo?.value&&deltaInfo.value!=='—'?`<small>${deltaInfo.value} from baseline</small>`:'<small>Your personal reference</small>'}</div><small class="pjCaption">${caption}</small></article>`
  }
  function daysSince(value){return value?Math.max(0,(Date.now()-new Date(value).getTime())/86400000):null}
  function nextAction(scan){
    if(!scan)return {title:'Create your baseline',copy:'Take your first Phone RGB scan. Future comparable scans will be measured against your own history.',button:'Take first scan'}
    const age=daysSince(scan.created_at)
    if(age!==null && age<2)return {title:'You have a recent scan',copy:'Your latest comparable scan is recent. Keep your next capture under similar lighting, distance and angle.',button:'View progress'}
    return {title:'Ready for another comparison',copy:'A new scan can extend your personal timeline. Try to reuse similar lighting, distance and angle.',button:'Scan now'}
  }

  function renderToday(){
    const root=document.querySelector('#personalJourneyToday')
    if(!root)return
    const current=latestComparable()||latestRgb()
    const baseline=baselineComparable()
    if(!current){
      root.innerHTML=`<section class="pjWelcome card"><span class="eyebrow">YOUR SKIN TODAY</span><h2>Start with your baseline</h2><p>Take one clear Phone RGB scan. Skin AI will use your own future scans—not population rankings—to show how your visible skin signals change over time.</p><button class="primary pjGoScan">Take first scan</button></section>`
      root.querySelector('.pjGoScan')?.addEventListener('click',()=>setTab('scan'))
      return
    }
    const m=current.metrics||{}, b=baseline?.metrics||{}
    const red=baseline&&baseline.id!==current.id?direction(ppDelta(m.redness_area_fraction,b.redness_area_fraction)):null
    const pig=baseline&&baseline.id!==current.id?direction(ppDelta(m.pigmentation_area_fraction,b.pigmentation_area_fraction)):null
    const tex=baseline&&baseline.id!==current.id?direction(numericDelta(m.texture_index_proxy,b.texture_index_proxy),0.0005,'index'):null
    const action=nextAction(current)
    root.innerHTML=`
      <section class="pjTodayHero card">
        <div class="pjTodayCopy"><span class="eyebrow">YOUR SKIN TODAY · V${VERSION}</span><h2>${dateLong(current.created_at)}</h2><p>${baseline&&baseline.id!==current.id?`Compared with your baseline from ${dateShort(baseline.created_at)}.`:'This is your current personal baseline.'}</p></div>
        <img class="pjTodayPhoto" src="${current.media?.original||current.media?.overlay||''}" alt="Latest skin scan" />
      </section>
      <section class="pjSection"><div class="pjSectionHead"><div><span class="eyebrow">VISIBLE-LIGHT SIGNALS</span><h3>Your snapshot</h3></div><span class="pjQuality ${eligible(current)?'ok':'review'}">${qualityLabel(current)}</span></div>
        <div class="pjSignalGrid">
          ${signalCard('Redness',pctValue(m.redness_area_fraction),red,'Visible redness area')}
          ${signalCard('Pigmentation',pctValue(m.pigmentation_area_fraction),pig,'Visible pigmentation area')}
          ${signalCard('Texture',num(m.texture_index_proxy),tex,'Visible-light texture signal')}
        </div>
      </section>
      <section class="pjActionCard card"><div><span class="eyebrow">NEXT</span><h3>${action.title}</h3><p>${action.copy}</p></div><button class="primary" id="pjNextAction">${action.button}</button></section>
      <section class="pjQuickLinks"><button data-pj-go="progress">See progress</button><button data-pj-go="journey">View journey</button><button data-pj-go="routine">Routine & notes</button></section>
      <p class="pjSafety">Personal visible-light tracking only. Results are not diagnoses or population rankings.</p>`
    root.querySelector('#pjNextAction')?.addEventListener('click',()=>setTab(action.button==='View progress'?'progress':'scan'))
    root.querySelectorAll('[data-pj-go]').forEach(button=>button.addEventListener('click',()=>setTab(button.dataset.pjGo)))
  }

  function sparkline(rows,key,label,format){
    const chronological=[...rows].reverse().filter(s=>finite(s.metrics?.[key]))
    if(chronological.length<2)return `<article class="pjTrendCard"><div><b>${label}</b><small>Take at least two comparable scans</small></div><div class="pjTrendEmpty">Not enough data yet</div></article>`
    const vals=chronological.map(s=>Number(s.metrics[key]))
    const min=Math.min(...vals),max=Math.max(...vals),span=Math.max(max-min,0.000001)
    const width=320,height=90,pad=8
    const points=vals.map((v,i)=>`${pad+i*((width-pad*2)/Math.max(1,vals.length-1))},${height-pad-((v-min)/span)*(height-pad*2)}`).join(' ')
    return `<article class="pjTrendCard"><div class="pjTrendHead"><div><b>${label}</b><small>${dateShort(chronological[0].created_at)} → ${dateShort(chronological[chronological.length-1].created_at)}</small></div><strong>${format(vals[vals.length-1])}</strong></div><svg viewBox="0 0 ${width} ${height}" aria-label="${label} trend"><polyline points="${points}" fill="none" vector-effect="non-scaling-stroke" /></svg></article>`
  }

  function renderCompare(rows){
    if(rows.length<2)return `<section class="pjCompare card"><span class="eyebrow">BEFORE & AFTER</span><h3>Your visual comparison will appear here</h3><p>Take another quality-eligible RGB scan to compare it with your baseline.</p><button class="primary pjGoScan">Take another scan</button></section>`
    const newest=rows[0], oldest=rows[rows.length-1]
    return `<section class="pjCompare card"><div class="pjSectionHead"><div><span class="eyebrow">BEFORE & AFTER</span><h3>${dateShort(oldest.created_at)} vs ${dateShort(newest.created_at)}</h3></div><small>Drag to compare</small></div>
      <div class="pjCompareFrame" id="pjCompareFrame">
        <img class="pjCompareBase" src="${oldest.media?.original||''}" alt="Baseline scan" />
        <div class="pjCompareReveal" id="pjCompareReveal"><img src="${newest.media?.original||''}" alt="Latest scan" /></div>
        <div class="pjCompareLine" id="pjCompareLine"></div>
        <span class="pjCompareTag before">Baseline</span><span class="pjCompareTag after">Today</span>
      </div>
      <input id="pjCompareSlider" class="pjCompareSlider" type="range" min="0" max="100" value="50" aria-label="Before and after comparison position" />
      <p class="pjCompareNote">Photos are shown as captured. Apparent visual differences can also reflect lighting, angle or distance.</p>
    </section>`
  }

  function renderProgress(){
    const root=document.querySelector('#progressRoot')
    if(!root)return
    const rows=comparableScans()
    const current=rows[0]||null, baseline=rows.length?rows[rows.length-1]:null
    if(!current){
      root.innerHTML=`<div class="pjEmpty card"><span class="eyebrow">YOUR PROGRESS</span><h2>No comparable scans yet</h2><p>Take a quality-eligible Phone RGB scan to create your baseline.</p><button class="primary pjGoScan">Start scan</button></div>`
      root.querySelector('.pjGoScan')?.addEventListener('click',()=>setTab('scan'))
      return
    }
    const m=current.metrics||{}, b=baseline?.metrics||{}
    const red=baseline&&baseline.id!==current.id?direction(ppDelta(m.redness_area_fraction,b.redness_area_fraction)):null
    const pig=baseline&&baseline.id!==current.id?direction(ppDelta(m.pigmentation_area_fraction,b.pigmentation_area_fraction)):null
    const tex=baseline&&baseline.id!==current.id?direction(numericDelta(m.texture_index_proxy,b.texture_index_proxy),0.0005,'index'):null
    root.innerHTML=`
      <section class="pjProgressSummary card"><span class="eyebrow">FROM YOUR BASELINE</span><h2>${rows.length===1?'Your baseline is ready':`${rows.length} comparable scans`}</h2><div class="pjProgressDeltas">
        <div><span>Redness</span><b>${red?`${red.symbol} ${red.label}`:'Baseline'}</b></div>
        <div><span>Pigmentation</span><b>${pig?`${pig.symbol} ${pig.label}`:'Baseline'}</b></div>
        <div><span>Texture</span><b>${tex?`${tex.symbol} ${tex.label}`:'Baseline'}</b></div>
      </div><small>Changes describe your own comparable RGB scans. Higher/lower is descriptive, not good/bad.</small></section>
      ${renderCompare(rows)}
      <section class="pjSection"><div class="pjSectionHead"><div><span class="eyebrow">TREND</span><h3>Your visible signals over time</h3></div><span>${rows.length} scans</span></div><div class="pjTrendGrid">
        ${sparkline(rows,'redness_area_fraction','Redness',v=>pctValue(v))}
        ${sparkline(rows,'pigmentation_area_fraction','Pigmentation',v=>pctValue(v))}
        ${sparkline(rows,'texture_index_proxy','Texture',v=>num(v))}
      </div></section>`
    root.querySelector('.pjGoScan')?.addEventListener('click',()=>setTab('scan'))
    const slider=root.querySelector('#pjCompareSlider'), reveal=root.querySelector('#pjCompareReveal'), line=root.querySelector('#pjCompareLine')
    slider?.addEventListener('input',()=>{
      const value=Number(slider.value)
      if(reveal)reveal.style.clipPath=`inset(0 ${100-value}% 0 0)`
      if(line)line.style.left=`${value}%`
    })
  }

  function journeyDelta(scan,baseline,key,type='pp'){
    if(!baseline||scan.id===baseline.id)return 'Baseline'
    const d=type==='pp'?direction(ppDelta(scan.metrics?.[key],baseline.metrics?.[key])):direction(numericDelta(scan.metrics?.[key],baseline.metrics?.[key]),0.0005,'index')
    return `${d.symbol} ${d.label}`
  }
  function renderJourney(){
    const root=document.querySelector('#journeyRoot')
    if(!root)return
    const rows=comparableScans(), baseline=rows.length?rows[rows.length-1]:null
    if(!rows.length){
      root.innerHTML=`<div class="pjEmpty card"><span class="eyebrow">MY JOURNEY</span><h2>Your timeline starts with your first scan</h2><p>Once you have comparable scans, this page becomes a visual record of your skin over time.</p><button class="primary pjGoScan">Take first scan</button></div>`
      root.querySelector('.pjGoScan')?.addEventListener('click',()=>setTab('scan'))
      return
    }
    root.innerHTML=`<section class="pjJourneyIntro"><span class="eyebrow">MY JOURNEY</span><h2>${rows.length} comparable ${rows.length===1?'scan':'scans'}</h2><p>Your photos and measurements in one simple timeline.</p></section><div class="pjTimeline">${rows.map((scan,index)=>`<article class="pjTimelineItem card" data-scan-id="${scan.id}"><div class="pjTimelineMarker"></div><img src="${scan.media?.original||scan.media?.overlay||''}" alt="Skin scan ${dateShort(scan.created_at)}"/><div class="pjTimelineCopy"><div class="pjTimelineTitle"><b>${index===0?'Latest':scan.id===baseline?.id?'Baseline':dateLong(scan.created_at)}</b><span>${dateShort(scan.created_at)}</span></div><div class="pjTimelineSignals"><span>Redness <b>${journeyDelta(scan,baseline,'redness_area_fraction')}</b></span><span>Pigment <b>${journeyDelta(scan,baseline,'pigmentation_area_fraction')}</b></span><span>Texture <b>${journeyDelta(scan,baseline,'texture_index_proxy','index')}</b></span></div><button class="pjOpenScan" data-scan="${scan.id}">View scan</button></div></article>`).join('')}</div>`
    root.querySelectorAll('.pjOpenScan').forEach(button=>button.addEventListener('click',()=>{
      const scan=scans.find(row=>row.id===button.dataset.scan)
      if(scan){latest=scan;scanMode='rgb';resultView='combined';applyModeUI();renderResult();setTab('scan')}
    }))
  }

  function loadNotes(){
    try{const rows=JSON.parse(localStorage.getItem(NOTES_KEY)||'[]');return Array.isArray(rows)?rows:[]}catch(_e){return []}
  }
  function currentTester(){return localStorage.getItem('skin_ai_study_tester_v157')||'personal'}
  function renderRoutineAddon(){
    const root=document.querySelector('#journeyRoutineAddon')
    if(!root)return
    const tester=currentTester(), notes=loadNotes().filter(row=>row.tester===tester).slice(0,5)
    root.innerHTML=`<section class="pjContext card"><span class="eyebrow">SKIN DIARY</span><h3>Add context for today</h3><p>Optional notes can help you remember what was different around a scan. They are saved on this device only.</p><div class="pjContextChips">${CONTEXT_OPTIONS.map(label=>`<label><input type="checkbox" value="${label}"><span>${label}</span></label>`).join('')}</div><textarea id="pjContextNote" maxlength="240" placeholder="Optional note, e.g. started a new cleanser today"></textarea><button id="pjSaveContext" class="primary" type="button">Save today's note</button></section><section class="pjRecentNotes"><div class="pjSectionHead"><div><span class="eyebrow">RECENT NOTES</span><h3>Remember what changed</h3></div></div>${notes.length?notes.map(note=>`<article class="pjNoteRow"><div><b>${dateLong(note.created_at)}</b><span>${(note.tags||[]).join(' · ')||'Personal note'}</span></div><p>${escapeHtml(note.note||'')}</p></article>`).join(''):'<div class="pjTrendEmpty">No diary notes yet.</div>'}</section>`
    root.querySelector('#pjSaveContext')?.addEventListener('click',()=>{
      const tags=[...root.querySelectorAll('.pjContextChips input:checked')].map(input=>input.value)
      const note=String(root.querySelector('#pjContextNote')?.value||'').trim()
      if(!tags.length&&!note)return
      const all=loadNotes();all.unshift({tester,created_at:new Date().toISOString(),tags,note,scan_id:latestComparable()?.id||null});localStorage.setItem(NOTES_KEY,JSON.stringify(all.slice(0,100)))
      renderRoutineAddon()
    })
  }
  function escapeHtml(text){return String(text||'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}

  function renderAllJourney(){renderToday();renderProgress();renderJourney();renderRoutineAddon()}

  const baseRenderV158=render
  render=function(){baseRenderV158();renderAllJourney()}

  const baseSetTabV158=setTab
  setTab=function(tab){
    baseSetTabV158(tab)
    if(tab==='home')renderToday()
    else if(tab==='progress')renderProgress()
    else if(tab==='journey')renderJourney()
    else if(tab==='routine')renderRoutineAddon()
    window.scrollTo({top:0,behavior:'smooth'})
  }

  document.querySelectorAll('nav [data-tab]').forEach(button=>button.onclick=()=>setTab(button.dataset.tab))
  document.querySelectorAll('[data-go]').forEach(button=>button.onclick=()=>setTab(button.dataset.go))

  async function restoreProductHome(){
    try{
      const status=await fetch('/v1/study/status').then(r=>r.json()).catch(()=>null)
      if(status?.authenticated){document.body.classList.add('pjStudySignedIn');setTimeout(()=>setTab('home'),60)}
    }catch(_e){}
  }

  document.body.classList.add('pjV158Ready')
  renderAllJourney()
  restoreProductHome()
  window.skinJourneyV158={version:VERSION,render:renderAllJourney,comparableScans}
})()
