// V1.5.9.2 — Visual Registration & Comparison Layout
// Presentation-only refinement. RGB measurements remain V1.5.2 / Capture Protocol V1.4.
(function(){
  const VERSION='1.5.9.2'
  let scheduled=false

  const finite=v=>Number.isFinite(Number(v))
  const comparable=()=> (typeof scans!=='undefined'?scans:[]).filter(s=>
    s.modality==='rgb' &&
    String(s.metrics?.rgb_engine_version)==='1.5.2' &&
    s.metrics?.capture_quality==='good' &&
    s.metrics?.longitudinal_eligible!==false
  )

  function bbox(scan){
    const b=scan?.metrics?.face_bbox
    if(!b||![b.x,b.y,b.w,b.h].every(finite)||Number(b.w)<=0||Number(b.h)<=0)return null
    return {x:Number(b.x),y:Number(b.y),w:Number(b.w),h:Number(b.h)}
  }

  function geometryTransform(img,scan,frame){
    const b=bbox(scan)
    if(!img||!b||!frame)return null
    const cw=frame.clientWidth,ch=frame.clientHeight,nw=img.naturalWidth,nh=img.naturalHeight
    if(!cw||!ch||!nw||!nh)return null

    // Standardize both face width and face height rather than width alone.
    // Geometric mean avoids overreacting to small Haar box aspect differences.
    const targetFaceW=cw*.48
    const targetFaceH=ch*.64
    const sx=targetFaceW/b.w
    const sy=targetFaceH/b.h
    let scale=Math.sqrt(Math.max(sx,1e-9)*Math.max(sy,1e-9))

    // Always cover the visual frame so transformed image edges never expose a seam.
    scale=Math.max(scale,cw/nw,ch/nh)

    // Anchor around the upper-mid face (eye/nose region), which is more stable for
    // comparison than the lower face center used in V1.5.9.
    const anchorX=b.x+b.w*.50
    const anchorY=b.y+b.h*.42
    const targetX=cw*.50
    const targetY=ch*.43

    const left=targetX-anchorX*scale
    const top=targetY-anchorY*scale
    return {scale,left,top,anchorX,anchorY,targetX,targetY,nw,nh}
  }

  function applyTransform(img,t,residual){
    if(!img||!t)return
    const r=residual||{dx:0,dy:0,scale:1,angle:0}
    img.style.width=`${t.nw*t.scale}px`
    img.style.height=`${t.nh*t.scale}px`
    img.style.maxWidth='none'
    img.style.maxHeight='none'
    img.style.left=`${t.left}px`
    img.style.top=`${t.top}px`
    img.style.position='absolute'
    img.style.transformOrigin=`${(t.anchorX/t.nw)*100}% ${(t.anchorY/t.nh)*100}%`
    img.style.transform=`translate(${r.dx}px,${r.dy}px) rotate(${r.angle}deg) scale(${r.scale})`
  }

  function drawFacePatch(ctx,img,b,size,transform){
    const marginX=.10*b.w, marginTop=.08*b.h
    const sx=b.x+marginX
    const sy=b.y+marginTop
    const sw=b.w-marginX*2
    const sh=b.h*.68
    ctx.save()
    ctx.clearRect(0,0,size,size)
    ctx.fillStyle='#777';ctx.fillRect(0,0,size,size)
    ctx.translate(size/2+(transform?.dx||0),size/2+(transform?.dy||0))
    ctx.rotate(((transform?.angle||0)*Math.PI)/180)
    ctx.scale(transform?.scale||1,transform?.scale||1)
    ctx.translate(-size/2,-size/2)
    ctx.drawImage(img,sx,sy,sw,sh,0,0,size,size)
    ctx.restore()
  }

  function grayscaleNormalized(data){
    const out=new Float32Array(data.length/4)
    let mean=0
    for(let i=0,j=0;i<data.length;i+=4,j++){
      const v=.299*data[i]+.587*data[i+1]+.114*data[i+2]
      out[j]=v;mean+=v
    }
    mean/=Math.max(1,out.length)
    let variance=0
    for(let i=0;i<out.length;i++){const d=out[i]-mean;variance+=d*d}
    const sd=Math.sqrt(variance/Math.max(1,out.length))||1
    for(let i=0;i<out.length;i++)out[i]=(out[i]-mean)/sd
    return out
  }

  function patchScore(a,b,size){
    // Compare only the central oval-ish face area; ignore corners/background.
    let sum=0,count=0
    const cx=(size-1)/2,cy=(size-1)/2
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){
      const nx=(x-cx)/(size*.46),ny=(y-cy)/(size*.50)
      if(nx*nx+ny*ny>1)continue
      const i=y*size+x,d=a[i]-b[i]
      sum+=d*d;count++
    }
    return count?sum/count:Infinity
  }

  function estimateResidual(baseImg,curImg,baseScan,curScan){
    try{
      const bb=bbox(baseScan),cb=bbox(curScan)
      if(!bb||!cb)return null
      const size=56
      const baseCanvas=document.createElement('canvas'),work=document.createElement('canvas')
      baseCanvas.width=baseCanvas.height=work.width=work.height=size
      const bctx=baseCanvas.getContext('2d',{willReadFrequently:true})
      const wctx=work.getContext('2d',{willReadFrequently:true})
      drawFacePatch(bctx,baseImg,bb,size,null)
      const baseGray=grayscaleNormalized(bctx.getImageData(0,0,size,size).data)

      let best={score:Infinity,dx:0,dy:0,scale:1,angle:0}
      const shifts=[-3,0,3]
      const scales=[.97,1,1.03]
      const angles=[-4,0,4]
      for(const angle of angles)for(const scale of scales)for(const dx of shifts)for(const dy of shifts){
        drawFacePatch(wctx,curImg,cb,size,{angle,scale,dx,dy})
        const curGray=grayscaleNormalized(wctx.getImageData(0,0,size,size).data)
        const score=patchScore(baseGray,curGray,size)
        if(score<best.score)best={score,dx,dy,scale,angle}
      }

      // Poor residual matches should not distort the image. Geometry-only fallback.
      if(!Number.isFinite(best.score)||best.score>1.55)return null
      return best
    }catch(_e){return null}
  }

  function registerPair(frame,baseImg,curImg,baseScan,curScan){
    const run=()=>{
      const bt=geometryTransform(baseImg,baseScan,frame)
      const ct=geometryTransform(curImg,curScan,frame)
      if(!bt||!ct)return
      applyTransform(baseImg,bt,null)
      const residual=estimateResidual(baseImg,curImg,baseScan,curScan)
      let screenResidual=null
      if(residual){
        // Convert low-resolution patch offsets into final display-space offsets.
        screenResidual={
          dx:residual.dx/56*(frame.clientWidth*.48),
          dy:residual.dy/56*(frame.clientHeight*.64),
          scale:residual.scale,
          angle:residual.angle,
        }
      }
      applyTransform(curImg,ct,screenResidual)
      frame.dataset.registrationMode=residual?'geometry+residual':'geometry'
    }
    if(baseImg.complete&&curImg.complete)run()
    else{
      let loaded=0
      const ready=()=>{loaded++;if(loaded>=2)run()}
      baseImg.complete?ready():baseImg.addEventListener('load',ready,{once:true})
      curImg.complete?ready():curImg.addEventListener('load',ready,{once:true})
    }
    setTimeout(run,80)
  }

  function enhanceComparison(){
    const root=document.querySelector('#progressRoot'),rows=comparable()
    if(!root||rows.length<2)return
    const frame=root.querySelector('.pjCompareFrame')
    if(!frame)return
    const base=rows[rows.length-1],cur=rows[0]
    const baseImg=frame.querySelector('.pjCompareBase')
    const curImg=frame.querySelector('.pjCompareReveal img')
    if(!baseImg||!curImg)return

    frame.classList.add('v1592Registered')
    registerPair(frame,baseImg,curImg,base,cur)

    const note=root.querySelector('.pjCompareNote')
    if(note)note.textContent='Photos are normalized to the same facial geometry, with a small residual alignment when the image pattern is stable. Pose, expression and perspective can still create differences.'
  }

  function enhance(){
    scheduled=false
    document.documentElement.dataset.visualRegistrationVersion=VERSION
    enhanceComparison()
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(enhance)}
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true})
  document.addEventListener('click',e=>{if(e.target.closest('[data-tab]'))setTimeout(schedule,40)})
  window.addEventListener('resize',schedule)
  setTimeout(enhance,0)
})()
