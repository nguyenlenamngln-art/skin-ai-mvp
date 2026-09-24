// V1.6.0 — Vietnamese / English Localization Foundation
// Presentation only. RGB V1.5.2, Capture Protocol V1.4, comparison scoring and study access remain unchanged.
(function(){
  const VERSION='1.6.0'
  const STORAGE_KEY='skin_ai_locale_v160'
  const SUPPORTED=['vi','en']
  const nodeState=new WeakMap()
  let locale=SUPPORTED.includes(localStorage.getItem(STORAGE_KEY))?localStorage.getItem(STORAGE_KEY):'vi'
  let scheduled=false

  const VI={
    'Personal skin tracking':'Theo dõi da cá nhân',
    'Today':'Hôm nay','Progress':'Tiến trình','Scan':'Quét','Routine':'Chu trình','Journey':'Hành trình',
    '+ Scan':'+ Quét',
    'Tracks your own visible-light skin signals over time. Not a diagnostic device.':'Theo dõi các tín hiệu da của chính bạn theo thời gian dưới ánh sáng khả kiến. Không phải thiết bị chẩn đoán.',
    'PERSONAL SKIN TRACKING':'THEO DÕI DA CÁ NHÂN',
    'Your skin today':'Làn da hôm nay','Your progress':'Tiến trình của bạn','Take a skin scan':'Quét da','Your routine':'Chu trình của bạn','Your journey':'Hành trình của bạn',
    'Checking engines…':'Đang kiểm tra hệ thống…','RGB ready · UV unavailable':'RGB sẵn sàng · UV chưa khả dụng',
    'LATEST SIGNAL':'TÍN HIỆU GẦN NHẤT','No scans yet':'Chưa có lần quét nào','Start with a Phone RGB or UV scan to create your baseline.':'Bắt đầu bằng một lần quét RGB điện thoại hoặc UV để tạo mốc ban đầu.',
    'Start scan':'Bắt đầu quét','SKIN INSIGHT':'GỢI Ý VỀ DA','Repeat scans under similar lighting, distance and angle to track change.':'Lặp lại lần quét với ánh sáng, khoảng cách và góc chụp tương tự để theo dõi thay đổi.',
    'Development insight based only on stored measurements.':'Gợi ý thử nghiệm chỉ dựa trên các chỉ số đã lưu.',
    '90-DAY VIEW':'THEO DÕI 90 NGÀY','Signal trend':'Xu hướng tín hiệu','Run at least two scans of the same type to see your trend.':'Cần ít nhất hai lần quét cùng loại để xem xu hướng.',

    'YOUR SKIN TODAY':'LÀN DA HÔM NAY','VISIBLE-LIGHT SIGNALS':'TÍN HIỆU ÁNH SÁNG KHẢ KIẾN','Your snapshot':'Tổng quan hôm nay',
    'This is your current personal baseline.':'Đây là mốc ban đầu hiện tại của riêng bạn.','Your personal reference':'Mốc tham chiếu cá nhân',
    'Redness':'Đỏ da','Pigmentation':'Sắc tố','Pigment':'Sắc tố','Texture':'Kết cấu','Redness area':'Vùng đỏ','Pigmented area':'Vùng sắc tố',
    'Visible redness area':'Vùng đỏ nhìn thấy','Visible pigmentation area':'Vùng sắc tố nhìn thấy','Visible-light texture signal':'Tín hiệu kết cấu dưới ánh sáng khả kiến',
    'Good for comparison':'Phù hợp để so sánh','Saved, not used for trends':'Đã lưu, không dùng cho xu hướng','No scan':'Chưa có lần quét',
    'NEXT':'TIẾP THEO','You have a recent scan':'Bạn vừa có một lần quét gần đây','View progress':'Xem tiến trình','See progress':'Xem tiến trình','View journey':'Xem hành trình','Routine & notes':'Chu trình & ghi chú',
    'Your latest comparable scan is recent. Keep your next capture under similar lighting, distance and angle.':'Lần quét gần nhất có thể so sánh vẫn còn mới. Hãy giữ ánh sáng, khoảng cách và góc chụp tương tự cho lần tiếp theo.',
    'Ready for another comparison':'Sẵn sàng cho lần so sánh tiếp theo','A new scan can extend your personal timeline. Try to reuse similar lighting, distance and angle.':'Một lần quét mới sẽ bổ sung vào hành trình của bạn. Hãy cố gắng giữ ánh sáng, khoảng cách và góc chụp tương tự.',
    'Personal visible-light tracking only. Results are not diagnoses or population rankings.':'Chỉ dùng để theo dõi cá nhân dưới ánh sáng khả kiến. Kết quả không phải chẩn đoán hay xếp hạng so với cộng đồng.',

    'FROM YOUR BASELINE':'SO VỚI MỐC BAN ĐẦU','BEFORE & AFTER':'TRƯỚC & SAU','Drag to compare':'Kéo để so sánh','Baseline':'Mốc ban đầu','Latest':'Mới nhất',
    'Comparison match':'Độ phù hợp để so sánh','Strong':'Rất phù hợp','Usable':'Có thể dùng','Review':'Cần xem lại',
    'Framing and lighting are similar enough for personal trend comparison.':'Khung hình và ánh sáng đủ tương đồng để so sánh xu hướng cá nhân.',
    'Usable for comparison, but older scans lack full framing metadata; confidence is intentionally capped.':'Có thể dùng để so sánh, nhưng các lần quét cũ thiếu dữ liệu khung hình đầy đủ nên mức tin cậy được giới hạn có chủ đích.',
    'This scan is valid on its own, but capture differences make trend comparison less reliable.':'Lần quét này vẫn hợp lệ khi xem riêng, nhưng khác biệt khi chụp làm việc so sánh xu hướng kém tin cậy hơn.',
    'Changes use the values shown above, so displayed endpoints and displayed deltas always agree. Higher/lower is descriptive, not good/bad.':'Thay đổi được tính từ chính các giá trị hiển thị ở trên nên số đầu-cuối và mức chênh luôn khớp nhau. Cao hơn/thấp hơn chỉ mang tính mô tả, không đồng nghĩa tốt/xấu.',
    'Changes describe your own comparable RGB scans. Higher/lower is descriptive, not good/bad.':'Các thay đổi mô tả những lần quét RGB có thể so sánh của chính bạn. Cao hơn/thấp hơn chỉ mang tính mô tả, không đồng nghĩa tốt/xấu.',
    'TREND':'XU HƯỚNG','Your change from baseline':'Thay đổi so với mốc ban đầu','Your visible signals over time':'Tín hiệu nhìn thấy theo thời gian',
    'Change from displayed baseline':'Thay đổi so với mốc hiển thị','No meaningful change at the displayed precision':'Không có thay đổi đáng kể ở độ chính xác đang hiển thị',
    'Photos are normalized to a shared mobile viewport so both scans use the same face-centered crop. Pose, expression and perspective can still create visual differences.':'Ảnh được chuẩn hóa vào cùng một khung nhìn trên điện thoại để hai lần quét dùng chung vùng cắt căn giữa khuôn mặt. Tư thế, biểu cảm và phối cảnh vẫn có thể tạo khác biệt hình ảnh.',
    'Photos are normalized to the same facial geometry, with a small residual alignment when the image pattern is stable. Pose, expression and perspective can still create differences.':'Ảnh được chuẩn hóa theo cùng hình học khuôn mặt và tinh chỉnh căn chỉnh nhẹ khi mẫu hình ảnh đủ ổn định. Tư thế, biểu cảm và phối cảnh vẫn có thể tạo khác biệt.',
    'Photos are face-centered for easier visual comparison. Lighting, expression and head angle can still affect apparent differences.':'Ảnh được căn giữa theo khuôn mặt để dễ so sánh hơn. Ánh sáng, biểu cảm và góc đầu vẫn có thể ảnh hưởng đến khác biệt nhìn thấy.',

    'MY JOURNEY':'HÀNH TRÌNH CỦA TÔI','Your photos and measurements in one simple timeline.':'Ảnh và các chỉ số của bạn trong một dòng thời gian đơn giản.','View scan':'Xem lần quét',
    'NEXT MILESTONE':'MỐC TIẾP THEO','Add your second comparable scan':'Thêm lần quét thứ hai có thể so sánh','With two scans, Journey can start showing visible changes from your personal baseline.':'Khi có hai lần quét, Hành trình có thể bắt đầu hiển thị thay đổi nhìn thấy so với mốc ban đầu của bạn.',
    'Take another scan':'Quét thêm một lần','Your timeline starts with your first scan':'Dòng thời gian bắt đầu từ lần quét đầu tiên','Once you have comparable scans, this page becomes a visual record of your skin over time.':'Khi có các lần quét có thể so sánh, trang này sẽ trở thành nhật ký hình ảnh về làn da của bạn theo thời gian.',

    'MORNING':'BUỔI SÁNG','AM routine':'Chu trình buổi sáng','EVENING':'BUỔI TỐI','PM routine':'Chu trình buổi tối','Save routine':'Lưu chu trình',
    'One product or step per line.':'Mỗi dòng một sản phẩm hoặc một bước.','Use consistent names so you can remember what changed.':'Dùng tên nhất quán để dễ nhớ những gì đã thay đổi.',
    'SKIN DIARY':'NHẬT KÝ DA','Add context for today':'Ghi chú cho hôm nay','Optional notes can help you remember what was different around a scan. They are saved on this device only.':'Ghi chú tùy chọn giúp bạn nhớ điều gì khác biệt quanh thời điểm quét. Ghi chú chỉ được lưu trên thiết bị này.',
    'New product':'Sản phẩm mới','Outdoor / sun':'Ngoài trời / nắng','Shaving':'Cạo râu','Makeup':'Trang điểm','Poor sleep':'Ngủ kém','Other':'Khác',
    'Save today\'s note':'Lưu ghi chú hôm nay','RECENT NOTES':'GHI CHÚ GẦN ĐÂY','Remember what changed':'Ghi lại những thay đổi','No diary notes yet.':'Chưa có ghi chú nào.',

    'Tester access':'Truy cập thử nghiệm','Use study code':'Dùng mã thử nghiệm','Take a clear photo':'Chụp ảnh rõ nét','Open camera':'Mở camera','Advanced scan settings':'Cài đặt quét nâng cao','Hide advanced settings':'Ẩn cài đặt nâng cao',
    'Or upload a front-facing photo':'Hoặc tải ảnh chụp chính diện','Neutral light · no beauty filters · up to 20 MB':'Ánh sáng trung tính · không dùng bộ lọc làm đẹp · tối đa 20 MB','Choose image':'Chọn ảnh',
    'Camera guidance checks lighting, sharpness and stability before analysis.':'Hướng dẫn camera kiểm tra ánh sáng, độ nét và độ ổn định trước khi phân tích.',
    'Built-in webcam or phone camera supported.':'Hỗ trợ webcam tích hợp hoặc camera điện thoại.','Live guidance checks lighting, sharpness and stability.':'Hướng dẫn trực tiếp kiểm tra ánh sáng, độ nét và độ ổn định.',
    'Face should fill roughly 20–60% of the frame.':'Khuôn mặt nên chiếm khoảng 20–60% khung hình.','Use the same lighting, distance and angle for repeat scans.':'Giữ ánh sáng, khoảng cách và góc chụp tương tự cho các lần quét lặp lại.',
    'Capture or upload a front-facing photo':'Chụp hoặc tải ảnh chính diện','Natural/neutral light · no beauty filters · up to 20 MB':'Ánh sáng tự nhiên/trung tính · không dùng bộ lọc làm đẹp · tối đa 20 MB',
    'YOUR RESULT':'KẾT QUẢ CỦA BẠN','Latest scan':'Lần quét gần nhất','Current attempt':'Lần thử hiện tại','Capture rejected':'Ảnh chụp chưa đạt',
    'WHAT WE DETECTED':'NHỮNG GÌ ĐÃ PHÁT HIỆN','Original':'Ảnh gốc','Skin region':'Vùng da','Redness map':'Bản đồ đỏ da','Pigmentation map':'Bản đồ sắc tố','Combined':'Kết hợp',
    'SCAN QUALITY':'CHẤT LƯỢNG LẦN QUÉT','Advanced details':'Chi tiết nâng cao','Measurement and scan-quality details':'Chi tiết chỉ số và chất lượng lần quét','Technical details':'Chi tiết kỹ thuật',
    'For your next scan':'Cho lần quét tiếp theo','Capture conditions are suitable. Reuse similar lighting, distance and angle for repeat scans.':'Điều kiện chụp phù hợp. Hãy dùng ánh sáng, khoảng cách và góc chụp tương tự cho các lần quét tiếp theo.',
    'Phone RGB research measurement.':'Phép đo nghiên cứu bằng RGB điện thoại.','These are relative visible-light proxies for longitudinal tracking. They are not diagnoses and are not equivalent to polarized or UV imaging.':'Đây là các chỉ số tương đối dưới ánh sáng khả kiến để theo dõi theo thời gian. Chúng không phải chẩn đoán và không tương đương ảnh phân cực hoặc UV.',
    'Research measurement.':'Phép đo nghiên cứu.','Artifact pixels are excluded rather than reconstructed. Compare scans only when capture conditions are similar.':'Các điểm ảnh nhiễu bị loại bỏ thay vì tái tạo. Chỉ so sánh các lần quét khi điều kiện chụp tương tự.',
    'Choose a scan type, then capture or upload an image.':'Chọn loại quét, sau đó chụp hoặc tải ảnh lên.',
    'Phone RGB':'RGB điện thoại','UV fluorescence':'Huỳnh quang UV',
    'Capture quality':'Chất lượng ảnh chụp','Status':'Trạng thái','Rejected':'Không đạt','Issues':'Vấn đề','Retake guidance':'Hướng dẫn chụp lại',
    'not added to History or trends':'không được thêm vào lịch sử hoặc xu hướng','quality gate':'kiểm tra chất lượng','See guidance':'Xem hướng dẫn',
    'Retake with steady focus, even frontal light, and the face centered in frame.':'Chụp lại với máy ổn định, ánh sáng đều từ phía trước và khuôn mặt ở giữa khung hình.',

    'Higher':'Cao hơn','Lower':'Thấp hơn','Stable':'Ổn định','No comparison':'Chưa có so sánh','Your personal reference':'Mốc tham chiếu cá nhân',
    'Not enough data yet':'Chưa đủ dữ liệu','Take at least two comparable scans':'Cần ít nhất hai lần quét có thể so sánh',
    'Your visual comparison will appear here':'So sánh hình ảnh sẽ xuất hiện tại đây','Take another quality-eligible RGB scan to compare it with your baseline.':'Hãy thực hiện thêm một lần quét RGB đạt chất lượng để so sánh với mốc ban đầu.',
    'Your baseline is ready':'Mốc ban đầu đã sẵn sàng','Your baseline is saved':'Mốc ban đầu đã được lưu','WHAT HAPPENS NEXT':'TIẾP THEO LÀ GÌ',
    'Take another comparable scan later to unlock before/after comparison and trend charts.':'Thực hiện thêm một lần quét có thể so sánh để mở khóa so sánh trước/sau và biểu đồ xu hướng.',

    'Research measurement':'Phép đo nghiên cứu','Research and validation review':'Xem xét nghiên cứu và xác thực','Result experience V1.5.5':'Trải nghiệm kết quả V1.5.5',
    'Visible-light skin signals':'Tín hiệu da dưới ánh sáng khả kiến','These measurements describe this photo and are designed primarily for tracking your own changes over time.':'Các chỉ số này mô tả ảnh hiện tại và chủ yếu dùng để theo dõi thay đổi của chính bạn theo thời gian.',
    'New baseline after analysis update':'Mốc ban đầu mới sau cập nhật phân tích','Future scans using the same analysis version can be compared with this result.':'Các lần quét sau dùng cùng phiên bản phân tích có thể được so sánh với kết quả này.'
  }

  const PLACEHOLDER_VI={
    'Optional note, e.g. started a new cleanser today':'Ghi chú tùy chọn, ví dụ: hôm nay bắt đầu dùng sữa rửa mặt mới'
  }

  const MONTHS={Jan:'Thg 1',Feb:'Thg 2',Mar:'Thg 3',Apr:'Thg 4',May:'Thg 5',Jun:'Thg 6',Jul:'Thg 7',Aug:'Thg 8',Sep:'Thg 9',Oct:'Thg 10',Nov:'Thg 11',Dec:'Thg 12'}
  const WEEKDAYS={Sun:'CN',Mon:'Th 2',Tue:'Th 3',Wed:'Th 4',Thu:'Th 5',Fri:'Th 6',Sat:'Th 7'}

  function dateVi(text){
    let out=text
    out=out.replace(/\b(Sun|Mon|Tue|Wed|Thu|Fri|Sat),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b/g,(_,d,m,day)=>`${WEEKDAYS[d]}, ${day} ${MONTHS[m]}`)
    out=out.replace(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b/g,(_,m,day)=>`${day} ${MONTHS[m]}`)
    return out
  }

  function dynamicVi(text){
    if(VI[text])return VI[text]
    let m
    if((m=text.match(/^(\d+) comparable scans?$/)))return `${m[1]} lần quét có thể so sánh`
    if((m=text.match(/^(\d+) scans? · start to latest$/)))return `${m[1]} lần quét · từ đầu đến gần nhất`
    if((m=text.match(/^(\d+) saved scans?$/)))return `${m[1]} lần quét đã lưu`
    if((m=text.match(/^Compared with your baseline from (.+)\.$/)))return `So với mốc ban đầu ngày ${dateVi(m[1])}.`
    if((m=text.match(/^Good for comparison$/)))return 'Phù hợp để so sánh'
    if((m=text.match(/^Strong · (\d+)\/100$/)))return `Rất phù hợp · ${m[1]}/100`
    if((m=text.match(/^Usable · (\d+)\/100$/)))return `Có thể dùng · ${m[1]}/100`
    if((m=text.match(/^Review · (\d+)\/100$/)))return `Cần xem lại · ${m[1]}/100`
    if((m=text.match(/^Take at least (\d+) comparable scans$/)))return `Cần ít nhất ${m[1]} lần quét có thể so sánh`
    if((m=text.match(/^This is your first RGB baseline\.$/)))return 'Đây là mốc RGB ban đầu đầu tiên của bạn.'
    if((m=text.match(/^This is your first UV baseline\.$/)))return 'Đây là mốc UV ban đầu đầu tiên của bạn.'
    if((m=text.match(/^([+-]?\d+(?:\.\d+)?) pp vs previous$/)))return `${m[1]} điểm % so với lần trước`
    if((m=text.match(/^(↑|↓|→) ([+-]?\d+(?:\.\d+)?) pp$/)))return `${m[1]} ${m[2]} điểm %`
    if((m=text.match(/^(↑|↓|→) ([+-]?\d+(?:\.\d+)?)$/)))return `${m[1]} ${m[2]}`
    return dateVi(text)
  }

  function translateText(text){
    const leading=text.match(/^\s*/)?.[0]||''
    const trailing=text.match(/\s*$/)?.[0]||''
    const core=text.trim()
    if(!core)return text
    const translated=locale==='vi'?dynamicVi(core):core
    return `${leading}${translated}${trailing}`
  }

  function updateTitles(){
    try{
      if(typeof titles!=='undefined'){
        const map=locale==='vi'
          ?{home:'Làn da hôm nay',progress:'Tiến trình của bạn',scan:'Quét da',routine:'Chu trình của bạn',journey:'Hành trình của bạn',history:'Lịch sử quét'}
          :{home:'Your skin today',progress:'Your progress',scan:'Take a skin scan',routine:'Your routine',journey:'Your journey',history:'Scan history'}
        Object.assign(titles,map)
      }
    }catch(_e){}
  }

  function translateNode(node){
    if(node.nodeType!==Node.TEXT_NODE)return
    const parent=node.parentElement
    if(!parent||['SCRIPT','STYLE','TEXTAREA','OPTION'].includes(parent.tagName))return
    let state=nodeState.get(node)
    const current=node.data
    if(!state){state={original:current,last:null};nodeState.set(node,state)}
    else if(current!==state.last&&current!==state.original)state.original=current
    const target=locale==='vi'?translateText(state.original):state.original
    state.last=target
    if(current!==target)node.data=target
  }

  function translateAttributes(root){
    root.querySelectorAll?.('[placeholder]').forEach(el=>{
      if(!el.dataset.i18nOriginalPlaceholder)el.dataset.i18nOriginalPlaceholder=el.getAttribute('placeholder')||''
      const original=el.dataset.i18nOriginalPlaceholder
      el.setAttribute('placeholder',locale==='vi'?(PLACEHOLDER_VI[original]||dynamicVi(original)):original)
    })
    root.querySelectorAll?.('img[alt]').forEach(el=>{
      if(!el.dataset.i18nOriginalAlt)el.dataset.i18nOriginalAlt=el.getAttribute('alt')||''
      if(locale==='en')el.setAttribute('alt',el.dataset.i18nOriginalAlt)
    })
  }

  function translateTree(root=document.body){
    if(!root)return
    if(root.nodeType===Node.TEXT_NODE){translateNode(root);return}
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT)
    let node
    while((node=walker.nextNode()))translateNode(node)
    translateAttributes(root)
  }

  function ensureSwitcher(){
    const header=document.querySelector('main>header')
    if(!header)return
    let wrap=document.querySelector('.languageSwitchV160')
    if(!wrap){
      wrap=document.createElement('div')
      wrap.className='languageSwitchV160'
      wrap.setAttribute('role','group')
      wrap.setAttribute('aria-label','Language / Ngôn ngữ')
      wrap.innerHTML='<button type="button" data-locale="vi" aria-label="Tiếng Việt">VI</button><button type="button" data-locale="en" aria-label="English">EN</button>'
      header.appendChild(wrap)
      wrap.addEventListener('click',e=>{
        const button=e.target.closest('[data-locale]')
        if(button)setLocale(button.dataset.locale)
      })
    }
    wrap.querySelectorAll('[data-locale]').forEach(btn=>btn.classList.toggle('active',btn.dataset.locale===locale))
  }

  function applyLocale(){
    document.documentElement.lang=locale
    document.documentElement.dataset.locale=locale
    updateTitles()
    ensureSwitcher()
    translateTree(document.body)
    const active=document.querySelector('.view.active')?.id
    if(active&&typeof titles!=='undefined'&&titles[active]){
      const title=document.querySelector('#title')
      if(title)title.textContent=titles[active]
      translateTree(title)
    }
  }

  function setLocale(next){
    if(!SUPPORTED.includes(next))return
    locale=next
    localStorage.setItem(STORAGE_KEY,locale)
    updateTitles()
    try{if(typeof render==='function')render()}catch(_e){}
    try{if(typeof applyModeUI==='function'&&document.querySelector('#scan.view.active'))applyModeUI()}catch(_e){}
    requestAnimationFrame(applyLocale)
    window.dispatchEvent(new CustomEvent('skin-ai:locale-change',{detail:{locale}}))
  }

  function schedule(){
    if(scheduled)return
    scheduled=true
    requestAnimationFrame(()=>{scheduled=false;applyLocale()})
  }

  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true,characterData:true})
  document.addEventListener('click',e=>{if(e.target.closest('[data-tab],[data-go],[data-result-view]'))setTimeout(schedule,0)})
  window.skinI18n={version:VERSION,getLocale:()=>locale,setLocale,t:(en)=>locale==='vi'?dynamicVi(en):en}
  setTimeout(applyLocale,0)
})()
