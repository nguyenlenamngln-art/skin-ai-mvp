// V1.5.9.3 — Mobile Comparison Registration Patch
// Presentation only. RGB measurements remain V1.5.2 / Capture Protocol V1.4.
(function(){
  const VERSION='1.5.9.3'
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

  function anchoredCoverScale({anchorX,anchorY,targetX,targetY,nw,nh,cw,ch,pad}){
    const eps=1e-6
    const left=(targetX+pad)/Math.max(anchorX,eps)
    const right=(cw-targetX+pad)/Math.max(nw-anchorX,eps)
    const top=(targetY+pad)/Math.max(anchorY,eps)
    const bottom=(ch-targetY+pad)/Math.max(nh-anchorY,eps)
    return Math.max(left,right,top,bottom,cw/nw,ch/nh)
  }

  function canonicalTransform(img,scan,frame){
    const b=bbox(scan)
    if(!img||!b||!frame)return null
    const cw=frame.clientWidth,ch=frame.clientHeight,nw=img.naturalWidth,nh=img.naturalHeight
    if(!cw||!ch||!nw||!nh)return null

    // Both images are normalized into the same facial viewport.
    const targetFaceW=cw*.56
    const targetFaceH=ch*.62
    const faceScale=Math.sqrt(
      Math.max(targetFaceW/b.w,1e-9)*Math.max(targetFaceH/b.h,1e-9)
    )

    // Anchor around the upper-mid face. This keeps eyes/nose more stable than
    // centering the whole photograph or the lower half of the face box.
    const anchorX=b.x+b.w*.50
    const anchorY=b.y+b.h*.40
    const targetX=cw*.50
    const targetY=ch*.42

    // Cover is computed AFTER anchoring. This is the V1.5.9.3 fix: the earlier
    // code only checked raw image cover before translation, which could expose
    // the pale frame background at the top/bottom after face centering.
    const pad=Math.max(10,Math.min(cw,ch)*.035)
    const coverScale=anchoredCoverScale({anchorX,anchorY,targetX,targetY,nw,nh,cw,ch,pad})
    const mobile=window.matchMedia('(max-width:820px)').matches
    const overscan=mobile?1.07:1.025
    const scale=Math.max(faceScale,coverScale)*overscan

    return {
      scale,
      left:targetX-anchorX*scale,
      top:targetY-anchorY*scale,
      anchorX,anchorY,targetX,targetY,nw,nh,cw,ch,
    }
  }

  function applyTransform(img,t,residual){
    if(!img||!t)return
    const mobile=window.matchMedia('(max-width:820px)').matches
    const maxDx=t.cw*.025,maxDy=t.ch*.022
    const r=residual||{dx:0,dy:0,scale:1,angle:0}
    const dx=Math.max(-maxDx,Math.min(maxDx,Number(r.dx)||0))
    const dy=Math.max(-maxDy,Math.min(maxDy,Number(r.dy)||0))
    // Never shrink the image after canonical cover. Small expansion is safe;
    // rotation is deliberately tighter on phones to avoid uncovering corners.
    const residualScale=Math.max(1,Math.min(1.025,Number(r.scale)||1))
    const angle=Math.max(mobile?-1.5:-2.5,Math.min(mobile?1.5:2.5,Number(r.angle)||0))

    img.style.position='absolute'
    img.style.width=`${t.nw*t.scale}px`
    img.style.height=`${t.nh*t.scale}px`
    img.style.maxWidth='none'
    img.style.maxHeight='none'
    img.style.left=`${t.left}px`
    img.style.top=`${t.top}px`
    img.style.transformOrigin=`${(t.anchorX/t.nw)*100}% ${(t.anchorY/t.nh)*100}%`
    img.style.transform=`translate(${dx}px,${dy}px) rotate(${angle}deg) scale(${residualScale})`
  }

  function drawFacePatch(ctx,img,b,size,transform){
    const marginX=.10*b.w,marginTop=.08*b.h
    const sx=b.x+marginX,sy=b.y+marginTop,sw=b.w-marginX*2,sh=b.h*.68
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
      const shifts=[-2,0,2],scales=[1,1.02],angles=[-2,0,2]
      for(const angle of angles)for(const scale of scales)for(const dx of shifts)for(const dy of shifts){
        drawFacePatch(wctx,curImg,cb,size,{angle,scale,dx,dy})
        const curGray=grayscaleNormalized(wctx.getImageData(0,0,size,size).data)
        const score=patchScore(baseGray,curGray,size)
        if(score<best.score)best={score,dx,dy,scale,angle}
      }
      if(!Number.isFinite(best.score)||best.score>1.50)return null
      return best
    }catch(_e){return null}
  }

  function registerPair(frame,baseImg,curImg,baseScan,curScan){
    const run=()=>{
      const bt=canonicalTransform(baseImg,baseScan,frame)
      const ct=canonicalTransform(curImg,curScan,frame)
      if(!bt||!ct)return
      applyTransform(baseImg,bt,null)
      const residual=estimateResidual(baseImg,curImg,baseScan,curScan)
      let screenResidual=null
      if(residual){
        screenResidual={
          dx:residual.dx/56*(frame.clientWidth*.56),
          dy:residual.dy/56*(frame.clientHeight*.62),
          scale:residual.scale,
          angle:residual.angle,
        }
      }
      applyTransform(curImg,ct,screenResidual)
      frame.dataset.registrationMode=residual?'shared-viewport+residual':'shared-viewport'
      frame.dataset.registrationVersion=VERSION
    }
    if(baseImg.complete&&curImg.complete)run()
    else{
      let loaded=0
      const ready=()=>{loaded++;if(loaded>=2)run()}
      baseImg.complete?ready():baseImg.addEventListener('load',ready,{once:true})
      curImg.complete?ready():curImg.addEventListener('load',ready,{once:true})
    }
    setTimeout(run,100)
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

    frame.classList.remove('v1592Registered')
    frame.classList.add('v1593Registered')
    registerPair(frame,baseImg,curImg,base,cur)

    const note=root.querySelector('.pjCompareNote')
    if(note)note.textContent='Both photos use one shared face-centered viewport for visual comparison. Small residual alignment is applied only when stable; pose, expression and perspective can still differ.'
  }

  function enhance(){
    scheduled=false
    document.documentElement.dataset.mobileComparisonRegistrationVersion=VERSION
    enhanceComparison()
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(enhance)}
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true})
  document.addEventListener('click',e=>{if(e.target.closest('[data-tab]'))setTimeout(schedule,40)})
  window.addEventListener('resize',schedule)
  setTimeout(enhance,0)
})()
