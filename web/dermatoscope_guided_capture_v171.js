// V1.7.1 — Guided dermatoscope capture simulator.
// Capture-only foundation. Quality thresholds are provisional until physical DE-500 validation.
(function(){
  const VERSION='1.7.1'
  const HOLD_MS=800
  const SAMPLE_MS=180
  const COOLDOWN_MS=1400
  const REGIONS={
    forehead:{en:'Forehead',vi:'Trán',shots:['left','center','right']},
    left_cheek:{en:'Left cheek',vi:'Má trái',shots:['upper','middle','lower']},
    right_cheek:{en:'Right cheek',vi:'Má phải',shots:['upper','middle','lower']},
    nose:{en:'Nose',vi:'Mũi',shots:['center']},
    chin:{en:'Chin',vi:'Cằm',shots:['upper','lower']},
    custom:{en:'Custom area',vi:'Vùng tùy chọn',shots:['custom']}
  }
  let stream=null,timer=null,previous=null,goodSince=0,lastCaptureAt=0,busy=false,selected=null,shotIndex=0,captured=[]
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const tr=(en,vi)=>locale()==='vi'?vi:en
  const research=()=>Boolean(window.skinDermatoscopeTransition?.researchMode)
  const root=()=>document.querySelector('#dermV171')

  function regionLabel(code){const r=REGIONS[code];return r?(locale()==='vi'?r.vi:r.en):code}
  function subLabel(code){const map={upper:['Upper','Phía trên'],middle:['Middle','Ở giữa'],lower:['Lower','Phía dưới'],center:['Center','Chính giữa'],left:['Left','Bên trái'],right:['Right','Bên phải'],custom:['Selected area','Vùng đã chọn']};return tr(...(map[code]||[code,code]))}
  function speak(en,vi){
    const text=tr(en,vi)
    try{
      if(!document.querySelector('#dermAudioToggle')?.checked||!('speechSynthesis' in window))return
      speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=locale()==='vi'?'vi-VN':'en-US';u.rate=.95;speechSynthesis.speak(u)
    }catch(_e){}
  }
  function beep(freq=660,duration=.08){try{const C=window.AudioContext||window.webkitAudioContext;if(!C)return;const c=new C(),o=c.createOscillator(),g=c.createGain();o.frequency.value=freq;o.connect(g);g.connect(c.destination);g.gain.value=.035;o.start();o.stop(c.currentTime+duration);o.onended=()=>c.close()}catch(_e){}}

  function build(){
    const scan=document.querySelector('#scan');if(!scan||root())return
    const box=document.createElement('div');box.id='dermV171';box.className='dermV171 active'
    box.innerHTML=`<div class="card"><span class="eyebrow">${tr('DERMATOSCOPE SCAN','QUÉT DERMATOSCOPE')}</span><h2>${tr('Choose an area to examine','Chọn vùng cần kiểm tra')}</h2><p class="dermNotice">${tr('DE-500 workflow · Polarized · Brightness level 2. Until the device arrives, the rear phone camera is used only as a capture simulator.','Quy trình DE-500 · Phân cực · Mức sáng 2. Trong lúc chờ thiết bị, camera sau của điện thoại chỉ được dùng để mô phỏng quy trình chụp.')}</p><div class="dermRegionGrid">${Object.keys(REGIONS).map(k=>`<button type="button" class="dermRegion" data-derm-region="${k}"><strong>${regionLabel(k)}</strong><small>${REGIONS[k].shots.length} ${tr(REGIONS[k].shots.length===1?'snapshot':'snapshots','ảnh')}</small></button>`).join('')}</div></div>
      <div class="card" id="dermSetup" hidden><span class="eyebrow">${tr('DEVICE SETUP','THIẾT LẬP THIẾT BỊ')}</span><h3>IBOOLO DE-500</h3><div class="dermSetupGrid"><div class="dermSetupBox"><span>${tr('Mode','Chế độ')}</span><b>${tr('Polarized','Phân cực')}</b></div><div class="dermSetupBox"><span>${tr('Brightness','Độ sáng')}</span><b>${tr('Level 2','Mức 2')}</b></div></div><label style="display:flex;gap:8px;align-items:center;margin-top:14px"><input id="dermAudioToggle" type="checkbox" checked> ${tr('Audio guidance','Hướng dẫn bằng giọng nói')}</label><div class="dermActions"><button type="button" id="dermStart">${tr('Start guided capture','Bắt đầu chụp có hướng dẫn')}</button></div></div>
      <div class="card" id="dermCapture" hidden><div class="dermShotHeader"><div><span class="eyebrow" id="dermStepLabel"></span><h3 id="dermTargetLabel"></h3></div><b id="dermCounter"></b></div><div class="dermCameraStage"><video id="dermVideo" autoplay playsinline muted></video><div class="dermTarget"></div></div><div class="dermChecks"><div class="dermCheck" data-check="exposure"><span>${tr('Exposure','Phơi sáng')}</span><b>—</b></div><div class="dermCheck" data-check="sharpness"><span>${tr('Sharpness','Độ nét')}</span><b>—</b></div><div class="dermCheck" data-check="stability"><span>${tr('Stability','Độ ổn định')}</span><b>—</b></div><div class="dermCheck" data-check="glare"><span>${tr('Glare','Chói sáng')}</span><b>—</b></div></div><div class="dermProgress"><i id="dermHoldBar"></i></div><p class="dermStatus" id="dermStatus"></p><canvas id="dermCanvas" hidden></canvas><div class="dermActions"><button type="button" class="ghost" id="dermCancel">${tr('Cancel','Hủy')}</button></div></div>
      <div class="card" id="dermComplete" hidden><span class="eyebrow">${tr('CAPTURE COMPLETE','ĐÃ CHỤP XONG')}</span><h3 id="dermCompleteTitle"></h3><p class="dermNotice">${tr('Images are stored as capture-only research data. No dermatoscope analysis is enabled yet.','Ảnh được lưu dưới dạng dữ liệu nghiên cứu chỉ-chụp. Phân tích dermatoscope chưa được bật.')}</p><div class="dermCapturedGrid" id="dermCapturedGrid"></div><div class="dermActions"><button type="button" id="dermAgain">${tr('Examine another area','Kiểm tra vùng khác')}</button></div></div>`
    const grid=scan.querySelector('.scan-grid');scan.insertBefore(box,grid)
    if(!research())grid.classList.add('dermHiddenLegacy')
    box.querySelectorAll('[data-derm-region]').forEach(b=>b.onclick=()=>selectRegion(b.dataset.dermRegion))
    box.querySelector('#dermStart').onclick=start
    box.querySelector('#dermCancel').onclick=reset
    box.querySelector('#dermAgain').onclick=reset
  }

  function selectRegion(code){selected=code;shotIndex=0;captured=[];root().querySelectorAll('.dermRegion').forEach(x=>x.classList.toggle('active',x.dataset.dermRegion===code));root().querySelector('#dermSetup').hidden=false;root().querySelector('#dermSetup').scrollIntoView({behavior:'smooth',block:'center'})}
  function setCheck(name,state,text){const e=root()?.querySelector(`[data-check="${name}"]`);if(!e)return;e.classList.remove('good','warn','poor');e.classList.add(state);e.querySelector('b').textContent=text}
  function currentSub(){return selected?REGIONS[selected].shots[shotIndex]:null}
  function updateTarget(){
    const shots=REGIONS[selected].shots,sub=currentSub();root().querySelector('#dermStepLabel').textContent=`${regionLabel(selected)} · ${shotIndex+1}/${shots.length}`;root().querySelector('#dermTargetLabel').textContent=subLabel(sub);root().querySelector('#dermCounter').textContent=`${shotIndex+1} / ${shots.length}`;root().querySelector('#dermStatus').textContent=tr('Position the dermatoscope, then hold still.','Đặt dermatoscope đúng vị trí rồi giữ yên.');root().querySelector('#dermHoldBar').style.width='0%';goodSince=0;previous=null
    speak(`Place the dermatoscope on the ${subLabel(sub).toLowerCase()} ${regionLabel(selected).toLowerCase()}.`, `Đặt máy soi vào vùng ${subLabel(sub).toLowerCase()} của ${regionLabel(selected).toLowerCase()}.`)
  }
  async function start(){
    if(!selected)return
    try{
      stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1920},height:{ideal:1440}},audio:false})
      const video=root().querySelector('#dermVideo');video.srcObject=stream;await video.play();root().querySelector('#dermSetup').hidden=true;root().querySelector('#dermCapture').hidden=false;updateTarget();timer=setInterval(sample,SAMPLE_MS)
    }catch(e){root().querySelector('#dermStatus').textContent=tr('Rear camera access is required for guided capture.','Cần quyền truy cập camera sau để chụp có hướng dẫn.')}
  }
  function metrics(image,w,h){
    const p=image.data,g=new Float32Array(w*h);let sum=0,clip=0,edge=0
    for(let i=0,j=0;i<p.length;i+=4,j++){const y=.2126*p[i]+.7152*p[i+1]+.0722*p[i+2];g[j]=y;sum+=y;if(y>247)clip++}
    for(let y=1;y<h;y+=2)for(let x=1;x<w;x+=2){const i=y*w+x;edge+=Math.abs(g[i]-g[i-1])+Math.abs(g[i]-g[i-w])}
    const n=w*h,samples=Math.max(1,Math.floor((w-1)/2)*Math.floor((h-1)/2)),mean=sum/n,glare=clip/n
    let motion=99;if(previous&&previous.length===g.length){motion=0;let c=0;for(let i=0;i<g.length;i+=8){motion+=Math.abs(g[i]-previous[i]);c++}motion/=Math.max(1,c)}previous=g
    return {mean,glare,edge:edge/samples,motion}
  }
  function evaluate(m){return {exposure:m.mean>=55&&m.mean<=210,sharpness:m.edge>=16,stability:m.motion<=3.6,glare:m.glare<=.08}}
  function score(v,min,max,invert=false){const x=Math.max(0,Math.min(1,(v-min)/(max-min)));return Math.round(100*(invert?1-x:x))}
  function sample(){
    if(busy||Date.now()-lastCaptureAt<COOLDOWN_MS)return
    const video=root()?.querySelector('#dermVideo'),canvas=root()?.querySelector('#dermCanvas');if(!video||video.readyState<2)return
    const w=180,h=Math.max(120,Math.round(w*video.videoHeight/Math.max(1,video.videoWidth)));canvas.width=w;canvas.height=h;const c=canvas.getContext('2d',{willReadFrequently:true});c.drawImage(video,0,0,w,h);const m=metrics(c.getImageData(0,0,w,h),w,h),q=evaluate(m)
    setCheck('exposure',q.exposure?'good':'poor',q.exposure?tr('Good','Tốt'):tr('Adjust','Điều chỉnh'));setCheck('sharpness',q.sharpness?'good':'poor',q.sharpness?tr('Good','Tốt'):tr('Refocus','Lấy nét lại'));setCheck('stability',q.stability?'good':'warn',q.stability?tr('Stable','Ổn định'):tr('Hold still','Giữ yên'));setCheck('glare',q.glare?'good':'poor',q.glare?tr('Good','Tốt'):tr('Reduce glare','Giảm chói'))
    const all=q.exposure&&q.sharpness&&q.stability&&q.glare
    if(all){if(!goodSince){goodSince=Date.now();speak('Hold still.','Giữ yên.')}const held=Date.now()-goodSince;root().querySelector('#dermHoldBar').style.width=`${Math.min(100,held/HOLD_MS*100)}%`;root().querySelector('#dermStatus').textContent=tr('All checks passed — hold still for auto-capture.','Tất cả tiêu chí đạt — giữ yên để tự động chụp.');if(held>=HOLD_MS)capture(m)}else{goodSince=0;root().querySelector('#dermHoldBar').style.width='0%';root().querySelector('#dermStatus').textContent=tr('Waiting for all capture criteria.','Đang chờ tất cả tiêu chí chụp đạt yêu cầu.')}
  }
  async function capture(m){
    if(busy)return;busy=true;goodSince=0;const video=root().querySelector('#dermVideo'),canvas=root().querySelector('#dermCanvas');const scale=Math.min(1,1600/video.videoWidth);canvas.width=Math.max(1,Math.round(video.videoWidth*scale));canvas.height=Math.max(1,Math.round(video.videoHeight*scale));canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);const blob=await new Promise(r=>canvas.toBlob(r,'image/jpeg',.94));if(!blob){busy=false;return}
    const sub=currentSub(),form=new FormData();form.append('image',blob,`de500-${selected}-${sub}-${Date.now()}.jpg`);form.append('region',selected);form.append('subregion',sub);form.append('sequence_index',String(shotIndex+1));form.append('illumination_mode','polarized');form.append('brightness_level','2');form.append('simulator','true');form.append('sharpness_score',String(score(m.edge,8,35)));form.append('exposure_score',String(Math.max(0,100-Math.abs(m.mean-132)*1.1)));form.append('motion_score',String(score(m.motion,0,10,true)));form.append('glare_fraction',String(m.glare));form.append('client_device',navigator.userAgent.slice(0,80));form.append('camera_label',stream?.getVideoTracks?.()[0]?.label||'rear camera')
    try{
      const r=await fetch('/v1/dermatoscope/captures',{method:'POST',body:form});if(!r.ok)throw new Error(`capture ${r.status}`);const data=await r.json();captured.push(data);lastCaptureAt=Date.now();beep();speak('Image captured.','Đã chụp ảnh.');shotIndex++
      if(shotIndex>=REGIONS[selected].shots.length){finish()}else{setTimeout(()=>{busy=false;updateTarget()},COOLDOWN_MS)}
    }catch(_e){busy=false;root().querySelector('#dermStatus').textContent=tr('Capture could not be saved. Hold still and try again.','Không thể lưu ảnh. Giữ yên và thử lại.')}
  }
  function stopCamera(){if(timer){clearInterval(timer);timer=null}if(stream){stream.getTracks().forEach(t=>t.stop());stream=null}previous=null}
  function finish(){stopCamera();root().querySelector('#dermCapture').hidden=true;root().querySelector('#dermComplete').hidden=false;root().querySelector('#dermCompleteTitle').textContent=`${regionLabel(selected)} · ${captured.length} ${tr('images','ảnh')}`;root().querySelector('#dermCapturedGrid').innerHTML=captured.map(x=>`<img src="${x.media.original}" alt="${regionLabel(selected)} ${x.subregion}">`).join('');speak(`${regionLabel(selected)} complete.`, `Đã hoàn thành vùng ${regionLabel(selected)}.`);busy=false}
  function reset(){stopCamera();selected=null;shotIndex=0;captured=[];busy=false;root()?.querySelectorAll('.dermRegion').forEach(x=>x.classList.remove('active'));if(root()){root().querySelector('#dermSetup').hidden=true;root().querySelector('#dermCapture').hidden=true;root().querySelector('#dermComplete').hidden=true;root().scrollIntoView({behavior:'smooth',block:'start'})}}
  function relocalize(){const old=selected;const parent=root()?.parentNode;if(parent){root().remove();build();if(old)selectRegion(old)}}
  window.addEventListener('skin-ai:locale-change',relocalize)
  window.skinDermatoscopeCapture={version:VERSION,regions:REGIONS,reset}
  build()
})()