// V1.7.2 — close-up baseline and per-position history.
(function(){
  const VERSION='1.7.2'
  const SUBJECT='my_profile'
  const root=()=>document.querySelector('#dermV171')
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const tr=(en,vi)=>locale()==='vi'?vi:en
  const regionLabel=(code)=>({forehead:['Forehead','Trán'],left_cheek:['Left cheek','Má trái'],right_cheek:['Right cheek','Má phải'],nose:['Nose','Mũi'],chin:['Chin','Cằm'],custom:['Custom area','Vùng tùy chọn']}[code]||[code,code])[locale()==='vi'?1:0]
  const subLabel=(code)=>({upper:['Upper','Phía trên'],middle:['Middle','Ở giữa'],lower:['Lower','Phía dưới'],center:['Center','Chính giữa'],left:['Left','Bên trái'],right:['Right','Bên phải'],custom:['Selected area','Vùng đã chọn']}[code]||[code,code])[locale()==='vi'?1:0]

  function ensureCard(){
    const host=root();if(!host)return null
    let card=host.querySelector('#dermHistoryV172')
    if(card)return card
    card=document.createElement('section')
    card.id='dermHistoryV172';card.className='card dermHistoryCard'
    card.innerHTML=`<div class="dermHistoryHead"><div><span class="eyebrow"></span><h3></h3><p></p></div><span class="dermHistoryBadge">V1.7.2</span></div><div class="dermHistoryBody"></div>`
    const intro=host.querySelector('.dermIntroCard')
    if(intro)intro.insertAdjacentElement('afterend',card);else host.prepend(card)
    return card
  }

  function copy(card){
    card.querySelector('.eyebrow').textContent=tr('YOUR CLOSE-UP HISTORY','LỊCH SỬ QUÉT CẬN CẢNH')
    card.querySelector('h3').textContent=tr('Baseline by skin position','Mốc ban đầu theo từng vị trí da')
    card.querySelector('p').textContent=tr(
      'The first accepted image for each position becomes that position’s baseline. Simulator history stays separate from future Skin AI Scope device history.',
      'Ảnh đạt yêu cầu đầu tiên của mỗi vị trí sẽ trở thành mốc ban đầu cho vị trí đó. Dữ liệu mô phỏng được tách riêng khỏi dữ liệu Skin AI Scope thật trong tương lai.'
    )
  }

  function formatDate(value){try{return new Intl.DateTimeFormat(locale()==='vi'?'vi-VN':'en-US',{day:'2-digit',month:'short',year:'numeric'}).format(new Date(value))}catch(_e){return ''}}

  async function refresh(){
    const card=ensureCard();if(!card)return
    copy(card)
    const body=card.querySelector('.dermHistoryBody')
    try{
      const res=await fetch(`/v1/dermatoscope/position-summary?subject_key=${encodeURIComponent(SUBJECT)}`,{cache:'no-store'})
      if(!res.ok)throw new Error('history')
      const rows=await res.json()
      const simulatorRows=rows.filter(r=>r.simulator)
      if(!simulatorRows.length){
        body.innerHTML=`<div class="dermHistoryEmpty"><strong>${tr('No close-up baseline yet','Chưa có mốc quét cận cảnh')}</strong><span>${tr('Complete a guided scan to create the first baseline for each position.','Hoàn thành một lần quét có hướng dẫn để tạo mốc đầu tiên cho từng vị trí.')}</span></div>`
        return
      }
      body.innerHTML=`<div class="dermHistoryGrid">${simulatorRows.map(r=>`<article class="dermHistoryItem"><div><strong>${regionLabel(r.region)} · ${subLabel(r.subregion)}</strong><span>${tr('Baseline','Mốc ban đầu')}: ${formatDate(r.first_capture_at)}</span></div><div class="dermHistoryCount"><b>${r.capture_count}</b><span>${tr(r.capture_count===1?'capture':'captures','lần chụp')}</span></div></article>`).join('')}</div><div class="dermHistoryNote">${tr('Simulator series · not validated for the physical Skin AI Scope yet.','Chuỗi dữ liệu mô phỏng · chưa được xác thực với Skin AI Scope thật.')}</div>`
    }catch(_e){
      body.innerHTML=`<div class="dermHistoryEmpty"><strong>${tr('History is temporarily unavailable','Tạm thời chưa tải được lịch sử')}</strong></div>`
    }
    document.documentElement.dataset.dermatoscopeHistoryVersion=VERSION
  }

  function start(){
    refresh()
    const host=root();if(!host)return
    const complete=host.querySelector('#dermComplete')
    if(complete){
      new MutationObserver(()=>{if(!complete.hidden)setTimeout(refresh,250)}).observe(complete,{attributes:true,attributeFilter:['hidden']})
    }
  }

  window.addEventListener('skin-ai:locale-change',()=>setTimeout(refresh,0))
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(start,300))
  else setTimeout(start,300)
  window.skinDermatoscopeHistory={version:VERSION,refresh}
})()
