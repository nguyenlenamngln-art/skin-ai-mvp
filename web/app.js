const $ = q => document.querySelector(q)
const $$ = q => [...document.querySelectorAll(q)]
const pct = (x=0) => `${(x*100).toFixed(1)}%`
const signed = (n, digits=0) => `${n>0?'+':''}${n.toFixed(digits)}`
const titles = {home:'Your skin, over time.',scan:'New skin scan',history:'Scan history',routine:'Routine tracker'}
let scans=[], trends=[], latest=null, resultView='combined', scanMode='uv', health={}, rejectedAttempt=null

async function api(path, options={}){
  const r=await fetch(path,options)
  const data=await r.json().catch(()=>({}))
  if(!r.ok){
    const err=new Error(typeof data.detail==='string'?data.detail:(data.detail?.message||`Request failed (${r.status})`))
    err.status=r.status
    err.detail=data.detail
    throw err
  }
  return data
}
function showError(msg=''){ const el=$('#error'); el.textContent=msg; el.classList.toggle('hidden',!msg) }
function setTab(tab){
  $$('.view').forEach(v=>v.classList.toggle('active',v.id===tab))
  $$('nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab))
  $('#title').textContent=titles[tab]
}
$$('[data-tab]').forEach(b=>b.onclick=()=>setTab(b.dataset.tab))
$$('[data-go]').forEach(b=>b.onclick=()=>setTab(b.dataset.go))

function metric(label,value,note,delta=''){
  return `<div class="metric card"><span>${label}</span><strong>${value}</strong><small>${note}</small>${delta?`<em class="delta">${delta}</em>`:''}</div>`
}
function scansOf(modality){ return scans.filter(s=>s.modality===modality) }
function previousSameModality(scan){
  if(!scan) return null
  const same=scansOf(scan.modality), i=same.findIndex(s=>s.id===scan.id)
  return i>=0 && i<same.length-1 ? same[i+1] : null
}
function deltaText(curr,prev,kind='number'){
  if(prev==null || !Number.isFinite(curr) || !Number.isFinite(prev)) return ''
  const d=curr-prev
  if(Math.abs(d)<0.00001) return 'no change'
  if(kind==='pct') return `${signed(d*100,1)} pp vs previous`
  if(kind==='decimal') return `${signed(d,3)} vs previous`
  return `${signed(d,0)} vs previous`
}
function scanPrimary(scan){
  if(!scan) return {label:'No scans yet',copy:'Start with a Phone RGB or UV scan to create your baseline.'}
  const m=scan.metrics
  if(scan.modality==='rgb') return {label:`${pct(m.redness_area_fraction)} redness area`,copy:`Phone RGB baseline · capture quality: ${m.capture_quality}.`}
  return {label:`${m.porphyrin_component_count_proxy} fluorescent components`,copy:`UV fluorescence analysis from ${new Date(scan.created_at).toLocaleDateString()}.`}
}
function render(){
  latest=latest||scans[0]||null
  const primary=scanPrimary(latest)
  $('#latestSignal').textContent=primary.label
  $('#latestCopy').textContent=primary.copy
  const prev=previousSameModality(latest)
  if(!latest){
    $('#metricCards').innerHTML=[metric('Redness','—','Phone RGB proxy'),metric('Pigmentation','—','Phone RGB proxy'),metric('Porphyrin','—','UV fluorescence'),metric('Capture quality','—','repeatability check')].join('')
    $('#insightText').textContent='Repeat scans under similar lighting, distance and angle to track change.'
  } else if(latest.modality==='rgb'){
    const m=latest.metrics
    $('#metricCards').innerHTML=[
      metric('Redness area',pct(m.redness_area_fraction),'relative RGB proxy',prev?deltaText(m.redness_area_fraction,prev.metrics.redness_area_fraction,'pct'):''),
      metric('Pigmented area',pct(m.pigmentation_area_fraction),'relative RGB proxy',prev?deltaText(m.pigmentation_area_fraction,prev.metrics.pigmentation_area_fraction,'pct'):''),
      metric('Texture index',(m.texture_index_proxy||0).toFixed(3),'luminance texture proxy',prev?deltaText(m.texture_index_proxy,prev.metrics.texture_index_proxy,'decimal'):''),
      metric('Capture quality',m.capture_quality||'—',(m.quality_flags||[]).join(', ')||'no capture flags')
    ].join('')
    $('#insightText').textContent=prev?'Compare RGB values only when lighting, angle and distance are similar.':'This is your first RGB baseline. Repeat under similar capture conditions to track change.'
  } else {
    const m=latest.metrics
    $('#metricCards').innerHTML=[
      metric('Fluorescent spots',m.porphyrin_component_count_proxy,'porphyrin component proxy',prev?deltaText(m.porphyrin_component_count_proxy,prev.metrics.porphyrin_component_count_proxy):''),
      metric('Fluorescent area',pct(m.porphyrin_area_fraction_valid),'of valid observed pixels',prev?deltaText(m.porphyrin_area_fraction_valid,prev.metrics.porphyrin_area_fraction_valid,'pct'):''),
      metric('Signal intensity',(m.porphyrin_red_intensity_proxy||0).toFixed(2),'red-channel proxy'),
      metric('Artifact excluded',pct(m.artifact_area_fraction),'hair / reflections / ruler')
    ].join('')
    $('#insightText').textContent=prev?'Compare UV scans only when capture conditions are similar.':'This is your first UV baseline. Repeat under similar capture conditions to track change.'
  }
  renderTrend(); renderHistory(); renderResult()
}
function renderTrend(){
  if(!latest){ $('#trendTitle').textContent='Signal trend'; $('#trendSvg').innerHTML=''; $('#trendEmpty').classList.remove('hidden'); return }
  const modality=latest.modality
  const rows=trends.filter(x=>x.modality===modality)
  const key=modality==='rgb'?'redness_area_fraction':'porphyrin_component_count_proxy'
  const vals=rows.map(x=>x[key]).filter(Number.isFinite), svg=$('#trendSvg'), empty=$('#trendEmpty')
  $('#trendTitle').textContent=modality==='rgb'?'RGB redness-area trend':'UV porphyrin spot trend'
  if(vals.length<2){svg.innerHTML='';empty.classList.remove('hidden');return}
  empty.classList.add('hidden')
  const mn=Math.min(...vals),mx=Math.max(...vals),span=Math.max(0.000001,mx-mn)
  const pts=vals.map((v,i)=>`${20+i*(560/(vals.length-1))},${140-((v-mn)/span)*105}`).join(' ')
  svg.innerHTML=`<line x1="20" y1="140" x2="580" y2="140" stroke="#d8dbd3"/><polyline points="${pts}" fill="none" stroke="#496956" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>`
}
function renderHistory(){
  $('#historyTitle').textContent=`${scans.length} saved scans`
  $('#historyList').innerHTML=scans.length?scans.map(s=>{
    const m=s.metrics
    const thumb=s.media.overlay||s.media.original
    const summary=s.modality==='rgb'?`${pct(m.redness_area_fraction)} redness · ${pct(m.pigmentation_area_fraction)} pigment`:`${m.porphyrin_component_count_proxy} spots · ${pct(m.artifact_area_fraction)} artifacts`
    return `<button class="historyRow" data-id="${s.id}"><img src="${thumb}"/><div><b>${new Date(s.created_at).toLocaleString()}</b><span>${s.modality.toUpperCase()} · ${s.source_name||'scan'}</span></div><div class="historyStat"><b>${s.modality==='rgb'?(m.capture_quality||'—'):m.porphyrin_component_count_proxy}</b><span>${summary}</span></div><span>›</span></button>`
  }).join(''):'<div class="empty">No scans yet.</div>'
  $$('.historyRow').forEach(b=>b.onclick=()=>{rejectedAttempt=null;showError('');latest=scans.find(s=>s.id===b.dataset.id);scanMode=latest.modality;resultView='combined';applyModeUI();renderResult();setTab('scan')})
}
function viewSrc(scan,view){
  if(view==='original') return scan.media.original
  if(scan.modality==='rgb'){
    if(view==='redness') return scan.media.redness_map
    if(view==='pigmentation') return scan.media.pigmentation_map
    return scan.media.overlay
  }
  if(view==='artifact') return scan.media.artifact_mask
  if(view==='porphyrin') return scan.media.porphyrin_mask
  return scan.media.overlay
}
function renderRejectedAttempt(){
  const body=$('#resultBody'), date=$('#resultDate'), badge=$('#compareBadge')
  const attempt=rejectedAttempt, detail=(attempt?.detail && typeof attempt.detail==='object')?attempt.detail:{}
  const guidance=Array.isArray(detail.quality_guidance)?detail.quality_guidance:[]
  const flags=Array.isArray(detail.quality_flags)?detail.quality_flags:[]
  const score=Number.isFinite(detail.capture_quality_score)?`${detail.capture_quality_score}/100`:'Not measured'
  const reason=detail.message||attempt?.message||'This capture did not pass the quality gate.'
  date.textContent='Current attempt'
  badge.textContent='Capture rejected'
  badge.className='compareBadge warn'
  body.className=''
  body.innerHTML=`
    <div class="scienceNote"><b>Capture rejected — not saved.</b> ${reason}</div>
    <div class="analysisMetrics">
      ${metric('Status','Rejected','not added to History or trends')}
      ${metric('Capture quality',detail.capture_quality||'poor',`score ${score}`)}
      ${metric('Issues',flags.length?flags.join(', '):'See guidance','quality gate')}
    </div>
    <div class="scienceNote"><b>Retake guidance</b>${guidance.length?`<ul style="margin:8px 0 0 18px;padding:0">${guidance.map(x=>`<li>${x}</li>`).join('')}</ul>`:'<p>Retake with steady focus, even frontal light, and the face centered in frame.</p>'}</div>
    <div class="scienceNote">The previous saved scan remains in History, but it is intentionally not shown here as the result of this rejected attempt.</div>`
}
function renderResult(){
  const body=$('#resultBody'), date=$('#resultDate'), badge=$('#compareBadge')
  if(rejectedAttempt && rejectedAttempt.mode===scanMode){renderRejectedAttempt();return}
  if(!latest){body.className='empty resultEmpty';body.textContent='Choose a scan type, then capture or upload an image.';date.textContent='Latest scan';badge.classList.add('hidden');return}
  body.className=''; date.textContent=new Date(latest.created_at).toLocaleString()
  const prev=previousSameModality(latest), m=latest.metrics
  if(prev){
    if(latest.modality==='rgb'){
      const d=(m.redness_area_fraction-prev.metrics.redness_area_fraction)*100
      badge.textContent=Math.abs(d)<0.05?'RGB stable vs previous':`${d<0?'↓':'↑'} ${Math.abs(d).toFixed(1)} pp redness area`
      badge.className=`compareBadge ${d<0?'good':d>0?'warn':''}`
    } else {
      const d=m.porphyrin_component_count_proxy-prev.metrics.porphyrin_component_count_proxy
      badge.textContent=Math.abs(d)<1?'Stable vs previous':`${d<0?'↓':'↑'} ${Math.abs(d)} spots vs previous`
      badge.className=`compareBadge ${d<0?'good':d>0?'warn':''}`
    }
  } else badge.classList.add('hidden')

  if(latest.modality==='rgb'){
    if(!['original','redness','pigmentation','combined'].includes(resultView)) resultView='combined'
    const tabs=[['original','Original'],['redness','Redness map'],['pigmentation','Pigmentation map'],['combined','Combined']]
    body.innerHTML=`
      <div class="viewTabs">${tabs.map(([k,l])=>`<button data-result-view="${k}" class="${resultView===k?'active':''}">${l}</button>`).join('')}</div>
      <div class="analysisImage ${resultView}"><img src="${viewSrc(latest,resultView)}" alt="${resultView} analysis"/>${resultView==='combined'?`<div class="legend"><span><i class="dot red"></i>local redness</span><span><i class="dot violet"></i>local pigmentation</span><span><i class="dot green"></i>detected face</span></div>`:''}</div>
      <div class="analysisMetrics">
        ${metric('Redness area',pct(m.redness_area_fraction),'relative skin pixels',prev?deltaText(m.redness_area_fraction,prev.metrics.redness_area_fraction,'pct'):'')}
        ${metric('Red spots',m.red_spot_count_proxy,'local redness components')}
        ${metric('Pigmented area',pct(m.pigmentation_area_fraction),'relative skin pixels',prev?deltaText(m.pigmentation_area_fraction,prev.metrics.pigmentation_area_fraction,'pct'):'')}
        ${metric('Pigmented spots',m.pigmented_spot_count_proxy,'local dark components')}
        ${metric('Texture index',(m.texture_index_proxy||0).toFixed(3),'luminance high-frequency proxy')}
        ${metric('Capture quality',m.capture_quality||'—',(m.quality_flags||[]).join(', ')||'no capture flags')}
      </div>
      <div class="scienceNote"><b>Phone RGB research measurement.</b> These are relative visible-light proxies for longitudinal tracking. They are not diagnoses and are not equivalent to polarized or UV imaging.</div>`
  } else {
    if(!['original','artifact','porphyrin','combined'].includes(resultView)) resultView='combined'
    const tabs=[['original','Original'],['artifact','Artifact map'],['porphyrin','Porphyrin map'],['combined','Combined']]
    body.innerHTML=`
      <div class="viewTabs">${tabs.map(([k,l])=>`<button data-result-view="${k}" class="${resultView===k?'active':''}">${l}</button>`).join('')}</div>
      <div class="analysisImage ${resultView}"><img src="${viewSrc(latest,resultView)}" alt="${resultView} analysis"/>${resultView==='combined'?`<div class="legend"><span><i class="dot red"></i>dark hair / ruler</span><span><i class="dot green"></i>light / reflective</span><span><i class="dot amber"></i>porphyrin</span></div>`:''}</div>
      <div class="analysisMetrics">
        ${metric('Fluorescent spots',m.porphyrin_component_count_proxy,'component proxy',prev?deltaText(m.porphyrin_component_count_proxy,prev.metrics.porphyrin_component_count_proxy):'')}
        ${metric('Fluorescent area',pct(m.porphyrin_area_fraction_valid),'of valid pixels',prev?deltaText(m.porphyrin_area_fraction_valid,prev.metrics.porphyrin_area_fraction_valid,'pct'):'')}
        ${metric('Signal intensity',(m.porphyrin_red_intensity_proxy||0).toFixed(2),'red-channel proxy')}
        ${metric('Dark artifacts',pct(m.dark_artifact_area_fraction),'hair / ruler')}
        ${metric('Light artifacts',pct(m.light_artifact_area_fraction),'reflective / light hair')}
        ${metric('Total excluded',pct(m.artifact_area_fraction),'not used in fluorescence metric')}
      </div>
      <div class="scienceNote"><b>Research measurement.</b> Artifact pixels are excluded rather than reconstructed. Compare scans only when capture conditions are similar.</div>`
  }
  $$('[data-result-view]').forEach(b=>b.onclick=()=>{resultView=b.dataset.resultView;renderResult()})
}
function applyModeUI(){
  $$('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===scanMode))
  if(scanMode==='rgb'){
    $('#uploadTitle').textContent='Capture or upload a front-facing photo'
    $('#uploadHelp').textContent='Natural/neutral light · no beauty filters · up to 20 MB'
    $('#captureTips').innerHTML='<span>Face should fill roughly 20–60% of the frame.</span><span>Use the same lighting, distance and angle for repeat scans.</span>'
    $('#title').textContent='New Phone RGB scan'
  } else {
    $('#uploadTitle').textContent='Upload or capture UV image'
    $('#uploadHelp').textContent='PNG or JPEG · up to 20 MB'
    $('#captureTips').innerHTML='<span>Artifact pixels are excluded, never inpainted.</span><span>Repeat scans under similar capture conditions.</span>'
    $('#title').textContent='New UV scan'
  }
  const same=scansOf(scanMode)
  if(same.length){latest=same[0];resultView='combined'}
  renderResult()
}
$$('[data-mode]').forEach(b=>b.onclick=()=>{rejectedAttempt=null;showError('');scanMode=b.dataset.mode;applyModeUI()})
async function refresh(){
  const [s,t,r,h]=await Promise.all([api('/v1/scans?limit=100'),api('/v1/trends?limit=180'),api('/v1/routine'),api('/health')])
  scans=s;trends=t;health=h
  if(!latest || !scans.some(x=>x.id===latest.id)) latest=scans[0]||null
  $('#morning').value=r.morning.join('\n');$('#evening').value=r.evening.join('\n')
  const st=$('#status');st.textContent=h.rgb_engine_available&&h.uv_model_available?'UV + RGB ready':h.rgb_engine_available?'RGB ready · UV setup needed':'Engine setup needed';st.className=`status ${h.rgb_engine_available?'ready':'warn'}`
  render();applyModeUI()
}
$('#fileInput').onchange=async e=>{
  const f=e.target.files?.[0]; if(!f)return
  showError(''); rejectedAttempt=null
  const p=$('#preview');p.src=URL.createObjectURL(f);p.classList.remove('hidden');$('#dropContent').classList.add('hidden');$('#dropzone').classList.add('busy')
  const fd=new FormData();fd.append('image',f)
  try{
    latest=await api(scanMode==='rgb'?'/v1/rgb/analyze':'/v1/uv/analyze',{method:'POST',body:fd})
    rejectedAttempt=null;resultView='combined';await refresh();renderResult()
  } catch(err){
    rejectedAttempt={mode:scanMode,filename:f.name,message:err.message,detail:err.detail,status:err.status,at:new Date().toISOString()}
    const guidance=Array.isArray(err.detail?.quality_guidance)?err.detail.quality_guidance:[]
    showError([err.message,...guidance].filter(Boolean).join(' '))
    renderResult()
  } finally{$('#dropzone').classList.remove('busy');e.target.value=''}
}
$('#saveRoutine').onclick=async()=>{
  const btn=$('#saveRoutine'), routine={morning:$('#morning').value.split('\n').map(x=>x.trim()).filter(Boolean),evening:$('#evening').value.split('\n').map(x=>x.trim()).filter(Boolean)}
  btn.disabled=true;btn.textContent='Saving…'
  try{await api('/v1/routine',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(routine)});btn.textContent='Saved'}catch(e){showError(e.message)}
  finally{setTimeout(()=>{btn.disabled=false;btn.textContent='Save routine'},800)}
}
refresh().catch(e=>showError(e.message))