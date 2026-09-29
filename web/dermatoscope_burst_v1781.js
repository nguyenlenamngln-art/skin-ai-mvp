// V1.7.8.1 — Three-frame burst capture enhancer.
// Keeps the stable guided-capture UI intact and enriches only the close-up capture POST.
(function(){
  const VERSION='1.7.8.1'
  const FRAME_COUNT=3
  const GAP_MS=170
  const ANALYSIS_W=96
  const ANALYSIS_H=72
  const baseFetch=window.fetch.bind(window)
  if(window.skinDermatoscopeBurst?.version===VERSION)return

  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const tr=(en,vi)=>locale()==='vi'?vi:en
  const sleep=(ms)=>new Promise(r=>setTimeout(r,ms))
  const clamp=(v,a=0,b=100)=>Math.max(a,Math.min(b,v))

  function status(textEn,textVi){
    const el=document.querySelector('#dermStatus')
    if(el)el.textContent=tr(textEn,textVi)
  }

  function targetUrl(input){
    try{
      if(typeof input==='string')return new URL(input,location.href).pathname
      if(input instanceof Request)return new URL(input.url,location.href).pathname
    }catch(_e){}
    return ''
  }

  async function bitmapFromBlob(blob){
    if('createImageBitmap' in window)return await createImageBitmap(blob)
    return await new Promise((resolve,reject)=>{
      const url=URL.createObjectURL(blob),img=new Image()
      img.onload=()=>{URL.revokeObjectURL(url);resolve(img)}
      img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('decode'))}
      img.src=url
    })
  }

  async function analyseBlob(blob){
    const img=await bitmapFromBlob(blob)
    const c=document.createElement('canvas');c.width=ANALYSIS_W;c.height=ANALYSIS_H
    const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0,ANALYSIS_W,ANALYSIS_H)
    if(typeof img.close==='function')img.close()
    const data=ctx.getImageData(0,0,ANALYSIS_W,ANALYSIS_H).data
    const gray=new Float32Array(ANALYSIS_W*ANALYSIS_H)
    let sum=0,edge=0,clip=0
    for(let i=0,j=0;i<data.length;i+=4,j++){
      const y=.2126*data[i]+.7152*data[i+1]+.0722*data[i+2]
      gray[j]=y;sum+=y;if(y>247)clip++
    }
    for(let y=1;y<ANALYSIS_H;y+=2)for(let x=1;x<ANALYSIS_W;x+=2){
      const i=y*ANALYSIS_W+x;edge+=Math.abs(gray[i]-gray[i-1])+Math.abs(gray[i]-gray[i-ANALYSIS_W])
    }
    const n=ANALYSIS_W*ANALYSIS_H
    const samples=Math.max(1,Math.floor((ANALYSIS_W-1)/2)*Math.floor((ANALYSIS_H-1)/2))
    const mean=sum/n,glare=clip/n,sharpness=edge/samples
    const exposureScore=clamp(100-Math.abs(mean-132)*.78)
    const sharpnessScore=clamp((sharpness-8)/(35-8)*100)
    const glareScore=clamp(100-(glare/.08)*100)
    const qualityScore=Math.round(.45*sharpnessScore+.35*exposureScore+.20*glareScore)
    return {gray,mean,glare,sharpness,exposureScore,sharpnessScore,glareScore,qualityScore}
  }

  function align(a,b){
    let best={dx:0,dy:0,mad:1e9}
    for(let dy=-4;dy<=4;dy++)for(let dx=-4;dx<=4;dx++){
      let total=0,count=0
      const x0=Math.max(0,-dx),x1=Math.min(ANALYSIS_W,ANALYSIS_W-dx)
      const y0=Math.max(0,-dy),y1=Math.min(ANALYSIS_H,ANALYSIS_H-dy)
      for(let y=y0;y<y1;y+=2)for(let x=x0;x<x1;x+=2){
        total+=Math.abs(a[y*ANALYSIS_W+x]-b[(y+dy)*ANALYSIS_W+(x+dx)]);count++
      }
      const mad=total/Math.max(1,count)
      if(mad<best.mad)best={dx,dy,mad}
    }
    return {...best,similarity:Math.round(clamp(100-best.mad*3.2))}
  }

  async function videoBlob(){
    const video=document.querySelector('#dermVideo')
    if(!video||video.readyState<2||!video.videoWidth||!video.videoHeight)throw new Error('video unavailable')
    const scale=Math.min(1,1600/video.videoWidth)
    const c=document.createElement('canvas')
    c.width=Math.max(1,Math.round(video.videoWidth*scale));c.height=Math.max(1,Math.round(video.videoHeight*scale))
    c.getContext('2d').drawImage(video,0,0,c.width,c.height)
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',.94))
    if(!blob)throw new Error('capture failed')
    return blob
  }

  async function enrich(form){
    const first=form.get('image')
    if(!(first instanceof Blob))return form
    status('Capturing 3-frame burst…','Đang chụp chuỗi 3 ảnh…')
    const blobs=[first]
    while(blobs.length<FRAME_COUNT){
      await sleep(GAP_MS)
      blobs.push(await videoBlob())
      status(`Capturing frame ${blobs.length}/${FRAME_COUNT}…`,`Đang chụp ảnh ${blobs.length}/${FRAME_COUNT}…`)
    }
    const metrics=[]
    for(const blob of blobs)metrics.push(await analyseBlob(blob))
    let selectedIndex=0
    for(let i=1;i<metrics.length;i++)if(metrics[i].qualityScore>metrics[selectedIndex].qualityScore)selectedIndex=i
    const alignments=metrics.map((m,i)=>i===selectedIndex?{dx:0,dy:0,mad:0,similarity:100}:align(metrics[selectedIndex].gray,m.gray))
    const alignmentStatus=alignments.every(x=>x.similarity>=55)?'good':alignments.every(x=>x.similarity>=38)?'borderline':'poor'
    const meta={
      version:VERSION,
      frame_count:FRAME_COUNT,
      interval_ms:GAP_MS,
      selected_frame:selectedIndex+1,
      selection_reason:'highest_quality_score',
      alignment_status:alignmentStatus,
      fusion_used:false,
      fusion_reason:'deferred_until_physical_device_validation',
      frames:metrics.map((m,i)=>({
        index:i+1,
        quality_score:m.qualityScore,
        sharpness_score:Math.round(m.sharpnessScore),
        exposure_score:Math.round(m.exposureScore),
        glare_score:Math.round(m.glareScore),
        mean_luma:Number(m.mean.toFixed(2)),
        glare_fraction:Number(m.glare.toFixed(5)),
        shift_x:alignments[i].dx,
        shift_y:alignments[i].dy,
        alignment_similarity:alignments[i].similarity
      }))
    }
    form.set('image',blobs[selectedIndex],`skinscope-burst-selected-${selectedIndex+1}-${Date.now()}.jpg`)
    blobs.forEach((blob,i)=>form.append(`burst_frame_${i+1}`,blob,`skinscope-burst-${i+1}-${Date.now()}.jpg`))
    form.set('burst_metadata',JSON.stringify(meta))
    status('Burst complete — saving best frame…','Đã chụp đủ 3 ảnh — đang lưu ảnh tốt nhất…')
    return form
  }

  window.fetch=async function(input,init){
    const path=targetUrl(input)
    const isCapture=path==='/v1/dermatoscope/captures'&&String(init?.method||'GET').toUpperCase()==='POST'&&init?.body instanceof FormData
    if(!isCapture)return baseFetch(input,init)
    try{
      const body=await enrich(init.body)
      return await baseFetch(input,{...init,body})
    }catch(err){
      console.warn('[Skin AI burst] falling back to single frame',err)
      status('Burst unavailable — saving the accepted frame.','Không thể chụp chuỗi — đang lưu ảnh đã đạt yêu cầu.')
      return await baseFetch(input,init)
    }
  }

  window.skinDermatoscopeBurst={version:VERSION,frameCount:FRAME_COUNT,gapMs:GAP_MS}
  document.documentElement.dataset.dermatoscopeBurstVersion=VERSION
})()
