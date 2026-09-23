// RGB V1.5.6 Tester Study Mode
// Orchestration-only layer. Measurement remains RGB engine V1.5.2 / Capture Protocol V1.4.
(function(){
  const STUDY_MODE_VERSION='1.5.6'
  const NOTICE_VERSION='1.0'
  const PROFILE_PREFIX='STUDY-'
  const STORAGE_TESTER='skin_ai_study_tester_v156'
  const STORAGE_ACK='skin_ai_study_notice_v156'
  const ID_RE=/^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$/
  let studyActive=false
  let studyTesterId=localStorage.getItem(STORAGE_TESTER)||''

  function profileName(id){ return `${PROFILE_PREFIX}${id}` }
  function studyAcknowledged(){ return localStorage.getItem(STORAGE_ACK)===NOTICE_VERSION }
  function validTesterId(value){ return ID_RE.test(String(value||'').trim()) }
  function studySubject(){ return trackingSubjects.find(x=>x.display_name===profileName(studyTesterId))||null }

  function buildStudyUI(){
    const capture=document.querySelector('.capture')
    if(!capture || document.querySelector('#studyModeV156')) return
    const box=document.createElement('section')
    box.id='studyModeV156'
    box.className='studyModeV156'
    box.innerHTML=`
      <div class="studyHeader">
        <div><span class="eyebrow">TESTER STUDY MODE · V${STUDY_MODE_VERSION}</span><b>Repeatable RGB capture study</b></div>
        <label class="studyToggle"><input id="studyEnabled" type="checkbox"><span>Study mode</span></label>
      </div>
      <div id="studySetup" class="studySetup hidden">
        <div class="studyNotice">
          <b>Study notice</b>
          <p>This research beta records your pseudonymous tester code, scan-session ID, capture time, image, and RGB analysis so repeatability can be evaluated. It is not a medical or diagnostic assessment.</p>
          <p>Use only the tester code assigned to you. Do not enter your name, email address, phone number, or other identifying information here.</p>
          <label class="studyAck"><input id="studyAck" type="checkbox"> I have read this study notice and agree to submit this test capture.</label>
          <small>This acknowledgment supports this engineering beta workflow; it is not a substitute for any formal research consent process that may be required.</small>
        </div>
        <label class="studyField">Tester code<input id="studyTesterId" type="text" maxlength="32" autocomplete="off" spellcheck="false" placeholder="P001"></label>
        <div class="studyActions"><button id="studyStart" type="button" class="primary">Start study session</button><button id="studyExit" type="button" class="secondaryMini">Exit study mode</button></div>
        <div id="studyStatus" class="studyStatus"></div>
      </div>`
    const modes=capture.querySelector('.modes')
    modes.insertAdjacentElement('afterend',box)
    bindStudyUI()
  }

  function bindStudyUI(){
    const enabled=document.querySelector('#studyEnabled')
    const tester=document.querySelector('#studyTesterId')
    const ack=document.querySelector('#studyAck')
    if(tester) tester.value=studyTesterId
    if(ack) ack.checked=studyAcknowledged()
    enabled?.addEventListener('change',()=>{
      if(enabled.checked) enterStudySetup()
      else leaveStudyMode(false)
    })
    ack?.addEventListener('change',()=>{
      if(ack.checked) localStorage.setItem(STORAGE_ACK,NOTICE_VERSION)
      else localStorage.removeItem(STORAGE_ACK)
    })
    document.querySelector('#studyStart')?.addEventListener('click',startStudySession)
    document.querySelector('#studyExit')?.addEventListener('click',()=>leaveStudyMode(true))
  }

  function enterStudySetup(){
    studyActive=true
    document.querySelector('#studySetup')?.classList.remove('hidden')
    document.body.classList.add('studyModeActiveV156')
    scanMode='rgb'
    applyModeUI()
    renderStudyStatus()
  }

  function leaveStudyMode(clearStored){
    studyActive=false
    document.querySelector('#studyEnabled') && (document.querySelector('#studyEnabled').checked=false)
    document.querySelector('#studySetup')?.classList.add('hidden')
    document.body.classList.remove('studyModeActiveV156')
    if(clearStored){
      localStorage.removeItem(STORAGE_TESTER)
      localStorage.removeItem(STORAGE_ACK)
      studyTesterId=''
      if(document.querySelector('#studyTesterId')) document.querySelector('#studyTesterId').value=''
      if(document.querySelector('#studyAck')) document.querySelector('#studyAck').checked=false
    }
    renderStudyStatus()
  }

  async function ensureStudySubject(testerId){
    const wanted=profileName(testerId)
    let subject=trackingSubjects.find(x=>x.display_name===wanted)
    if(subject) return subject
    subject=await api('/v1/subjects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:wanted})})
    trackingSubjects=await api('/v1/subjects')
    return subject
  }

  async function startStudySession(){
    const testerId=String(document.querySelector('#studyTesterId')?.value||'').trim()
    const ack=!!document.querySelector('#studyAck')?.checked
    if(!validTesterId(testerId)){
      showError("Enter a 2–32 character pseudonymous tester code using only letters, numbers, '-' or '_'.")
      return
    }
    if(!ack){ showError('Read and acknowledge the study notice before starting a study session.'); return }
    if(sessionIsActive()){
      const currentName=activeSession?.subject?.display_name||''
      if(currentName!==profileName(testerId)){
        showError('Finish the currently active guided session before switching study testers.')
        return
      }
      studyTesterId=testerId; studyActive=true; renderStudyStatus(); return
    }
    try{
      showError('')
      studyTesterId=testerId
      localStorage.setItem(STORAGE_TESTER,studyTesterId)
      localStorage.setItem(STORAGE_ACK,NOTICE_VERSION)
      const subject=await ensureStudySubject(studyTesterId)
      trackingSubjectId=subject.id
      trackingRegionCode='full_face'
      scanMode='rgb'
      populateTrackingControls()
      await startGuidedSession()
      renderStudyStatus()
    }catch(e){ showError(`Study setup: ${e.message}`) }
  }

  function renderStudyStatus(){
    const status=document.querySelector('#studyStatus')
    if(!status) return
    if(!studyActive){ status.innerHTML=''; return }
    const subject=studySubject()
    const isStudySession=!!activeSession && activeSession?.subject?.display_name===profileName(studyTesterId)
    if(sessionIsActive() && isStudySession){
      status.innerHTML=`<b>Study session active</b><span>Tester ${studyTesterId} · session ${activeSession.id}</span><small>Take one front-facing RGB capture below. The session ID is attached automatically.</small>`
    }else if(sessionIsComplete() && isStudySession){
      status.innerHTML=`<b>Study capture saved</b><span>Tester ${studyTesterId} · session ${activeSession.id}</span><small>Start another study session for a repeat capture on the same or a later visit.</small><button id="studyNextSession" type="button" class="primary">Start another study session</button>`
      document.querySelector('#studyNextSession')?.addEventListener('click',async()=>{
        clearCompletedSession()
        await startStudySession()
      })
    }else if(subject){
      status.innerHTML=`<b>Tester ${studyTesterId} ready</b><small>Start a study session to attach a unique session ID to the next RGB capture.</small>`
    }else{
      status.innerHTML='<small>Enter your assigned tester code and start a study session.</small>'
    }
    syncStudyControlState()
  }

  function syncStudyControlState(){
    if(!studyActive) return
    const tracking=document.querySelector('#trackingContext')
    if(tracking) tracking.classList.add('studyManagedTracking')
    document.querySelectorAll('[data-mode]').forEach(button=>{ button.disabled=true })
    const subject=document.querySelector('#scanSubjectSelect'), region=document.querySelector('#scanRegionSelect')
    if(subject) subject.disabled=true
    if(region) region.disabled=true
  }

  // Keep the study panel synchronized with guided-session completion/restoration.
  const renderSessionPanelStudyBase=renderSessionPanel
  renderSessionPanel=function(){ renderSessionPanelStudyBase(); renderStudyStatus() }
  const syncSessionTrackingStudyBase=syncSessionTracking
  syncSessionTracking=function(){ syncSessionTrackingStudyBase(); syncStudyControlState(); renderStudyStatus() }
  const applyModeStudyBase=applyModeUI
  applyModeUI=function(){
    applyModeStudyBase()
    if(studyActive && scanMode!=='rgb'){ scanMode='rgb'; applyModeStudyBase() }
    syncStudyControlState()
  }

  async function restoreStudyMode(){
    buildStudyUI()
    if(!studyTesterId || !studyAcknowledged()) return
    studyActive=true
    const enabled=document.querySelector('#studyEnabled')
    if(enabled) enabled.checked=true
    document.querySelector('#studySetup')?.classList.remove('hidden')
    document.body.classList.add('studyModeActiveV156')
    try{
      if(!trackingSubjects.length) trackingSubjects=await api('/v1/subjects')
      const subject=studySubject()
      if(subject){ trackingSubjectId=subject.id; trackingRegionCode='full_face' }
      scanMode='rgb'; applyModeUI(); populateTrackingControls(); renderStudyStatus()
    }catch(e){ showError(`Study restore: ${e.message}`) }
  }

  // Delay one tick so Tracking V1 and Session V1 can initialize first.
  setTimeout(restoreStudyMode,0)
})()
