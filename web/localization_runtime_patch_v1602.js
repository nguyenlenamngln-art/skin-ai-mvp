// V1.6.0.2 — localization race + compound status compatibility patch
// Presentation only. Keeps generated status phrases synchronized with the selected locale.
(function(){
  const VERSION='1.6.0.2'
  const state=new WeakMap()
  let scheduled=false

  const EN_TO_VI={
    '↑ Higher':'↑ Cao hơn',
    '↓ Lower':'↓ Thấp hơn',
    '→ Stable':'→ Ổn định',
    '— No comparison':'— Chưa có so sánh',
    '↑ Higher from baseline':'↑ Cao hơn so với mốc ban đầu',
    '↓ Lower from baseline':'↓ Thấp hơn so với mốc ban đầu',
    '→ Stable from baseline':'→ Ổn định so với mốc ban đầu'
  }
  const VI_TO_EN=Object.fromEntries(Object.entries(EN_TO_VI).map(([en,vi])=>[vi,en]))

  function locale(){
    try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}
  }
  function canonical(text){return VI_TO_EN[text]||text}
  function target(en){return locale()==='vi'?(EN_TO_VI[en]||en):en}

  function translateNode(node){
    if(node.nodeType!==Node.TEXT_NODE)return
    const parent=node.parentElement
    if(!parent||['SCRIPT','STYLE','TEXTAREA'].includes(parent.tagName))return
    const current=node.data
    const leading=current.match(/^\s*/)?.[0]||''
    const trailing=current.match(/\s*$/)?.[0]||''
    const core=current.trim()
    if(!core)return
    let slot=state.get(node)
    if(!slot){slot={en:canonical(core),last:null};state.set(node,slot)}
    else if(core!==slot.last){
      const expected=target(slot.en)
      if(core!==expected)slot.en=canonical(core)
    }
    if(!EN_TO_VI[slot.en])return
    const translated=target(slot.en)
    slot.last=translated
    const next=`${leading}${translated}${trailing}`
    if(current!==next)node.data=next
  }

  function apply(){
    scheduled=false
    const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT)
    let node
    while((node=walker.nextNode()))translateNode(node)
    document.documentElement.dataset.localizationPatchVersion=VERSION
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(apply)}

  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true,characterData:true})
  window.addEventListener('skin-ai:locale-change',schedule)
  document.addEventListener('click',e=>{if(e.target.closest('[data-tab],[data-go],[data-result-view]'))setTimeout(schedule,0)})
  setTimeout(schedule,0)
})()
