// RGB V1.5.7 Tester Study Mode + access control
// Access/orchestration only. Measurement remains RGB engine V1.5.2 / Capture Protocol V1.4.
(function(){
  const STUDY_MODE_VERSION='1.5.7'
  const NOTICE_VERSION='1.0'
  const STORAGE_TESTER='skin_ai_study_tester_v157'
  const STORAGE_ACK='skin_ai_study_notice_v157'
  const ID_RE=/^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$/
  let studyActive=false
  let studyAuthenticated=false
  let studyTesterId=localStorage.getItem(STORAGE_TESTER)||''
  let studySubjectRecord=null

  function validTesterId(value){ return ID_RE.test(String(value||'').trim()) }
  function studyAcknowledged(){ return localStorage.getItem(STORAGE_ACK)===NOTICE_VERSION }

  // Scope normal app refresh/history reads to the authenticated tester.
  const apiStudyBase=api
  api=async function(path,options={}){
    if(studyActive && studyAuthenticated && (!options.method || String(options.method).toUpperCase()==='GET')){
      if(path.startsWith('/v1/scans')) path=path.replace('/v1/scans','/v1/study/scans')
      else if(path.startsWith('/v1/trends')) path=path.replace('/v1/trends','/v1/study/trends')
      else if(path==='/v1/subjects') path='/v1/study/subjects'
      else if(path.startsWith('/v1/sessions?')) path=path.replace('/v1/sessions','/v1/study/sessions')
    }
    return apiStudyBase(path,options)
  }

  function buildStudyUI(){
    const capture=document.querySelector('.capture')
    if(!capture || document.querySelector('#studyModeV157')) return
    const box=document.createElement('section')
    box.id='studyModeV157'
    box.className='studyModeV156 studyModeV157'
    box.innerHTML=`
      <div class="studyHeader">
        <div><span class="eyebrow">TESTER STUDY MODE · V${STUDY_MODE_VERSION}</span><b>Repeatable RGB capture study</b></div>
        <label class="studyToggle"><input id="studyEnabled" type="checkbox"><span>Study mode</span></label>
      </div>
      <div id="studySetup" class="studySetup hidden">
        <div class="studyNotice">
          <b>Study notice</b>
          <p>This research beta records your pseudonymous tester code, scan-session ID, capture time, image, and RGB analysis so repeatability can be evaluated. It is not a medical or diagnostic assessment.</p>
          <p>Use only the tester ID and access code provided by the study organizer. Do not enter your name, email address, phone number, or other identifying information.</p>
          <label class="studyAck"><input id="studyAck" type="checkbox"> I have read this study notice and agree to submit this test capture.</label>
          <small>This acknowledgment supports this engineering beta workflow; it is not a substitute for any formal research consent process that may be required.</small>
        </div>
        <label class="studyField">Tester ID<input id="studyTesterId" type="text" maxlength="32" autocomplete="off" spellcheck="false" placeholder="P001"></label>
        <label class="studyField">Access code<input id="studyAccessCode" type="password" maxlength="80" autocomplete="one-time-code" placeholder="Provided by study organizer"></label>
        <div class="studyActions"><button id="studyStart" type="button" class="primary">Sign in & start session</button><button id="studyExit" type="button" class="secondaryMini">Exit study mode</button></div>
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
    enabled?.addEventListener('change',()=>enabled.checked?enterStudySetup():leaveStudyMode(false))
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
    document.body.classList.add('studyModeActiveV157')
    scanMode='rgb'
    setTab('scan')
    applyModeUI()
    renderStudyStatus()
  }

  async function leaveStudyMode(clearStored){
    if(clearStored){
      try{await apiStudyBase('/v1/study/logout',{method:'POST'})}catch(_e){}
    }
    studyActive=false
    studyAuthenticated=false
    studySubjectRecord=null
    document.querySelector('#studyEnabled') && (document.querySelector('#studyEnabled').checked=false)
    document.querySelector('#studySetup')?.classList.add('hidden')
    document.body.classList.remove('studyModeActiveV157')
    document.querySelector('#trackingContext')?.classList.remove('studyManagedTracking')
    if(clearStored){
      localStorage.removeItem(STORAGE_TESTER)
      localStorage.removeItem(STORAGE_ACK)
      studyTesterId=''
      if(document.querySelector('#studyTesterId')) document.querySelector('#studyTesterId').value=''
      if(document.querySelector('#studyAccessCode')) document.querySelector('#studyAccessCode').value=''
      if(document.querySelector('#studyAck')) document.querySelector('#studyAck').checked=false
    }
    renderStudyStatus()
  }

  async function authenticateStudy(testerId,accessCode){
    const response=await apiStudyBase('/v1/study/login',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({tester_id:testerId,access_code:accessCode})
    })
    studyTesterId=response.tester_id
    studySubjectRecord=response.subject
    studyAuthenticated=true
    studyActive=true
    localStorage.setItem(STORAGE_TESTER,studyTesterId)
    return response
  }

  async function startStudySession(){
    const testerId=String(document.querySelector('#studyTesterId')?.value||'').trim()
    const accessCode=String(document.querySelector('#studyAccessCode')?.value||'')
    const ack=!!document.querySelector('#studyAck')?.checked
    if(!validTesterId(testerId)){
      showError("Enter the assigned tester ID (2–32 letters, numbers, '-' or '_').")
      return
    }
    if(!ack){showError('Read and acknowledge the study notice before starting a study session.');return}
    try{
      showError('')
      if(!studyAuthenticated || testerId!==studyTesterId){
        if(!accessCode){showError('Enter the access code provided by the study organizer.');return}
        await authenticateStudy(testerId,accessCode)
      }
      localStorage.setItem(STORAGE_ACK,NOTICE_VERSION)
      trackingSubjects=studySubjectRecord?[studySubjectRecord]:await api('/v1/subjects')
      trackingSubjectId=studySubjectRecord?.id||''
      trackingRegionCode='full_face'
      scanMode='rgb'
      setTab('scan')
      populateTrackingControls()
      if(sessionIsActive()){
        if(activeSession?.subject_id!==trackingSubjectId){showError('Finish the active session before starting another tester session.');return}
      }else{
        if(sessionIsComplete()) clearCompletedSession()
        await startGuidedSession()
      }
      if(document.querySelector('#studyAccessCode')) document.querySelector('#studyAccessCode').value=''
      await refresh()
      renderStudyStatus()
    }catch(e){showError(`Study access: ${e.message}`)}
  }

  function renderStudyStatus(){
    const status=document.querySelector('#studyStatus')
    if(!status)return
    if(!studyActive){status.innerHTML='';return}
    if(!studyAuthenticated){status.innerHTML='<small>Enter the assigned tester ID and access code to begin.</small>';syncStudyControlState();return}
    const isStudySession=!!activeSession && activeSession?.subject_id===studySubjectRecord?.id
    if(sessionIsActive() && isStudySession){
      status.innerHTML=`<b>Study session active</b><span>Tester ${studyTesterId} · session ${activeSession.id}</span><small>Take one front-facing RGB capture below. Only your study records are available in this signed-in session.</small>`
    }else if(sessionIsComplete() && isStudySession){
      status.innerHTML=`<b>Study capture saved</b><span>Tester ${studyTesterId} · session ${activeSession.id}</span><small>Your result is available above. Start another session for a repeat capture.</small><button id="studyNextSession" type="button" class="primary">Start another study session</button>`
      document.querySelector('#studyNextSession')?.addEventListener('click',async()=>{clearCompletedSession();await startStudySession()})
    }else{
      status.innerHTML=`<b>Tester ${studyTesterId} signed in</b><small>Start a study session to attach a unique session ID to the next RGB capture.</small><button id="studyNextSession" type="button" class="primary">Start study session</button>`
      document.querySelector('#studyNextSession')?.addEventListener('click',startStudySession)
    }
    syncStudyControlState()
  }

  function syncStudyControlState(){
    if(!studyActive)return
    document.querySelector('#trackingContext')?.classList.add('studyManagedTracking')
    document.querySelectorAll('[data-mode]').forEach(button=>{button.disabled=true})
    const subject=document.querySelector('#scanSubjectSelect'),region=document.querySelector('#scanRegionSelect')
    if(subject)subject.disabled=true
    if(region)region.disabled=true
  }

  const renderSessionPanelStudyBase=renderSessionPanel
  renderSessionPanel=function(){renderSessionPanelStudyBase();renderStudyStatus()}
  const syncSessionTrackingStudyBase=syncSessionTracking
  syncSessionTracking=function(){syncSessionTrackingStudyBase();syncStudyControlState();renderStudyStatus()}
  const applyModeStudyBase=applyModeUI
  applyModeUI=function(){
    applyModeStudyBase()
    if(studyActive && scanMode!=='rgb'){scanMode='rgb';applyModeStudyBase()}
    syncStudyControlState()
  }

  async function restoreStudyMode(){
    buildStudyUI()
    try{
      const status=await apiStudyBase('/v1/study/status')
      if(!status?.authenticated)return
      studyActive=true;studyAuthenticated=true;studyTesterId=status.tester_id||studyTesterId;studySubjectRecord=status.subject||null
      localStorage.setItem(STORAGE_TESTER,studyTesterId)
      const enabled=document.querySelector('#studyEnabled');if(enabled)enabled.checked=true
      const tester=document.querySelector('#studyTesterId');if(tester)tester.value=studyTesterId
      document.querySelector('#studySetup')?.classList.remove('hidden')
      document.body.classList.add('studyModeActiveV157')
      trackingSubjects=studySubjectRecord?[studySubjectRecord]:[]
      trackingSubjectId=studySubjectRecord?.id||''
      trackingRegionCode='full_face';scanMode='rgb';setTab('scan');applyModeUI();populateTrackingControls()
      await refresh();renderStudyStatus()
    }catch(_e){/* stay signed out */}
  }

  setTimeout(restoreStudyMode,0)
})()
