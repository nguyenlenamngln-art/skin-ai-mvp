// V1.7.4 — Live previous-position guidance for close-up scan simulator.
(function(){
  const VERSION='1.7.4'
  const SIZE=96
  const SAMPLE_MS=850
  const MATCH_READY_SCORE=62
  const MAX_SHIFT_FRACTION=.15
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const tr=(en,vi)=>locale()==='vi'?vi:en
  let activeKey=null
  let baseline=null
  let state={mode:'idle',ready:true,score:null,shift:null,direction:null}
  let timer=null
  let sampling=false
  let lastSpoken=''
  let lastSpokenAt=0

  function ensureUi(){
    const side=document.querySelector('#dermV171 .dermCaptureSide')
    if(!side||document.querySelector('#dermPositionGuide'))return
    const box=document.createElement('div')
    box.id='dermPositionGuide'
    box.className='dermPositionGuide neutral'
    box.innerHTML=`<div><span>${tr('Previous-position match','Khớp vị trí trước')}</span><b id="dermPositionState">${tr('Checking…','Đang kiểm tra…')}</b></div><small id="dermPositionHint">${tr('If a baseline exists, Skin AI will guide you closer to the same patch before capture.','Nếu đã có ảnh mốc, Skin AI sẽ hướng dẫn bạn trở lại gần cùng vị trí da trước khi chụp.')}</small>`
    const checks=side.querySelector('.dermChecks')
    if(checks)checks.insertAdjacentElement('afterend',box);else side.prepend(box)
  }

  function setUi(mode,label,hint){
    ensureUi()
    const box=document.querySelector('#dermPositionGuide')
    if(!box)return
    box.classList.remove('neutral','good','warn','poor')
    box.classList.add(mode)
    const stateEl=box.querySelector('#dermPositionState')
    const hintEl=box.querySelector('#dermPositionHint')
    if(stateEl&&stateEl.textContent!==label)stateEl.textContent=label
    if(hintEl&&hintEl.textContent!==hint)hintEl.textContent=hint
  }

  function speakOnce(key,en,vi){
    const now=Date.now()
    if(key===lastSpoken&&now-lastSpokenAt<2500)return
    lastSpoken=key;lastSpokenAt=now
    try{
      if(!document.querySelector('#dermAudioToggle')?.checked||!('speechSynthesis' in window))return
      speechSynthesis.cancel()
      const u=new SpeechSynthesisUtterance(tr(en,vi));u.lang=locale()==='vi'?'vi-VN':'en-US';u.rate=.95;speechSynthesis.speak(u)
    }catch(_e){}
  }

  function toGray(image){
    const c=document.createElement('canvas');c.width=SIZE;c.height=SIZE
    const x=c.getContext('2d',{willReadFrequently:true});x.drawImage(image,0,0,SIZE,SIZE)
    const p=x.getImageData(0,0,SIZE,SIZE).data,out=new Float32Array(SIZE*SIZE)
    let sum=0
    for(let i=0,j=0;i<p.length;i+=4,j++){const y=.2126*p[i]+.7152*p[i+1]+.0722*p[i+2];out[j]=y;sum+=y}
    const mean=sum/out.length;let variance=0
    for(let i=0;i<out.length;i++){out[i]-=mean;variance+=out[i]*out[i]}
    const sd=Math.sqrt(variance/out.length)||1
    for(let i=0;i<out.length;i++)out[i]/=sd
    return out
  }

  function videoGray(video){
    const c=document.createElement('canvas');c.width=SIZE;c.height=SIZE
    const x=c.getContext('2d',{willReadFrequently:true});x.drawImage(video,0,0,SIZE,SIZE)
    return toGray(c)
  }

  function corr(a,b,dx,dy){
    let sumA=0,sumB=0,sumAA=0,sumBB=0,sumAB=0,n=0
    for(let y=0;y<SIZE;y++){
      const by=y-dy;if(by<0||by>=SIZE)continue
      for(let x=0;x<SIZE;x++){
        const bx=x-dx;if(bx<0||bx>=SIZE)continue
        const va=a[y*SIZE+x],vb=b[by*SIZE+bx]
        sumA+=va;sumB+=vb;sumAA+=va*va;sumBB+=vb*vb;sumAB+=va*vb;n++
      }
    }
    if(n<SIZE*SIZE*.72)return -1
    const cov=sumAB-(sumA*sumB/n)
    const va=sumAA-(sumA*sumA/n),vb=sumBB-(sumB*sumB/n)
    const den=Math.sqrt(Math.max(va*vb,1e-8))
    return cov/den
  }

  function match(ref,cur){
    let best={corr:-1,dx:0,dy:0}
    for(let dy=-10;dy<=10;dy+=2)for(let dx=-10;dx<=10;dx+=2){
      const c=corr(ref,cur,dx,dy);if(c>best.corr)best={corr:c,dx,dy}
    }
    const shift=Math.sqrt(best.dx*best.dx+best.dy*best.dy)/SIZE
    const similarity=Math.max(0,Math.min(1,(best.corr+1)/2))
    const score=Math.round(100*(.85*similarity+.15*Math.max(0,1-shift/.14))*10)/10
    return {score,shift,dx:best.dx,dy:best.dy,corr:best.corr}
  }

  function directionFor(result){
    const ax=Math.abs(result.dx),ay=Math.abs(result.dy)
    if(Math.max(ax,ay)<=2)return 'centered'
    if(ax>=ay)return result.dx>0?'left':'right'
    return result.dy>0?'up':'down'
  }

  function renderMatch(result){
    const ready=result.score>=MATCH_READY_SCORE&&result.shift<=MAX_SHIFT_FRACTION
    const direction=directionFor(result)
    state={mode:'baseline',ready,score:result.score,shift:result.shift,direction}
    if(ready){
      setUi('good',tr(`Matched · ${Math.round(result.score)}%`,`Đã khớp · ${Math.round(result.score)}%`),tr('Position is close enough to the saved baseline. Hold still for capture.','Vị trí đã gần ảnh mốc. Giữ yên để chụp.'))
      return
    }
    const prompts={
      left:["Move slightly left.",'Di chuyển nhẹ sang trái.'],
      right:["Move slightly right.",'Di chuyển nhẹ sang phải.'],
      up:["Move slightly up.",'Di chuyển nhẹ lên trên.'],
      down:["Move slightly down.",'Di chuyển nhẹ xuống dưới.'],
      centered:["Adjust slightly to match the previous patch.",'Điều chỉnh nhẹ để khớp vùng da trước.']
    }
    const p=prompts[direction]||prompts.centered
    setUi(result.score>=48?'warn':'poor',tr(`Reposition · ${Math.round(result.score)}%`,`Điều chỉnh vị trí · ${Math.round(result.score)}%`),tr(p[0],p[1]))
    speakOnce(direction,p[0],p[1])
  }

  async function loadBaseline(region,subregion){
    const key=`${region}/${subregion}`
    if(key===activeKey)return
    activeKey=key;baseline=null;state={mode:'loading',ready:true,score:null,shift:null,direction:null}
    ensureUi();setUi('neutral',tr('Checking baseline…','Đang kiểm tra ảnh mốc…'),tr('Looking for an earlier capture of this exact position.','Đang tìm ảnh trước của đúng vị trí này.'))
    try{
      const q=new URLSearchParams({region,subregion,subject_key:'my_profile',illumination_mode:'polarized',brightness_level:'2',simulator:'true'})
      const r=await fetch(`/v1/dermatoscope/baseline?${q.toString()}`,{cache:'no-store'})
      if(!r.ok)throw new Error('baseline')
      const data=await r.json()
      if(!data.baseline){
        state={mode:'none',ready:true,score:null,shift:null,direction:null}
        setUi('neutral',tr('New baseline','Tạo ảnh mốc mới'),tr('No previous image exists for this position. Capture quality checks will be used.','Chưa có ảnh trước cho vị trí này. Ứng dụng sẽ dùng các tiêu chí chất lượng ảnh để chụp.'))
        return
      }
      const img=new Image();img.decoding='async'
      img.onload=()=>{
        try{baseline=toGray(img);state={mode:'baseline',ready:false,score:null,shift:null,direction:null};setUi('warn',tr('Find previous position','Tìm lại vị trí trước'),tr('Move slowly until the live image matches the saved baseline.','Di chuyển chậm đến khi hình ảnh hiện tại khớp với ảnh mốc đã lưu.'))}catch(_e){fallback()}
      }
      img.onerror=fallback
      img.src=data.baseline.media.original
    }catch(_e){fallback()}
  }

  function fallback(){
    baseline=null;state={mode:'unavailable',ready:true,score:null,shift:null,direction:null}
    setUi('neutral',tr('Position guidance unavailable','Chưa thể hướng dẫn vị trí'),tr('Capture can continue using the standard image-quality checks.','Vẫn có thể tiếp tục chụp bằng các tiêu chí chất lượng ảnh tiêu chuẩn.'))
  }

  function inferTarget(){
    const active=document.querySelector('#dermV171 .dermRegion.active')
    const counter=document.querySelector('#dermCounter')?.textContent||''
    if(!active)return null
    const region=active.dataset.dermRegion
    const shots={forehead:['left','center','right'],left_cheek:['upper','middle','lower'],right_cheek:['upper','middle','lower'],nose:['center'],chin:['upper','lower'],custom:['custom']}[region]||[]
    const idx=Math.max(0,(parseInt(counter.split('/')[0])||1)-1)
    const subregion=shots[idx]
    return subregion?{region,subregion}:null
  }

  async function sample(){
    if(sampling)return
    const capture=document.querySelector('#dermCapture')
    const video=document.querySelector('#dermVideo')
    if(!capture||capture.hidden||!video||video.readyState<2)return
    const target=inferTarget();if(!target)return
    await loadBaseline(target.region,target.subregion)
    if(!baseline)return
    sampling=true
    try{renderMatch(match(baseline,videoGray(video)))}catch(_e){fallback()}finally{sampling=false}
  }

  function ready(){
    return state.mode!=='baseline'||Boolean(state.ready)
  }

  function reset(){activeKey=null;baseline=null;state={mode:'idle',ready:true,score:null,shift:null,direction:null};lastSpoken='';ensureUi()}

  function start(){
    ensureUi()
    if(timer)clearInterval(timer)
    timer=setInterval(sample,SAMPLE_MS)
    sample()
  }

  window.addEventListener('skin-ai:locale-change',()=>{activeKey=null;ensureUi();sample()})
  window.skinDermatoscopeLiveGuidance={version:VERSION,ready,state:()=>({...state}),reset,sample}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start()
})()
