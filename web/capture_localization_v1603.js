// V1.6.0.3 — Capture Localization Completion
// Presentation only. Localizes runtime capture guidance, quality states, and result timestamps.
(function(){
  const VERSION='1.6.0.3'
  const nodeState=new WeakMap()
  let scheduled=false

  const EN_TO_VI={
    'CAPTURE GUIDANCE V2':'HƯỚNG DẪN CHỤP V2',
    'Improve repeatability before analysis':'Tăng độ lặp lại trước khi phân tích',
    'Use camera':'Dùng camera',
    'Position region':'Đặt vùng vào khung',
    'Lighting':'Ánh sáng',
    'Sharpness':'Độ nét',
    'Stability':'Độ ổn định',
    'Position':'Vị trí',
    'Visual guide':'Khung hướng dẫn',
    'Checking…':'Đang kiểm tra…',
    'Good':'Tốt',
    'good':'tốt',
    'Adjust':'Điều chỉnh',
    'Poor':'Kém',
    'poor':'kém',
    'Hold steady':'Giữ máy ổn định',
    'Refocus':'Lấy nét lại',
    'Stable':'Ổn định',
    'Too much movement':'Di chuyển quá nhiều',
    'Usable':'Có thể dùng',
    'Handheld':'Cầm tay',
    'Distance':'Khoảng cách',
    'Center face':'Đưa mặt vào giữa',
    'Distance good':'Khoảng cách phù hợp',
    'Move back':'Lùi máy ra',
    'Move closer':'Đưa máy lại gần',
    'Use face guide':'Theo khung khuôn mặt',
    'Cancel':'Hủy',
    'Capture photo':'Chụp ảnh',
    'Center the full face in the guide. Keep the phone level and use even frontal light.':'Đặt toàn bộ khuôn mặt vào giữa khung hướng dẫn. Giữ điện thoại cân bằng và dùng ánh sáng đều từ phía trước.',
    'Lighting, sharpness and stability are browser-side estimates. Position and distance remain visual guidance; the backend performs the final quality check.':'Ánh sáng, độ nét và độ ổn định chỉ là ước tính trên trình duyệt. Vị trí và khoảng cách là hướng dẫn trực quan; hệ thống máy chủ thực hiện kiểm tra chất lượng cuối cùng.',
    'Lighting, sharpness and stability are browser estimates. Distance uses a temporary low-resolution server check with the same face detector as analysis; preview frames are not saved.':'Ánh sáng, độ nét và độ ổn định chỉ là ước tính trên trình duyệt. Khoảng cách được kiểm tra tạm thời bằng ảnh độ phân giải thấp trên máy chủ với cùng bộ phát hiện khuôn mặt dùng khi phân tích; các khung hình xem trước không được lưu.',
    'Camera access was not available. You can still choose an image from your device.':'Không thể truy cập camera. Bạn vẫn có thể chọn ảnh từ thiết bị.',
    'Low image resolution':'Độ phân giải ảnh thấp',
    'Use a higher-resolution capture so small skin features are not lost.':'Hãy dùng ảnh có độ phân giải cao hơn để không mất các chi tiết da nhỏ.',
    'Lighting outside preferred range':'Ánh sáng ngoài khoảng khuyến nghị',
    'Use more even illumination and avoid very dark or blown-out areas.':'Hãy dùng ánh sáng đều hơn và tránh vùng quá tối hoặc cháy sáng.',
    'Lighting could be more even':'Ánh sáng có thể đều hơn',
    'Try more neutral, even light before capture.':'Hãy thử ánh sáng trung tính và đồng đều hơn trước khi chụp.',
    'Image may be blurry':'Ảnh có thể bị mờ',
    'Refocus and hold the phone steady.':'Lấy nét lại và giữ điện thoại ổn định.',
    'Tap the face to refocus and hold steady briefly.':'Chạm vào khuôn mặt để lấy nét lại và giữ máy ổn định trong giây lát.',
    'Sharpness is borderline':'Độ nét ở mức giới hạn',
    'Hold steady and refocus before capture.':'Giữ máy ổn định và lấy nét lại trước khi chụp.',
    'PRE-CAPTURE CHECK':'KIỂM TRA TRƯỚC KHI CHỤP',
    'Ready for backend quality check':'Sẵn sàng để kiểm tra chất lượng trên máy chủ',
    'Retake recommended':'Khuyến nghị chụp lại',
    'Capture can be improved':'Ảnh chụp có thể được cải thiện',
    'Choose another image':'Chọn ảnh khác',
    'Analyze anyway':'Vẫn phân tích',
    'These browser checks are advisory. The server-side RGB/UV quality gates remain authoritative.':'Các kiểm tra trên trình duyệt chỉ mang tính hướng dẫn. Kiểm tra chất lượng RGB/UV phía máy chủ vẫn là kết quả quyết định.',
    'Ready for backend quality check':'Sẵn sàng để kiểm tra chất lượng trên máy chủ',
    'exposure and sharpness look acceptable.':'độ sáng và độ nét ở mức phù hợp.',
    'Quality blockers.':'Các lỗi chặn chất lượng.',
    'Advisory capture notes.':'Ghi chú hướng dẫn khi chụp.',
    'These warnings do not by themselves block a good-quality scan from longitudinal tracking.':'Các cảnh báo này riêng lẻ không loại một lần quét chất lượng tốt khỏi theo dõi theo thời gian.'
  }
  const VI_TO_EN=Object.fromEntries(Object.entries(EN_TO_VI).map(([en,vi])=>[vi,en]))

  function locale(){
    try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}
  }
  function dynamicVi(en){
    if(EN_TO_VI[en])return EN_TO_VI[en]
    let m
    if((m=en.match(/^(\d+) issue$/)))return `${m[1]} vấn đề`
    if((m=en.match(/^(\d+) issues$/)))return `${m[1]} vấn đề`
    if((m=en.match(/^(\d+)×(\d+) · exposure and sharpness look acceptable\.$/)))return `${m[1]}×${m[2]} · độ sáng và độ nét ở mức phù hợp.`
    if((m=en.match(/^Position the (.+) close-up inside the guide\. Keep device distance and angle consistent with prior captures\.$/)))return `Đặt vùng cận cảnh ${m[1]} vào trong khung hướng dẫn. Giữ khoảng cách và góc thiết bị nhất quán với các lần chụp trước.`
    return en
  }
  function target(en){return locale()==='vi'?dynamicVi(en):en}
  function canonical(core){return VI_TO_EN[core]||core}

  function translateNode(node){
    if(node.nodeType!==Node.TEXT_NODE)return
    const parent=node.parentElement
    if(!parent||['SCRIPT','STYLE','TEXTAREA'].includes(parent.tagName))return
    const current=node.data
    const leading=current.match(/^\s*/)?.[0]||''
    const trailing=current.match(/\s*$/)?.[0]||''
    const core=current.trim()
    if(!core)return
    let slot=nodeState.get(node)
    if(!slot){slot={en:canonical(core),last:null};nodeState.set(node,slot)}
    else if(core!==slot.last){
      const expected=target(slot.en)
      if(core!==expected)slot.en=canonical(core)
    }
    const translated=target(slot.en)
    if(translated===slot.en && locale()==='vi')return
    slot.last=translated
    const next=`${leading}${translated}${trailing}`
    if(current!==next)node.data=next
  }

  function formatResultDate(){
    const el=document.querySelector('#resultDate')
    if(!el)return
    try{
      if(typeof latest==='undefined'||!latest?.created_at)return
      const date=new Date(latest.created_at)
      if(Number.isNaN(date.getTime()))return
      const vi=locale()==='vi'
      const formatted=new Intl.DateTimeFormat(vi?'vi-VN':'en-US',{
        year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:!vi
      }).format(date)
      if(el.textContent!==formatted)el.textContent=formatted
    }catch(_e){}
  }

  function localizeCaptureQualityValue(){
    const el=document.querySelector('.testerQualityScore strong')
    if(!el)return
    const core=el.textContent.trim()
    if(locale()==='vi'){
      if(core==='good'||core==='Good')el.textContent='Tốt'
      else if(core==='poor'||core==='Poor')el.textContent='Kém'
    }else{
      if(core==='Tốt')el.textContent='Good'
      else if(core==='Kém')el.textContent='Poor'
    }
  }

  function apply(){
    scheduled=false
    const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT)
    let node
    while((node=walker.nextNode()))translateNode(node)
    formatResultDate()
    localizeCaptureQualityValue()
    document.documentElement.dataset.captureLocalizationVersion=VERSION
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(apply)}

  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true,characterData:true})
  window.addEventListener('skin-ai:locale-change',schedule)
  document.addEventListener('click',e=>{
    if(e.target.closest('[data-tab],[data-go],[data-mode],[data-result-view],#cgOpenCamera,#cgCancelCamera,#cgCapture,#cgContinue,#cgRetake'))setTimeout(schedule,0)
  })
  setInterval(()=>{
    if(document.querySelector('#scan.view.active'))schedule()
  },750)
  setTimeout(schedule,0)
})()
