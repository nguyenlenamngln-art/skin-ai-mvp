// V1.7.0.0 — Dermatoscope transition foundation
// Keeps Phone RGB code and historical data intact while retiring new consumer RGB capture.
(function(){
  const VERSION='1.7.0.0'
  const params=new URLSearchParams(window.location.search)
  const researchMode=params.get('research')==='1'||params.get('developer')==='1'
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const pick=(en,vi)=>locale()==='vi'?vi:en

  function legacyRgbButton(){return document.querySelector('[data-mode="rgb"]')}
  function setLegacyButtonVisibility(){
    const button=legacyRgbButton()
    if(!button)return
    button.hidden=!researchMode
    button.setAttribute('aria-hidden',researchMode?'false':'true')
    button.dataset.legacyResearchOnly='true'
    if(researchMode)button.title='Research / developer capture only'
  }

  function annotateLegacyHistory(){
    if(typeof scans==='undefined')return
    document.querySelectorAll('.historyRow').forEach(row=>{
      const scan=scans.find(item=>item.id===row.dataset.id)
      if(scan?.modality!=='rgb')return
      row.dataset.legacyRgb='true'
      const meta=row.querySelector('div span')
      if(meta)meta.textContent=`${pick('Legacy Phone RGB','Phone RGB cũ')} · ${scan.source_name||'scan'}`
      row.title=pick('Historical Phone RGB scan — view only','Lần quét Phone RGB cũ — chỉ xem')
    })
  }

  function updateLegacyReadOnlyView(){
    const capture=document.querySelector('#scan .capture')
    const grid=document.querySelector('#scan .scan-grid')
    const result=document.querySelector('#scan .result')
    if(!capture||!result)return
    const legacyView=!researchMode&&typeof scanMode!=='undefined'&&scanMode==='rgb'
    capture.classList.toggle('hidden',legacyView)
    if(grid)grid.style.gridTemplateColumns=legacyView?'1fr':''
    let note=document.querySelector('#legacyRgbReadOnly')
    if(legacyView){
      if(!note){
        note=document.createElement('div')
        note.id='legacyRgbReadOnly'
        note.className='scienceNote'
        result.insertBefore(note,document.querySelector('#resultBody'))
      }
      note.textContent=pick(
        'Legacy Phone RGB · read only. This historical scan is preserved for reference and is not part of the new dermatoscope measurement series.',
        'Phone RGB cũ · chỉ xem. Lần quét lịch sử này được giữ lại để tham chiếu và không thuộc chuỗi đo bằng dermatoscope mới.'
      )
    }else if(note){note.remove()}
  }

  function updateEmptyHomeCopy(){
    if(typeof latest!=='undefined'&&!latest){
      const copy=document.querySelector('#latestCopy')
      if(copy)copy.textContent=pick('Start a scan to create your baseline.','Bắt đầu một lần quét để tạo mốc ban đầu.')
    }
  }

  const baseRenderHistory=typeof renderHistory==='function'?renderHistory:null
  if(baseRenderHistory){
    renderHistory=function(){
      baseRenderHistory()
      annotateLegacyHistory()
    }
    window.renderHistory=renderHistory
  }

  const baseApplyModeUI=typeof applyModeUI==='function'?applyModeUI:null
  if(baseApplyModeUI){
    applyModeUI=function(){
      baseApplyModeUI()
      setLegacyButtonVisibility()
      updateLegacyReadOnlyView()
    }
    window.applyModeUI=applyModeUI
  }

  const baseRender=typeof render==='function'?render:null
  if(baseRender){
    render=function(){
      baseRender()
      updateEmptyHomeCopy()
      annotateLegacyHistory()
      updateLegacyReadOnlyView()
    }
    window.render=render
  }

  function returnConsumerToAvailableScan(){
    if(researchMode||typeof scanMode==='undefined'||scanMode!=='rgb')return
    scanMode='uv'
    if(typeof scansOf==='function')latest=scansOf('uv')[0]||null
    if(typeof rejectedAttempt!=='undefined')rejectedAttempt=null
    if(typeof resultView!=='undefined')resultView='combined'
    try{if(typeof showError==='function')showError('')}catch(_e){}
    try{if(typeof applyModeUI==='function')applyModeUI()}catch(_e){}
  }

  document.querySelectorAll('[data-tab="scan"],[data-go="scan"]').forEach(control=>{
    control.addEventListener('click',()=>setTimeout(returnConsumerToAvailableScan,0))
  })

  function refreshTransition(){
    setLegacyButtonVisibility()
    updateEmptyHomeCopy()
    annotateLegacyHistory()
    updateLegacyReadOnlyView()
    document.documentElement.dataset.captureTransitionVersion=VERSION
    document.documentElement.dataset.researchCaptureMode=researchMode?'true':'false'
  }

  function loadGuidedDermatoscopeCapture(){
    if(!document.querySelector('link[data-derm-v171]')){
      const link=document.createElement('link')
      link.rel='stylesheet';link.href='/app/dermatoscope_guided_capture_v171.css?v=171';link.dataset.dermV171='1';document.head.appendChild(link)
    }
    if(!document.querySelector('script[data-derm-v171]')){
      const script=document.createElement('script')
      script.src='/app/dermatoscope_guided_capture_v171.js?v=171';script.defer=true;script.dataset.dermV171='1';document.body.appendChild(script)
    }
  }

  window.addEventListener('skin-ai:locale-change',()=>setTimeout(refreshTransition,0))
  window.skinDermatoscopeTransition={version:VERSION,researchMode,refresh:refreshTransition}
  setTimeout(refreshTransition,0)
  loadGuidedDermatoscopeCapture()
})()