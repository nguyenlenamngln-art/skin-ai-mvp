const $ = q => document.querySelector(q)
const $$ = q => [...document.querySelectorAll(q)]
const pct = (x=0) => `${(x*100).toFixed(1)}%`
const signed = (n, digits=0) => `${n>0?'+':''}${n.toFixed(digits)}`
const titles = {home:'Your skin, over time.',scan:'New UV scan',history:'Scan history',routine:'Routine tracker'}
let scans=[], trends=[], latest=null, resultView='combined'

async function api(path, options={}){
  const r=await fetch(path,options)
  const data=await r.json().catch(()=>({}))
  if(!r.ok) throw new Error(typeof data.detail==='string'?data.detail:(data.detail?.message||`Request failed (${r.status})`))
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
function previousScan(){
  if(!latest) return null
  const i=scans.findIndex(s=>s.id===latest.id)
  return i>=0 && i<scans.length-1 ? scans[i+1] : null
}
function deltaText(curr,prev,kind='number'){
  if(prev==null || !Number.isFinite(curr) || !Number.isFinite(prev)) return ''
  const d=curr-prev
  if(Math.abs(d)<0.00001) return 'no change'
  if(kind==='pct') return `${signed(d*100,1)} pp vs previous`
  return `${signed(d,0)} vs previous`
}
function render(){
  latest=latest||scans[0]||null
  $('#latestSignal').textContent=latest?`${latest.metrics.porphyrin_component_count_proxy} fluorescent components`:'No scans yet'
  $('#latestCopy').textContent=latest?`Artifact-corrected analysis from ${new Date(latest.created_at).toLocaleDateString()}.`:'Start with one UV fluorescence image to create your baseline.'
  const prev=latest?previousScan():null
  $('#metricCards').innerHTML=[
    metric('Fluorescent spots',latest?latest.metrics.porphyrin_component_count_proxy:'—','porphyrin component proxy',latest&&prev?deltaText(latest.metrics.porphyrin_component_count_proxy,prev.metrics.porphyrin_component_count_proxy):''),
    metric('Fluorescent area',latest?pct(latest.metrics.porphyrin_area_fraction_valid):'—','of valid observed pixels',latest&&prev?deltaText(latest.metrics.porphyrin_area_fraction_valid,prev.metrics.porphyrin_area_fraction_valid,'pct'):''),
    metric('Signal intensity',latest?(latest.metrics.porphyrin_red_intensity_proxy||0).toFixed(2):'—','red-channel proxy'),
    metric('Artifact excluded',latest?pct(latest.metrics.artifact_area_fraction):'—','hair / reflections / ruler')
  ].join('')
  if(scans.length<2) $('#insightText').textContent='Run another scan under similar lighting and distance to begin tracking change.'
  else {
    const d=scans[0].metrics.porphyrin_component_count_proxy-scans[1].metrics.porphyrin_component_count_proxy
    $('#insightText').textContent=Math.abs(d)<3?'Your recent porphyrin spot count is broadly stable. Keep capture conditions consistent before drawing conclusions.':d<0?`Your latest scan shows ${Math.abs(d)} fewer fluorescent components than the previous scan.`:`Your latest scan shows ${d} more fluorescent components than the previous scan.`
  }
  renderTrend(); renderHistory(); renderResult()
}
function renderTrend(){
  const vals=trends.map(x=>x.porphyrin_component_count_proxy).filter(Number.isFinite), svg=$('#trendSvg'), empty=$('#trendEmpty')
  if(vals.length<2){svg.innerHTML='';empty.classList.remove('hidden');return}
  empty.classList.add('hidden')
  const mn=Math.min(...vals),mx=Math.max(...vals),span=Math.max(1,mx-mn)
  const pts=vals.map((v,i)=>`${20+i*(560/(vals.length-1))},${140-((v-mn)/span)*105}`).join(' ')
  svg.innerHTML=`<line x1="20" y1="140" x2="580" y2="140" stroke="#d8dbd3"/><polyline points="${pts}" fill="none" stroke="#496956" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>`
}
function renderHistory(){
  $('#historyTitle').textContent=`${scans.length} saved scans`
  $('#historyList').innerHTML=scans.length?scans.map((s,i)=>{
    const older=scans[i+1]
    const d=older?s.metrics.porphyrin_component_count_proxy-older.metrics.porphyrin_component_count_proxy:null
    return `<button class="historyRow" data-id="${s.id}"><img src="${s.media.overlay}"/><div><b>${new Date(s.created_at).toLocaleString()}</b><span>${s.source_name||'UV scan'} · ${pct(s.metrics.artifact_area_fraction)} artifacts</span></div><div class="historyStat"><b>${s.metrics.porphyrin_component_count_proxy}</b><span>spots${d==null?'':` · ${signed(d,0)}`}</span></div><span>›</span></button>`
  }).join(''):'<div class="empty">No scans yet.</div>'
  $$('.historyRow').forEach(b=>b.onclick=()=>{latest=scans.find(s=>s.id===b.dataset.id);resultView='combined';renderResult();setTab('scan')})
}
function viewSrc(scan,view){
  if(view==='original') return scan.media.original
  if(view==='artifact') return scan.media.artifact_mask
  if(view==='porphyrin') return scan.media.porphyrin_mask
  return scan.media.overlay
}
function renderResult(){
  const body=$('#resultBody'), date=$('#resultDate'), badge=$('#compareBadge')
  if(!latest){body.className='empty resultEmpty';body.textContent='Your artifact-corrected overlay and fluorescence metrics will appear here.';date.textContent='Latest scan';badge.classList.add('hidden');return}
  body.className=''; date.textContent=new Date(latest.created_at).toLocaleString()
  const prev=previousScan(), m=latest.metrics
  if(prev){
    const d=m.porphyrin_component_count_proxy-prev.metrics.porphyrin_component_count_proxy
    badge.textContent=Math.abs(d)<1?'Stable vs previous':`${d<0?'↓':'↑'} ${Math.abs(d)} spots vs previous`
    badge.className=`compareBadge ${d<0?'good':d>0?'warn':''}`
  } else badge.classList.add('hidden')
  body.innerHTML=`
    <div class="viewTabs">
      ${[['original','Original'],['artifact','Artifact map'],['porphyrin','Porphyrin map'],['combined','Combined']].map(([k,l])=>`<button data-result-view="${k}" class="${resultView===k?'active':''}">${l}</button>`).join('')}
    </div>
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
  $$('[data-result-view]').forEach(b=>b.onclick=()=>{resultView=b.dataset.resultView;renderResult()})
}
async function refresh(){
  const [s,t,r,h]=await Promise.all([api('/v1/scans?limit=50'),api('/v1/trends?limit=90'),api('/v1/routine'),api('/health')])
  scans=s;trends=t
  if(!latest || !scans.some(x=>x.id===latest.id)) latest=scans[0]||null
  $('#morning').value=r.morning.join('\n');$('#evening').value=r.evening.join('\n')
  const st=$('#status');st.textContent=h.model_available?'UV engine ready':'Model setup needed';st.className=`status ${h.model_available?'ready':'warn'}`
  $('#fileInput').disabled=!h.model_available; render()
}
$('#fileInput').onchange=async e=>{
  const f=e.target.files?.[0]; if(!f)return
  showError(''); const p=$('#preview');p.src=URL.createObjectURL(f);p.classList.remove('hidden');$('#dropContent').classList.add('hidden');$('#dropzone').classList.add('busy')
  const fd=new FormData();fd.append('image',f)
  try{ latest=await api('/v1/uv/analyze',{method:'POST',body:fd});resultView='combined';await refresh();renderResult() }
  catch(err){showError(err.message)} finally{$('#dropzone').classList.remove('busy')}
}
$('#saveRoutine').onclick=async()=>{
  const btn=$('#saveRoutine'), routine={morning:$('#morning').value.split('\n').map(x=>x.trim()).filter(Boolean),evening:$('#evening').value.split('\n').map(x=>x.trim()).filter(Boolean)}
  btn.disabled=true;btn.textContent='Saving…'
  try{await api('/v1/routine',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(routine)});btn.textContent='Saved'}catch(e){showError(e.message)}
  finally{setTimeout(()=>{btn.disabled=false;btn.textContent='Save routine'},800)}
}
refresh().catch(e=>showError(e.message))
