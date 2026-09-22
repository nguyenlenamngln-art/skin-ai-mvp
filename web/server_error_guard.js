// Server Error Guard V1
// A transport/backend failure is not evidence that capture quality was poor.
(function(){
  if(typeof renderRejectedAttempt!=='function') return
  const baseRenderRejectedAttempt=renderRejectedAttempt
  renderRejectedAttempt=function(){
    const attempt=typeof rejectedAttempt!=='undefined'?rejectedAttempt:null
    if(attempt && Number(attempt.status)>=500){
      const body=document.querySelector('#resultBody')
      const date=document.querySelector('#resultDate')
      const badge=document.querySelector('#compareBadge')
      if(date) date.textContent='Current attempt'
      if(badge){
        badge.textContent='Server error'
        badge.className='compareBadge warn'
      }
      if(body){
        body.className=''
        body.innerHTML=`
          <div class="scienceNote"><b>Analysis could not run — nothing was saved.</b> ${attempt.message||'The server returned an internal error.'}</div>
          <div class="analysisMetrics">
            ${typeof metric==='function'?metric('Status','Server error','not a capture-quality decision'):''}
            ${typeof metric==='function'?metric('HTTP status',String(attempt.status),'backend/runtime failure'):''}
          </div>
          <div class="scienceNote"><b>What this means</b><p>Your photo was not classified as poor quality. The analysis service failed before it could complete the quality check. Please retry after the service is fixed.</p></div>`
      }
      return
    }
    return baseRenderRejectedAttempt()
  }
})();
