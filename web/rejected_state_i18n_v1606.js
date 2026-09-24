// V1.6.0.6 — rejected scan localization
// Presentation only. Keeps API quality codes canonical while rendering friendly VI/EN copy.
(function(){
  const VERSION='1.6.0.6'
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const isVi=()=>locale()==='vi'
  const pick=(en,vi)=>isVi()?vi:en

  const FLAGS={
    too_dark:['Too dark','Ảnh quá tối'],
    too_bright:['Too bright','Ảnh quá sáng'],
    blurry:['Image is blurry','Ảnh chưa đủ nét'],
    face_too_small:['Face too small in frame','Khuôn mặt quá nhỏ trong khung'],
    face_too_close:['Face too close to camera','Khuôn mặt quá gần camera'],
    face_off_center:['Face off center','Khuôn mặt lệch tâm'],
    shadow_clipping:['Deep shadows','Vùng tối quá sâu'],
    highlight_clipping:['Highlights clipped','Vùng sáng bị cháy'],
    uneven_light_or_pose:['Uneven light or pose','Ánh sáng hoặc tư thế chưa đều'],
    segmentation_unstable:['Skin-region boundary unstable','Biên vùng da phân tích chưa ổn định'],
    face_smaller_than_preferred:['Face slightly smaller than preferred','Khuôn mặt hơi nhỏ so với khuyến nghị'],
    segmentation_variation:['Skin-region boundary variation','Biên vùng da có biến động'],
    lighting_not_comparable:['Lighting differs from baseline','Ánh sáng không tương đồng với mốc so sánh'],
    comparison_match_low:['Comparison match too low','Độ phù hợp để so sánh quá thấp']
  }

  const SENTENCES=new Map([
    ['Capture quality is too low for a reliable RGB scan.','Chất lượng ảnh chụp chưa đủ để thực hiện quét RGB đáng tin cậy.'],
    ['Please retake the photo.','Vui lòng chụp lại ảnh.'],
    ['This capture did not pass the quality gate.','Ảnh chụp này chưa đạt yêu cầu chất lượng.'],
    ['No frontal face detected. Use a well-lit, front-facing photo with one face visible.','Không phát hiện được khuôn mặt chính diện. Hãy dùng ảnh đủ sáng, chụp chính diện và chỉ có một khuôn mặt rõ ràng.'],
    ['Not enough usable facial skin pixels. Try a closer, evenly lit front-facing photo.','Không đủ vùng da khuôn mặt để phân tích. Hãy chụp gần hơn, chính diện và dùng ánh sáng đồng đều.'],
    ['Image is too small; use at least 160 px on the shortest side','Ảnh có độ phân giải quá thấp; cạnh ngắn nhất cần ít nhất 160 px.'],
    ['Move to brighter, soft frontal light.','Hãy chuyển sang ánh sáng phía trước mềm và sáng hơn.'],
    ['Reduce direct light or move away from strong highlights.','Giảm ánh sáng chiếu trực tiếp hoặc tránh các vùng phản sáng mạnh.'],
    ['Hold the phone steady and refocus before capture.','Giữ điện thoại ổn định và lấy nét lại trước khi chụp.'],
    ['Hold the phone steady for a moment and tap the face to refocus before capture.','Giữ điện thoại ổn định trong giây lát và chạm vào khuôn mặt để lấy nét lại trước khi chụp.'],
    ['Move closer so the face fills about 20–60% of the frame.','Đưa camera lại gần hơn để khuôn mặt chiếm khoảng 20–60% khung hình.'],
    ['Move closer so the full face is clearly visible and occupies more of the center of the frame.','Đưa camera lại gần hơn để toàn bộ khuôn mặt hiển thị rõ và chiếm nhiều hơn ở vùng giữa khung hình.'],
    ['For more repeatable tracking, move slightly closer next time while keeping the full face visible.','Để theo dõi lặp lại ổn định hơn, lần sau hãy đưa camera gần hơn một chút nhưng vẫn giữ toàn bộ khuôn mặt trong khung.'],
    ['Move the phone farther away so the full face is visible.','Đưa điện thoại ra xa hơn để thấy đầy đủ khuôn mặt.'],
    ['Center the face and keep the camera level.','Đưa khuôn mặt vào giữa và giữ camera cân bằng.'],
    ['Use more even frontal light to reduce deep shadows.','Dùng ánh sáng đều từ phía trước để giảm vùng tối sâu.'],
    ['Avoid direct glare and strong overhead light.','Tránh ánh sáng chói trực tiếp và nguồn sáng mạnh từ phía trên.'],
    ['Face the camera more directly and use even light on both sides.','Hướng khuôn mặt thẳng hơn về phía camera và dùng ánh sáng đều ở hai bên.'],
    ['Retake with sharper, more even lighting so the analyzed skin boundary is stable.','Chụp lại với ảnh rõ nét hơn và ánh sáng đồng đều hơn để biên vùng da phân tích ổn định.'],
    ['Use even frontal light and keep the full face centered so the outer facial skin boundary remains stable.','Dùng ánh sáng đều từ phía trước và giữ toàn bộ khuôn mặt ở giữa để biên ngoài vùng da khuôn mặt ổn định.'],
    ['Outer skin-boundary consistency was acceptable but not ideal; use even frontal light for repeat scans.','Độ ổn định của biên vùng da ở mức chấp nhận được nhưng chưa tối ưu; hãy dùng ánh sáng đều từ phía trước cho các lần quét lặp lại.'],
    ['Capture conditions are suitable. Reuse similar lighting, distance and angle for repeat scans.','Điều kiện chụp phù hợp. Hãy giữ ánh sáng, khoảng cách và góc chụp tương tự cho các lần quét lặp lại.'],
    ['Capture is usable. For repeat scans, keep lighting, distance and angle as consistent as possible.','Ảnh có thể sử dụng. Với các lần quét lặp lại, hãy giữ ánh sáng, khoảng cách và góc chụp nhất quán nhất có thể.'],
    ['Retake with steady focus, even frontal light, and the face centered in frame.','Hãy chụp lại với máy ổn định, lấy nét rõ, ánh sáng đều từ phía trước và khuôn mặt ở giữa khung hình.'],
    ['The previous saved scan remains in History, but it is intentionally not shown here as the result of this rejected attempt.','Lần quét đã lưu trước đó vẫn nằm trong Lịch sử, nhưng không được hiển thị ở đây vì lần chụp hiện tại chưa đạt yêu cầu.']
  ])

  function flagLabel(code){
    const pair=FLAGS[String(code||'')]
    if(pair)return isVi()?pair[1]:pair[0]
    if(isVi())return 'Cần kiểm tra chất lượng ảnh'
    const text=String(code||'Quality issue').replaceAll('_',' ')
    return text.charAt(0).toUpperCase()+text.slice(1)
  }

  function translateQualityText(value){
    let text=String(value??'')
    if(!text||!isVi())return text
    const ev=text.match(/^Lighting differs from the comparable baseline by ([0-9.]+) EV; retake in (brighter|dimmer) light\.$/)
    if(ev){
      const direction=ev[2]==='brighter'?'sáng hơn':'tối hơn'
      return `Ánh sáng chênh so với mốc so sánh ${ev[1]} EV; hãy chụp lại trong điều kiện ánh sáng ${direction}.`
    }
    for(const [en,vi] of SENTENCES){text=text.split(en).join(vi)}
    return text
  }

  let lastErrorCanonical=''
  const baseShowError=typeof showError==='function'?showError:null
  if(baseShowError){
    showError=function(msg=''){
      lastErrorCanonical=String(msg||'')
      return baseShowError(translateQualityText(lastErrorCanonical))
    }
    window.showError=showError
  }

  const baseRejected=typeof renderRejectedAttempt==='function'?renderRejectedAttempt:null
  if(baseRejected){
    renderRejectedAttempt=function(){
      baseRejected()
      const body=document.querySelector('#resultBody')
      const attempt=(typeof rejectedAttempt!=='undefined')?rejectedAttempt:null
      if(!body||!attempt)return
      const detail=(attempt?.detail&&typeof attempt.detail==='object')?attempt.detail:{}
      const guidance=Array.isArray(detail.quality_guidance)?detail.quality_guidance:[]
      const flags=Array.isArray(detail.quality_flags)?detail.quality_flags:[]
      const reason=detail.message||attempt?.message||'This capture did not pass the quality gate.'
      const notes=body.querySelectorAll(':scope > .scienceNote')
      if(notes[0]){
        notes[0].innerHTML=''
        const b=document.createElement('b');b.textContent=pick('Capture rejected — not saved.','Ảnh chụp chưa đạt — chưa được lưu.')
        notes[0].append(b,document.createTextNode(` ${translateQualityText(reason)}`))
      }
      const cards=body.querySelectorAll('.analysisMetrics .metric')
      if(cards[0]){
        cards[0].querySelector('span').textContent=pick('Status','Trạng thái')
        cards[0].querySelector('strong').textContent=pick('Rejected','Không đạt')
        cards[0].querySelector('small').textContent=pick('not added to History or trends','không được thêm vào Lịch sử hoặc xu hướng')
      }
      if(cards[1]){
        cards[1].querySelector('span').textContent=pick('Capture quality','Chất lượng ảnh chụp')
        const q=String(detail.capture_quality||'poor')
        cards[1].querySelector('strong').textContent=q==='good'?pick('Good','Tốt'):q==='usable'?pick('Usable','Có thể dùng'):pick('Poor','Chưa đạt')
        const score=Number.isFinite(detail.capture_quality_score)?`${detail.capture_quality_score}/100`:pick('Not measured','Chưa đo')
        cards[1].querySelector('small').textContent=pick(`score ${score}`,`điểm ${score}`)
      }
      if(cards[2]){
        cards[2].querySelector('span').textContent=pick('Issues','Vấn đề')
        const shown=flags.length?flags.map(flagLabel).join(', '):pick('See guidance','Xem hướng dẫn')
        cards[2].querySelector('strong').textContent=shown
        cards[2].querySelector('strong').title=flags.join(', ')
        cards[2].querySelector('small').textContent=pick('quality gate','kiểm tra chất lượng')
      }
      if(notes[1]){
        notes[1].innerHTML=''
        const b=document.createElement('b');b.textContent=pick('Retake guidance','Hướng dẫn chụp lại');notes[1].appendChild(b)
        if(guidance.length){
          const ul=document.createElement('ul');ul.style.margin='8px 0 0 18px';ul.style.padding='0'
          guidance.forEach(item=>{const li=document.createElement('li');li.textContent=translateQualityText(item);ul.appendChild(li)})
          notes[1].appendChild(ul)
        }else{
          const p=document.createElement('p');p.textContent=translateQualityText('Retake with steady focus, even frontal light, and the face centered in frame.');notes[1].appendChild(p)
        }
      }
      if(notes[2])notes[2].textContent=translateQualityText('The previous saved scan remains in History, but it is intentionally not shown here as the result of this rejected attempt.')
      const badge=document.querySelector('#compareBadge')
      if(badge&&!badge.classList.contains('hidden'))badge.textContent=pick('Capture rejected','Ảnh chụp chưa đạt')
      document.documentElement.dataset.rejectedStateI18nVersion=VERSION
    }
    window.renderRejectedAttempt=renderRejectedAttempt
  }

  function refresh(){
    if(lastErrorCanonical&&baseShowError)baseShowError(translateQualityText(lastErrorCanonical))
    try{if(typeof rejectedAttempt!=='undefined'&&rejectedAttempt&&typeof renderRejectedAttempt==='function')renderRejectedAttempt()}catch(_e){}
  }
  window.addEventListener('skin-ai:locale-change',()=>setTimeout(refresh,0))
  window.skinRejectedI18n={version:VERSION,translateQualityText,flagLabel,refresh}
  setTimeout(refresh,0)
})()