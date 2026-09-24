// V1.6.0.5 — mobile capture localization ownership + runtime compatibility patch
// Presentation only. RGB V1.5.2, Capture Protocol V1.4, comparison scoring and study access remain unchanged.
(function(){
  const VERSION='1.6.0.5'
  const state=new WeakMap()
  let scheduled=false

  const EN_TO_VI={
    // Compound longitudinal statuses.
    '↑ Higher':'↑ Cao hơn','↓ Lower':'↓ Thấp hơn','→ Stable':'→ Ổn định','— No comparison':'— Chưa có so sánh',
    '↑ Higher from baseline':'↑ Cao hơn so với mốc ban đầu','↓ Lower from baseline':'↓ Thấp hơn so với mốc ban đầu','→ Stable from baseline':'→ Ổn định so với mốc ban đầu',

    // Capture shell and live guidance.
    'CAPTURE GUIDANCE V2':'HƯỚNG DẪN CHỤP V2','Improve repeatability before analysis':'Tăng độ lặp lại trước khi phân tích','Use camera':'Dùng camera','Open camera':'Mở camera',
    'Position region':'Đặt vùng vào khung','Lighting':'Ánh sáng','Sharpness':'Độ nét','Stability':'Độ ổn định','Position':'Vị trí','Visual guide':'Khung hướng dẫn','Checking…':'Đang kiểm tra…',
    'Good':'Tốt','good':'tốt','Adjust':'Cần điều chỉnh','Poor':'Chưa đạt','poor':'chưa đạt','Hold steady':'Giữ máy ổn định','Refocus':'Lấy nét lại','Stable':'Ổn định','Too much movement':'Di chuyển quá nhiều','Move less':'Giữ yên hơn','Usable':'Có thể dùng','Handheld':'Cầm tay',
    'Distance':'Khoảng cách','Center face':'Đưa mặt vào giữa khung','Distance good':'Khoảng cách phù hợp','Move back':'Đưa máy ra xa hơn','Move closer':'Đưa máy lại gần hơn','Use face guide':'Căn theo khung khuôn mặt',
    'Cancel':'Hủy','Capture photo':'Chụp ảnh',
    'Even light · Face centered · Hold steady':'Ánh sáng đều · Đặt mặt vào giữa khung · Giữ máy ổn định',
    'We’ll compare framing and lighting with your previous good scan.':'Hệ thống sẽ so sánh khung hình và ánh sáng với lần quét đạt yêu cầu trước đó.',
    "We'll compare framing and lighting with your previous good scan.":'Hệ thống sẽ so sánh khung hình và ánh sáng với lần quét đạt yêu cầu trước đó.',
    'Match previous framing':'Căn theo khung hình trước',
    'Previous comparable scan alignment reference':'Ảnh tham chiếu để căn theo lần quét trước',
    'For repeat scans, use similar lighting, distance and angle.':'Đối với các lần quét lặp lại, hãy giữ ánh sáng, khoảng cách và góc chụp tương tự.',
    'Or upload a photo':'Hoặc tải ảnh lên','Or upload a front-facing photo':'Hoặc tải ảnh chụp chính diện','Neutral light · no beauty filters':'Ánh sáng trung tính · không dùng bộ lọc làm đẹp','Choose photo':'Chọn ảnh',
    'Center the full face in the guide. Keep the phone level and use even frontal light.':'Đặt toàn bộ khuôn mặt vào giữa khung hướng dẫn. Giữ điện thoại cân bằng và dùng ánh sáng đều từ phía trước.',
    'Lighting, sharpness and stability are browser-side estimates. Position and distance remain visual guidance; the backend performs the final quality check.':'Ánh sáng, độ nét và độ ổn định chỉ là ước tính trên trình duyệt. Vị trí và khoảng cách là hướng dẫn trực quan; hệ thống máy chủ thực hiện kiểm tra chất lượng cuối cùng.',
    'Lighting, sharpness and stability are browser estimates. Distance uses a temporary low-resolution server check with the same face detector as analysis; preview frames are not saved.':'Ánh sáng, độ nét và độ ổn định chỉ là ước tính trên trình duyệt. Khoảng cách được kiểm tra tạm thời bằng ảnh độ phân giải thấp trên máy chủ với cùng bộ phát hiện khuôn mặt dùng khi phân tích; các khung hình xem trước không được lưu.',
    'Camera access was not available. You can still choose an image from your device.':'Không thể truy cập camera. Bạn vẫn có thể chọn ảnh từ thiết bị.',

    // Pre-capture validation states.
    'Low image resolution':'Độ phân giải ảnh thấp','Use a higher-resolution capture so small skin features are not lost.':'Hãy dùng ảnh có độ phân giải cao hơn để không mất các chi tiết da nhỏ.',
    'Lighting outside preferred range':'Ánh sáng ngoài khoảng khuyến nghị','Use more even illumination and avoid very dark or blown-out areas.':'Hãy dùng ánh sáng đều hơn và tránh vùng quá tối hoặc cháy sáng.',
    'Lighting could be more even':'Ánh sáng có thể đều hơn','Try more neutral, even light before capture.':'Hãy thử ánh sáng trung tính và đồng đều hơn trước khi chụp.',
    'Image may be blurry':'Ảnh có thể bị mờ','Refocus and hold the phone steady.':'Lấy nét lại và giữ điện thoại ổn định.','Tap the face to refocus and hold steady briefly.':'Chạm vào khuôn mặt để lấy nét lại và giữ máy ổn định trong giây lát.',
    'Sharpness is borderline':'Độ nét ở mức giới hạn','Hold steady and refocus before capture.':'Giữ máy ổn định và lấy nét lại trước khi chụp.',
    'PRE-CAPTURE CHECK':'KIỂM TRA TRƯỚC KHI CHỤP','Ready for backend quality check':'Sẵn sàng để kiểm tra chất lượng trên máy chủ','Retake recommended':'Khuyến nghị chụp lại','Capture can be improved':'Ảnh chụp có thể được cải thiện','Choose another image':'Chọn ảnh khác','Analyze anyway':'Vẫn phân tích',
    'These browser checks are advisory. The server-side RGB/UV quality gates remain authoritative.':'Các kiểm tra trên trình duyệt chỉ mang tính hướng dẫn. Kiểm tra chất lượng RGB/UV phía máy chủ vẫn là kết quả quyết định.',

    // Tracking/context and post-analysis notes.
    'Phone RGB defaults to My profile · Full face. Choose another profile only when needed.':'RGB điện thoại mặc định dùng Hồ sơ của tôi · Toàn mặt. Chỉ chọn hồ sơ khác khi cần.',
    'Choose both profile and region for longitudinal comparison, or leave both blank for analysis-only.':'Chọn cả hồ sơ và vùng để so sánh theo thời gian, hoặc để trống cả hai nếu chỉ phân tích.',
    'Quality blockers.':'Các lỗi chặn chất lượng.','Advisory capture notes.':'Ghi chú hướng dẫn khi chụp.','These warnings do not by themselves block a good-quality scan from longitudinal tracking.':'Các cảnh báo này riêng lẻ không loại một lần quét chất lượng tốt khỏi theo dõi theo thời gian.'
  }
  const VI_TO_EN=Object.fromEntries(Object.entries(EN_TO_VI).map(([en,vi])=>[vi,en]))

  function locale(){
    try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}
  }
  function canonical(text){return VI_TO_EN[text]||text}
  function dynamicVi(en){
    if(EN_TO_VI[en])return EN_TO_VI[en]
    let m
    if((m=en.match(/^(\d+) issues?$/)))return `${m[1]} vấn đề`
    if((m=en.match(/^(\d+)×(\d+) · exposure and sharpness look acceptable\.$/)))return `${m[1]}×${m[2]} · độ sáng và độ nét ở mức phù hợp.`
    if((m=en.match(/^Position the (.+) close-up inside the guide\. Keep device distance and angle consistent with prior captures\.$/)))return `Đặt vùng cận cảnh ${m[1]} vào trong khung hướng dẫn. Giữ khoảng cách và góc thiết bị nhất quán với các lần chụp trước.`
    return en
  }
  function target(en){return locale()==='vi'?dynamicVi(en):canonical(en)}

  // Extend the shared translator so legacy capture writers can localize before touching the DOM.
  const baseT=window.skinI18n?.t?.bind(window.skinI18n)
  if(window.skinI18n){
    window.skinI18n.t=function(en){
      const canonicalEn=canonical(String(en??''))
      if(locale()!=='vi')return canonicalEn
      const fromBase=baseT?baseT(canonicalEn):canonicalEn
      return fromBase!==canonicalEn?fromBase:dynamicVi(canonicalEn)
    }
  }
  window.skinCaptureI18n={version:VERSION,getLocale:locale,t:(en)=>target(canonical(String(en??''))),canonical}

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
      const formatted=new Intl.DateTimeFormat(vi?'vi-VN':'en-US',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:!vi}).format(date)
      if(el.textContent!==formatted)el.textContent=formatted
    }catch(_e){}
  }

  function localizeCaptureQualityValue(){
    const el=document.querySelector('.testerQualityScore strong')
    if(!el)return
    const core=el.textContent.trim()
    if(locale()==='vi'){
      if(core==='good'||core==='Good')el.textContent='Tốt'
      else if(core==='poor'||core==='Poor')el.textContent='Chưa đạt'
    }else{
      if(core==='Tốt')el.textContent='Good'
      else if(core==='Chưa đạt'||core==='Kém')el.textContent='Poor'
    }
  }

  function refreshCaptureSemantics(){
    const t=window.skinCaptureI18n.t
    const pairs=[
      ['#captureGuidanceV2 .cgHeader b','Take a clear photo'],['#cgOpenCamera','Open camera'],
      ['#captureGuidanceV2 .uxCaptureHint','Even light · Face centered · Hold steady'],
      ['#captureGuidanceV2 .v159RefHint','We’ll compare framing and lighting with your previous good scan.'],
      ['#captureGuidanceV2 .v159GhostLabel','Match previous framing'],
      ['#cgCancelCamera','Cancel'],['#cgCapture','Capture photo']
    ]
    for(const [selector,en] of pairs){const el=document.querySelector(selector);if(el&&el.textContent!==t(en))el.textContent=t(en)}
    const ghost=document.querySelector('.v159Ghost')
    if(ghost)ghost.alt=t('Previous comparable scan alignment reference')
    const labelMap={lighting:'Lighting',sharpness:'Sharpness',stability:'Stability',distance:'Distance'}
    Object.entries(labelMap).forEach(([key,en])=>{const el=document.querySelector(`[data-cg-check="${key}"] span`);if(el)el.textContent=t(en)})
  }

  function apply(){
    scheduled=false
    const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT)
    let node
    while((node=walker.nextNode()))translateNode(node)
    formatResultDate();localizeCaptureQualityValue();refreshCaptureSemantics()
    document.documentElement.dataset.localizationPatchVersion=VERSION
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(apply)}

  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true,characterData:true})
  window.addEventListener('skin-ai:locale-change',schedule)
  document.addEventListener('click',e=>{
    if(e.target.closest('[data-tab],[data-go],[data-mode],[data-result-view],#cgOpenCamera,#cgCancelCamera,#cgCapture,#cgContinue,#cgRetake'))setTimeout(schedule,0)
  })
  setInterval(()=>{if(document.querySelector('#scan.view.active'))schedule()},750)
  setTimeout(()=>{schedule();window.dispatchEvent(new CustomEvent('skin-ai:capture-i18n-ready'))},0)
})()