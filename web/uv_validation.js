// UV input validation V1 UI layer.
const baseRenderRejectedAttemptUVV1 = renderRejectedAttempt
renderRejectedAttempt = function(){
  if(!rejectedAttempt || rejectedAttempt.mode!=='uv') return baseRenderRejectedAttemptUVV1()
  const body=$('#resultBody'), date=$('#resultDate'), badge=$('#compareBadge')
  const detail=(rejectedAttempt.detail && typeof rejectedAttempt.detail==='object')?rejectedAttempt.detail:{}
  const flags=Array.isArray(detail.validation_flags)?detail.validation_flags:[]
  const guidance=Array.isArray(detail.validation_guidance)?detail.validation_guidance:[]
  const score=Number.isFinite(detail.uv_input_validation_score)?`${detail.uv_input_validation_score}/100`:'Not measured'
  date.textContent='Current attempt'
  badge.textContent='UV input rejected'
  badge.className='compareBadge warn'
  body.className=''
  body.innerHTML=`
    <div class="scienceNote"><b>UV input rejected — analysis not run and image not saved.</b> ${detail.message||rejectedAttempt.message||'This image is not compatible with the current UV input profile.'}</div>
    <div class="analysisMetrics">
      ${metric('Status','Rejected','not added to History or UV trends')}
      ${metric('UV input check',score,detail.profile||'UVFD-like close-up profile')}
      ${metric('Issues',flags.length?flags.join(', '):'wrong input profile','pre-analysis validation')}
    </div>
    <div class="scienceNote"><b>What to do next</b>${guidance.length?`<ul style="margin:8px 0 0 18px;padding:0">${guidance.map(x=>`<li>${x}</li>`).join('')}</ul>`:'<p>Use a direct close-up UV-fluorescence capture from the supported workflow, or switch to Phone RGB for ordinary face photos.</p>'}</div>
    <div class="scienceNote"><b>Validator V${detail.validator_version||'1.0'} limitation.</b> This gate rejects obvious wrong-modality inputs. Passing it does not independently prove that an image was captured under UV illumination.</div>`
}

const baseRenderResultUVV1 = renderResult
renderResult = function(){
  if(rejectedAttempt && rejectedAttempt.mode==='uv'){renderRejectedAttempt();return}
  baseRenderResultUVV1()
  if(latest?.modality==='uv' && Number.isFinite(latest.metrics?.uv_input_validation_score)){
    const note=document.createElement('div')
    note.className='scienceNote'
    note.innerHTML=`<b>UV input validator V${latest.metrics.uv_input_validation_version||'1.0'}.</b> Input compatibility score ${latest.metrics.uv_input_validation_score}/100 for ${latest.metrics.uv_input_validation_profile||'the supported close-up profile'}. Passing this gate does not independently verify UV illumination.`
    $('#resultBody').appendChild(note)
  }
}
