// V1.7.7 — Session resume & recovery.
(function(){
  const VERSION='1.7.7'
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const tr=(en,vi)=>locale()==='vi'?vi:en
  let resumable=null
  let originalShots=null

  function root(){return document.querySelector('#dermV171')}

  function ensureCard(){
    const r=root();if(!r)return null
    let card=document.querySelector('#dermResumeCard')
    if(card)return card
    card=document.createElement('div');card.id='dermResumeCard';card.className='card dermResumeCard';card.hidden=true
    card.innerHTML=`<div><span class="eyebrow">${tr('INCOMPLETE SCAN','LẦN QUÉT CHƯA HOÀN TẤT')}</span><h3>${tr('Continue where you left off','Tiếp tục từ vị trí đang dở')}</h3><p id="dermResumeCopy"></p></div><div class="dermResumeActions"><button type="button" class="primary" id="dermResumeButton">${tr('Resume scan','Tiếp tục quét')}</button><button type="button" class="secondaryMini" id="dermDismissResume">${tr('Not now','Để sau')}</button></div>`
    const intro=r.querySelector('.dermIntroCard');intro?.insertAdjacentElement('afterend',card)
    card.querySelector('#dermResumeButton').onclick=resume
    card.querySelector('#dermDismissResume').onclick=()=>{card.hidden=true}
    return card
  }

  function regionLabel(code){const item=window.skinDermatoscopeCapture?.regions?.[code];return item?(locale()==='vi'?item.vi:item.en):code}
  function subLabel(code){const map={upper:['Upper','Phía trên'],middle:['Middle','Ở giữa'],lower:['Lower','Phía dưới'],center:['Center','Chính giữa'],left:['Left','Bên trái'],right:['Right','Bên phải'],custom:['Selected area','Vùng đã chọn']};const pair=map[code]||[code,code];return tr(pair[0],pair[1])}

  async function check(){
    try{
      const r=await fetch('/v1/dermatoscope/sessions/resumable/latest?subject_key=my_profile&simulator=true',{cache:'no-store'})
      if(!r.ok)return
      const data=await r.json();if(!data?.session||!data?.next_unresolved)return
      resumable=data
      const card=ensureCard();if(!card)return
      const next=data.next_unresolved
      card.querySelector('#dermResumeCopy').textContent=tr(
        `${regionLabel(next.region)} · ${subLabel(next.subregion)} is the next unfinished position. Accepted positions will not be captured again.`,
        `${regionLabel(next.region)} · ${subLabel(next.subregion)} là vị trí tiếp theo chưa hoàn tất. Các vị trí đã đạt sẽ không được chụp lại.`
      )
      card.hidden=false
    }catch(_e){}
  }

  async function resume(){
    if(!resumable?.session)return
    const id=resumable.session.id
    try{
      const r=await fetch(`/v1/dermatoscope/sessions/${encodeURIComponent(id)}/resume`,{method:'POST',cache:'no-store'})
      if(!r.ok)throw new Error('resume')
      const data=await r.json(),session=data.session,next=data.next_unresolved
      const capture=window.skinDermatoscopeCapture
      const region=session.region
      const all=capture?.regions?.[region]?.shots
      if(!all||!Array.isArray(all))throw new Error('capture state')
      originalShots=[...all]
      const pending=originalShots.filter(sub=>{
        const s=session.positions?.[`${region}/${sub}`]?.status
        return s!=='accepted'&&s!=='skipped'
      })
      if(!pending.length)throw new Error('nothing to resume')
      capture.regions[region].shots=pending
      document.documentElement.dataset.dermatoscopeResumeAdopting='true'
      root()?.querySelector(`[data-derm-region="${region}"]`)?.click()
      delete document.documentElement.dataset.dermatoscopeResumeAdopting
      await window.skinDermatoscopeSession?.adoptSession?.(session)
      const button=document.querySelector('#dermStart')
      if(button)button.textContent=tr('Resume scan','Tiếp tục quét')
      const card=document.querySelector('#dermResumeCard');if(card)card.hidden=true
      document.documentElement.dataset.dermatoscopeResumedSession=id
    }catch(_e){
      const card=ensureCard();if(card){card.hidden=false;card.querySelector('#dermResumeCopy').textContent=tr('This session could not be resumed. You can start a new scan instead.','Không thể tiếp tục lần quét này. Bạn có thể bắt đầu một lần quét mới.')}
    }
  }

  function restoreShots(){
    if(!originalShots||!resumable?.session?.region)return
    const r=resumable.session.region
    if(window.skinDermatoscopeCapture?.regions?.[r])window.skinDermatoscopeCapture.regions[r].shots=[...originalShots]
    originalShots=null
  }

  function install(){
    setTimeout(check,150)
    document.addEventListener('click',event=>{if(event.target.closest?.('#dermAgain,#dermCancel'))restoreShots()})
    window.addEventListener('skin-ai:locale-change',()=>setTimeout(()=>{const card=document.querySelector('#dermResumeCard');if(card)card.remove();check()},0))
    document.documentElement.dataset.dermatoscopeResumeVersion=VERSION
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install()
  window.skinDermatoscopeResume={version:VERSION,check,resume,restoreShots}
})()
