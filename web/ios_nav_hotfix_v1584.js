// V1.5.8.4 — iOS bottom navigation hotfix.
// Presentation only. No measurement, capture protocol, study access, or researcher changes.
(function(){
  const VERSION='1.5.8.4'
  const isPhone=()=>window.matchMedia('(max-width: 820px)').matches
  const labels={home:'Today',progress:'Progress',scan:'+ Scan',routine:'Routine',journey:'Journey'}
  const order=['home','progress','scan','routine','journey']

  function activeTab(){return document.querySelector('main>.view.active')?.id||'home'}
  function buildNav(){
    if(!isPhone())return
    let nav=document.querySelector('#mobileBottomNavV1584')
    if(!nav){
      nav=document.createElement('nav')
      nav.id='mobileBottomNavV1584'
      nav.setAttribute('aria-label','Primary navigation')
      nav.innerHTML=order.map(tab=>`<button type="button" data-mobile-tab="${tab}" aria-label="${tab==='scan'?'Take a skin scan':labels[tab]}">${labels[tab]}</button>`).join('')
      document.body.appendChild(nav)
      nav.addEventListener('click',event=>{
        const button=event.target.closest('[data-mobile-tab]')
        if(!button)return
        const tab=button.dataset.mobileTab
        if(typeof setTab==='function') setTab(tab)
        syncActive()
      })
    }
    syncActive()
  }
  function syncActive(){
    const tab=activeTab()
    document.querySelectorAll('#mobileBottomNavV1584 [data-mobile-tab]').forEach(button=>button.classList.toggle('active',button.dataset.mobileTab===tab))
  }
  function enhance(){
    document.body.classList.toggle('mobileV1584',isPhone())
    document.documentElement.dataset.iosNavHotfix=VERSION
    if(isPhone())buildNav()
    else document.querySelector('#mobileBottomNavV1584')?.remove()
    syncActive()
  }

  if(typeof setTab==='function'){
    const baseSetTab=setTab
    setTab=function(tab){
      baseSetTab(tab)
      syncActive()
    }
  }

  document.addEventListener('click',event=>{
    if(event.target.closest('[data-tab],[data-go]'))setTimeout(syncActive,0)
  })
  window.addEventListener('resize',enhance)
  new MutationObserver(()=>requestAnimationFrame(syncActive)).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class']})
  enhance()
})()
