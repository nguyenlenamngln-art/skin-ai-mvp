// V1.6.0.1 — Complete Vietnamese / English dual-language runtime
// Presentation only. RGB V1.5.2, Capture Protocol V1.4, comparison scoring and study access remain unchanged.
(function(){
  const VERSION='1.6.0.1'
  const STORAGE_KEY='skin_ai_locale_v160'
  const SUPPORTED=['vi','en']
  const nodeState=new WeakMap()
  const attrState=new WeakMap()
  let locale=SUPPORTED.includes(localStorage.getItem(STORAGE_KEY))?localStorage.getItem(STORAGE_KEY):'vi'
  let scheduled=false

  const EN_VI={
    // App shell + navigation
    'Personal skin tracking':'Theo dõi da cá nhân','PERSONAL SKIN TRACKING':'THEO DÕI DA CÁ NHÂN',
    'Today':'Hôm nay','Progress':'Tiến trình','Scan':'Quét','Routine':'Chu trình','Journey':'Hành trình','+ Scan':'+ Quét',
    'Your skin today':'Làn da hôm nay','Your progress':'Tiến trình của bạn','Take a skin scan':'Quét da','Your routine':'Chu trình của bạn','Your journey':'Hành trình của bạn','Scan history':'Lịch sử quét',
    'Tracks your own visible-light skin signals over time. Not a diagnostic device.':'Theo dõi các tín hiệu da của chính bạn theo thời gian dưới ánh sáng khả kiến. Không phải thiết bị chẩn đoán.',
    'Checking engines…':'Đang kiểm tra hệ thống…','RGB ready · UV unavailable':'RGB sẵn sàng · UV chưa khả dụng',

    // Home / Today / Journey
    'LATEST SIGNAL':'TÍN HIỆU GẦN NHẤT','No scans yet':'Chưa có lần quét nào','Start with a Phone RGB or UV scan to create your baseline.':'Bắt đầu bằng một lần quét RGB điện thoại hoặc UV để tạo mốc ban đầu.',
    'Start scan':'Bắt đầu quét','SKIN INSIGHT':'GỢI Ý VỀ DA','Repeat scans under similar lighting, distance and angle to track change.':'Lặp lại lần quét với ánh sáng, khoảng cách và góc chụp tương tự để theo dõi thay đổi.',
    'Development insight based only on stored measurements.':'Gợi ý thử nghiệm chỉ dựa trên các chỉ số đã lưu.','90-DAY VIEW':'THEO DÕI 90 NGÀY','Signal trend':'Xu hướng tín hiệu',
    'Run at least two scans of the same type to see your trend.':'Cần ít nhất hai lần quét cùng loại để xem xu hướng.',
    'YOUR SKIN TODAY':'LÀN DA HÔM NAY','VISIBLE-LIGHT SIGNALS':'TÍN HIỆU ÁNH SÁNG KHẢ KIẾN','Your snapshot':'Tổng quan hôm nay',
    'Start with your baseline':'Bắt đầu với mốc ban đầu','Take one clear Phone RGB scan. Skin AI will use your own future scans—not population rankings—to show how your visible skin signals change over time.':'Hãy chụp một lần RGB điện thoại rõ nét. Skin AI sẽ dùng các lần quét sau của chính bạn — không dùng xếp hạng cộng đồng — để hiển thị thay đổi tín hiệu da nhìn thấy theo thời gian.',
    'This is your current personal baseline.':'Đây là mốc ban đầu hiện tại của riêng bạn.','Your personal reference':'Mốc tham chiếu cá nhân',
    'Create your baseline':'Tạo mốc ban đầu','Take your first Phone RGB scan. Future comparable scans will be measured against your own history.':'Hãy thực hiện lần quét RGB điện thoại đầu tiên. Các lần quét có thể so sánh sau này sẽ được đối chiếu với lịch sử của chính bạn.',
    'Take first scan':'Quét lần đầu','Ready for another comparison':'Sẵn sàng cho lần so sánh tiếp theo','Scan now':'Quét ngay',
    'A new scan can extend your personal timeline. Try to reuse similar lighting, distance and angle.':'Một lần quét mới sẽ bổ sung vào hành trình của bạn. Hãy cố gắng giữ ánh sáng, khoảng cách và góc chụp tương tự.',
    'You have a recent scan':'Bạn vừa có một lần quét gần đây','Your latest comparable scan is recent. Keep your next capture under similar lighting, distance and angle.':'Lần quét gần nhất có thể so sánh vẫn còn mới. Hãy giữ ánh sáng, khoảng cách và góc chụp tương tự cho lần tiếp theo.',
    'View progress':'Xem tiến trình','See progress':'Xem tiến trình','View journey':'Xem hành trình','Routine & notes':'Chu trình & ghi chú',
    'Personal visible-light tracking only. Results are not diagnoses or population rankings.':'Chỉ dùng để theo dõi cá nhân dưới ánh sáng khả kiến. Kết quả không phải chẩn đoán hay xếp hạng so với cộng đồng.',
    'MY JOURNEY':'HÀNH TRÌNH CỦA TÔI','Your photos and measurements in one simple timeline.':'Ảnh và các chỉ số của bạn trong một dòng thời gian đơn giản.','View scan':'Xem lần quét',
    'Your timeline starts with your first scan':'Dòng thời gian bắt đầu từ lần quét đầu tiên','Once you have comparable scans, this page becomes a visual record of your skin over time.':'Khi có các lần quét có thể so sánh, trang này sẽ trở thành nhật ký hình ảnh về làn da của bạn theo thời gian.',
    'Latest':'Mới nhất','Baseline':'Mốc ban đầu','No comparison':'Chưa có so sánh','Higher':'Cao hơn','Lower':'Thấp hơn','Stable':'Ổn định',
    'Redness':'Đỏ da','Pigmentation':'Sắc tố','Pigment':'Sắc tố','Texture':'Kết cấu','Redness area':'Vùng đỏ','Pigmented area':'Vùng sắc tố',
    'Visible redness area':'Vùng đỏ nhìn thấy','Visible pigmentation area':'Vùng sắc tố nhìn thấy','Visible-light texture signal':'Tín hiệu kết cấu dưới ánh sáng khả kiến',
    'Good for comparison':'Phù hợp để so sánh','Saved, not used for trends':'Đã lưu, không dùng cho xu hướng','No scan':'Chưa có lần quét',

    // Progress / comparison
    'FROM YOUR BASELINE':'SO VỚI MỐC BAN ĐẦU','YOUR PROGRESS':'TIẾN TRÌNH CỦA BẠN','BEFORE & AFTER':'TRƯỚC & SAU','Drag to compare':'Kéo để so sánh',
    'Comparison match':'Độ phù hợp để so sánh','Strong':'Rất phù hợp','Usable':'Có thể dùng','Review':'Cần xem lại',
    'Framing and lighting are similar enough for personal trend comparison.':'Khung hình và ánh sáng đủ tương đồng để so sánh xu hướng cá nhân.',
    'Usable for comparison, but older scans lack full framing metadata; confidence is intentionally capped.':'Có thể dùng để so sánh, nhưng các lần quét cũ thiếu dữ liệu khung hình đầy đủ nên mức tin cậy được giới hạn có chủ đích.',
    'This scan is valid on its own, but capture differences make trend comparison less reliable.':'Lần quét này vẫn hợp lệ khi xem riêng, nhưng khác biệt khi chụp làm việc so sánh xu hướng kém tin cậy hơn.',
    'Changes use the values shown above, so displayed endpoints and displayed deltas always agree. Higher/lower is descriptive, not good/bad.':'Thay đổi được tính từ chính các giá trị hiển thị ở trên nên số đầu-cuối và mức chênh luôn khớp nhau. Cao hơn/thấp hơn chỉ mang tính mô tả, không đồng nghĩa tốt/xấu.',
    'Changes describe your own comparable RGB scans. Higher/lower is descriptive, not good/bad.':'Các thay đổi mô tả những lần quét RGB có thể so sánh của chính bạn. Cao hơn/thấp hơn chỉ mang tính mô tả, không đồng nghĩa tốt/xấu.',
    'TREND':'XU HƯỚNG','Your change from baseline':'Thay đổi so với mốc ban đầu','Your visible signals over time':'Tín hiệu nhìn thấy theo thời gian',
    'Change from displayed baseline':'Thay đổi so với mốc hiển thị','No meaningful change at the displayed precision':'Không có thay đổi đáng kể ở độ chính xác đang hiển thị',
    'Your visual comparison will appear here':'So sánh hình ảnh sẽ xuất hiện tại đây','Take another quality-eligible RGB scan to compare it with your baseline.':'Hãy thực hiện thêm một lần quét RGB đạt chất lượng để so sánh với mốc ban đầu.',
    'Take another scan':'Quét thêm một lần','Your baseline is ready':'Mốc ban đầu đã sẵn sàng','Your baseline is saved':'Mốc ban đầu đã được lưu','WHAT HAPPENS NEXT':'TIẾP THEO LÀ GÌ',
    'Take another comparable scan later to unlock before/after comparison and trend charts.':'Thực hiện thêm một lần quét có thể so sánh để mở khóa so sánh trước/sau và biểu đồ xu hướng.',
    'Not enough data yet':'Chưa đủ dữ liệu','Take at least two comparable scans':'Cần ít nhất hai lần quét có thể so sánh',
    'Photos are shown as captured. Apparent visual differences can also reflect lighting, angle or distance.':'Ảnh được hiển thị theo bản chụp gốc. Khác biệt nhìn thấy cũng có thể do ánh sáng, góc chụp hoặc khoảng cách.',
    'Photos are face-centered for easier visual comparison. Lighting, expression and head angle can still affect apparent differences.':'Ảnh được căn giữa theo khuôn mặt để dễ so sánh hơn. Ánh sáng, biểu cảm và góc đầu vẫn có thể ảnh hưởng đến khác biệt nhìn thấy.',
    'Photos are normalized to the same facial geometry, with a small residual alignment when the image pattern is stable. Pose, expression and perspective can still create differences.':'Ảnh được chuẩn hóa theo cùng hình học khuôn mặt và tinh chỉnh căn chỉnh nhẹ khi mẫu hình ảnh đủ ổn định. Tư thế, biểu cảm và phối cảnh vẫn có thể tạo khác biệt.',
    'Photos are normalized to a shared mobile viewport so both scans use the same face-centered crop. Pose, expression and perspective can still create visual differences.':'Ảnh được chuẩn hóa vào cùng một khung nhìn trên điện thoại để hai lần quét dùng chung vùng cắt căn giữa khuôn mặt. Tư thế, biểu cảm và phối cảnh vẫn có thể tạo khác biệt hình ảnh.',
    'Both photos use one shared face-centered viewport for visual comparison. Small residual alignment is applied only when stable; pose, expression and perspective can still differ.':'Cả hai ảnh dùng chung một khung nhìn căn giữa khuôn mặt để so sánh trực quan. Chỉ tinh chỉnh căn chỉnh nhẹ khi đủ ổn định; tư thế, biểu cảm và phối cảnh vẫn có thể khác nhau.',

    // Routine / diary
    'MORNING':'BUỔI SÁNG','AM routine':'Chu trình buổi sáng','EVENING':'BUỔI TỐI','PM routine':'Chu trình buổi tối','Save routine':'Lưu chu trình',
    'One product or step per line.':'Mỗi dòng một sản phẩm hoặc một bước.','Use consistent names so you can remember what changed.':'Dùng tên nhất quán để dễ nhớ những gì đã thay đổi.',
    'SKIN DIARY':'NHẬT KÝ DA','Add context for today':'Ghi chú cho hôm nay','Optional notes can help you remember what was different around a scan. They are saved on this device only.':'Ghi chú tùy chọn giúp bạn nhớ điều gì khác biệt quanh thời điểm quét. Ghi chú chỉ được lưu trên thiết bị này.',
    'New product':'Sản phẩm mới','Outdoor / sun':'Ngoài trời / nắng','Shaving':'Cạo râu','Makeup':'Trang điểm','Poor sleep':'Ngủ kém','Other':'Khác',
    "Save today's note":'Lưu ghi chú hôm nay','RECENT NOTES':'GHI CHÚ GẦN ĐÂY','Remember what changed':'Ghi lại những thay đổi','No diary notes yet.':'Chưa có ghi chú nào.','Personal note':'Ghi chú cá nhân',

    // Scan shell / capture
    'Tester access':'Truy cập thử nghiệm','Use study code':'Dùng mã thử nghiệm','Take a clear photo':'Chụp ảnh rõ nét','Open camera':'Mở camera',
    'Advanced scan settings':'Cài đặt quét nâng cao','Hide advanced settings':'Ẩn cài đặt nâng cao','Or upload a front-facing photo':'Hoặc tải ảnh chụp chính diện',
    'Neutral light · no beauty filters · up to 20 MB':'Ánh sáng trung tính · không dùng bộ lọc làm đẹp · tối đa 20 MB','Choose image':'Chọn ảnh',
    'Capture or upload a front-facing photo':'Chụp hoặc tải ảnh chính diện','Natural/neutral light · no beauty filters · up to 20 MB':'Ánh sáng tự nhiên/trung tính · không dùng bộ lọc làm đẹp · tối đa 20 MB',
    'Built-in webcam or phone camera supported.':'Hỗ trợ webcam tích hợp hoặc camera điện thoại.','Live guidance checks lighting, sharpness and stability.':'Hướng dẫn trực tiếp kiểm tra ánh sáng, độ nét và độ ổn định.',
    'Camera guidance checks lighting, sharpness and stability before analysis.':'Hướng dẫn camera kiểm tra ánh sáng, độ nét và độ ổn định trước khi phân tích.',
    'Face should fill roughly 20–60% of the frame.':'Khuôn mặt nên chiếm khoảng 20–60% khung hình.','Use the same lighting, distance and angle for repeat scans.':'Giữ ánh sáng, khoảng cách và góc chụp tương tự cho các lần quét lặp lại.',
    'UV fluorescence':'Huỳnh quang UV','Phone RGB':'RGB điện thoại','Upload UV fluorescence image':'Tải ảnh huỳnh quang UV','Upload or capture UV image':'Tải lên hoặc chụp ảnh UV',
    'From a supported UV fluorescence device · PNG or JPEG · up to 20 MB':'Từ thiết bị huỳnh quang UV được hỗ trợ · PNG hoặc JPEG · tối đa 20 MB','PNG or JPEG · up to 20 MB':'PNG hoặc JPEG · tối đa 20 MB',
    'Artifact pixels are excluded, never inpainted.':'Các điểm ảnh nhiễu bị loại bỏ, không được nội suy.','Repeat scans under similar capture conditions.':'Lặp lại lần quét trong điều kiện chụp tương tự.',

    // Capture guidance V2
    'CAPTURE GUIDANCE V2':'HƯỚNG DẪN CHỤP V2','Improve repeatability before analysis':'Tăng độ lặp lại trước khi phân tích','Use camera':'Dùng camera',
    'Position region':'Đặt vùng chụp','Lighting':'Ánh sáng','Sharpness':'Độ nét','Stability':'Độ ổn định','Position':'Vị trí','Visual guide':'Hướng dẫn trực quan',
    'Checking…':'Đang kiểm tra…','Cancel':'Hủy','Capture photo':'Chụp ảnh','Good':'Tốt','Adjust':'Điều chỉnh','Poor':'Kém','Hold steady':'Giữ máy ổn định','Refocus':'Lấy nét lại','Too much movement':'Di chuyển quá nhiều',
    'Center the full face in the guide. Keep the phone level and use even frontal light.':'Đặt toàn bộ khuôn mặt vào khung hướng dẫn. Giữ điện thoại cân bằng và dùng ánh sáng đều từ phía trước.',
    'Lighting, sharpness and stability are browser-side estimates. Position and distance remain visual guidance; the backend performs the final quality check.':'Ánh sáng, độ nét và độ ổn định chỉ là ước tính trên trình duyệt. Vị trí và khoảng cách là hướng dẫn trực quan; hệ thống máy chủ thực hiện kiểm tra chất lượng cuối cùng.',
    'Camera access was not available. You can still choose an image from your device.':'Không thể truy cập camera. Bạn vẫn có thể chọn ảnh từ thiết bị.',
    'Low image resolution':'Độ phân giải ảnh thấp','Use a higher-resolution capture so small skin features are not lost.':'Hãy dùng ảnh có độ phân giải cao hơn để không làm mất các chi tiết da nhỏ.',
    'Lighting outside preferred range':'Ánh sáng ngoài khoảng phù hợp','Use more even illumination and avoid very dark or blown-out areas.':'Dùng ánh sáng đều hơn và tránh vùng quá tối hoặc cháy sáng.',
    'Lighting could be more even':'Ánh sáng có thể đều hơn','Try more neutral, even light before capture.':'Hãy thử ánh sáng trung tính và đều hơn trước khi chụp.',
    'Image may be blurry':'Ảnh có thể bị mờ','Refocus and hold the phone steady.':'Lấy nét lại và giữ điện thoại ổn định.',
    'Sharpness is borderline':'Độ nét chưa tối ưu','Hold steady and refocus before capture.':'Giữ máy ổn định và lấy nét lại trước khi chụp.',
    'PRE-CAPTURE CHECK':'KIỂM TRA TRƯỚC KHI CHỤP','Ready for backend quality check':'Sẵn sàng kiểm tra chất lượng trên máy chủ','exposure and sharpness look acceptable.':'độ sáng và độ nét ở mức phù hợp.',
    'Retake recommended':'Nên chụp lại','Capture can be improved':'Ảnh chụp có thể cải thiện','Choose another image':'Chọn ảnh khác','Analyze anyway':'Vẫn phân tích',
    'These browser checks are advisory. The server-side RGB/UV quality gates remain authoritative.':'Các kiểm tra trên trình duyệt chỉ mang tính hướng dẫn. Kiểm tra chất lượng RGB/UV phía máy chủ vẫn là tiêu chuẩn cuối cùng.',

    // Result experience
    'YOUR RESULT':'KẾT QUẢ CỦA BẠN','Latest scan':'Lần quét gần nhất','Current attempt':'Lần thử hiện tại','Capture rejected':'Ảnh chụp chưa đạt',
    'Visible-light skin signals':'Tín hiệu da dưới ánh sáng khả kiến','These measurements describe this photo and are designed primarily for tracking your own changes over time.':'Các chỉ số này mô tả ảnh hiện tại và chủ yếu dùng để theo dõi thay đổi của chính bạn theo thời gian.',
    'Result experience V1.5.5':'Trải nghiệm kết quả V1.5.5','of analyzed skin':'trên vùng da được phân tích','Texture signal':'Tín hiệu kết cấu','visible-light texture proxy':'chỉ số đại diện kết cấu dưới ánh sáng khả kiến',
    'CHANGE SINCE LAST COMPARABLE SCAN':'THAY ĐỔI SO VỚI LẦN QUÉT CÓ THỂ SO SÁNH GẦN NHẤT','Compared only with a same-version, quality-eligible RGB scan.':'Chỉ so sánh với lần quét RGB cùng phiên bản và đạt điều kiện chất lượng.',
    'Higher than your previous comparable scan':'Cao hơn so với lần quét có thể so sánh trước','Lower than your previous comparable scan':'Thấp hơn so với lần quét có thể so sánh trước','Stable than your previous comparable scan':'Ổn định so với lần quét có thể so sánh trước',
    'This scan is your baseline':'Lần quét này là mốc ban đầu của bạn','This scan is saved for review':'Lần quét này được lưu để xem lại',
    'Repeat your scan under similar lighting, distance and angle to begin tracking change.':'Lặp lại lần quét với ánh sáng, khoảng cách và góc chụp tương tự để bắt đầu theo dõi thay đổi.',
    'This capture is not used for longitudinal changes. Follow the scan-quality guidance and retake when possible.':'Ảnh chụp này không được dùng để tính thay đổi theo thời gian. Hãy làm theo hướng dẫn chất lượng và chụp lại khi có thể.',
    'New baseline after analysis update':'Mốc ban đầu mới sau cập nhật phân tích','Future scans using the same analysis version can be compared with this result.':'Các lần quét sau dùng cùng phiên bản phân tích có thể được so sánh với kết quả này.',
    'Not used for trend comparison':'Không dùng để so sánh xu hướng','This capture passed the current quality gate and can be compared with future same-version scans.':'Ảnh chụp này đã đạt kiểm tra chất lượng hiện tại và có thể so sánh với các lần quét sau dùng cùng phiên bản.',
    'You can review this result, but the app excludes it from longitudinal deltas and trends.':'Bạn vẫn có thể xem kết quả này, nhưng ứng dụng loại nó khỏi thay đổi và xu hướng theo thời gian.',
    'WHAT WE DETECTED':'NHỮNG GÌ ĐÃ PHÁT HIỆN','Switch views to inspect the analyzed skin region and visible-light signal maps.':'Chuyển chế độ xem để kiểm tra vùng da được phân tích và các bản đồ tín hiệu dưới ánh sáng khả kiến.',
    'Original':'Ảnh gốc','Skin region':'Vùng da','Redness map':'Bản đồ đỏ da','Pigmentation map':'Bản đồ sắc tố','Combined':'Kết hợp',
    'local redness':'vùng đỏ cục bộ','local pigmentation':'sắc tố cục bộ','analyzed skin boundary':'ranh giới vùng da phân tích',
    'SCAN QUALITY':'CHẤT LƯỢNG LẦN QUÉT','Capture quality':'Chất lượng ảnh chụp','For your next scan':'Cho lần quét tiếp theo',
    'Capture conditions are suitable. Reuse similar lighting, distance and angle for repeat scans.':'Điều kiện chụp phù hợp. Hãy dùng ánh sáng, khoảng cách và góc chụp tương tự cho các lần quét tiếp theo.',
    'Technical details':'Chi tiết kỹ thuật','Advanced details':'Chi tiết nâng cao','Measurement and scan-quality details':'Chi tiết chỉ số và chất lượng lần quét','For research and validation review':'Dành cho xem xét nghiên cứu và xác thực',
    'RGB engine':'Bộ máy RGB','production measurement engine':'bộ máy đo lường đang dùng','Capture protocol':'Giao thức chụp','Measurement confidence':'Độ tin cậy phép đo','High-confidence skin':'Vùng da độ tin cậy cao','Pigmentation-ready skin':'Vùng da phù hợp đo sắc tố',
    'Framing':'Khung hình','Segmentation':'Phân vùng','Outer-boundary stability':'Độ ổn định biên ngoài','Measured-skin support':'Mức hỗ trợ vùng da đo','Regional confidence':'Độ tin cậy theo vùng','Regional trend gate':'Điều kiện xu hướng theo vùng','Measurement warnings':'Cảnh báo phép đo',
    'Not measured':'Chưa đo','Regional confidence unavailable for this scan.':'Không có dữ liệu độ tin cậy theo vùng cho lần quét này.','No regions currently eligible':'Hiện chưa có vùng nào đủ điều kiện',
    'Research measurement.':'Phép đo nghiên cứu.','Research measurement':'Phép đo nghiên cứu','Phone RGB research measurement.':'Phép đo nghiên cứu bằng RGB điện thoại.',
    'These are relative visible-light proxies for longitudinal tracking. They are not diagnoses and are not equivalent to polarized or UV imaging.':'Đây là các chỉ số tương đối dưới ánh sáng khả kiến để theo dõi theo thời gian. Chúng không phải chẩn đoán và không tương đương ảnh phân cực hoặc UV.',
    'Phone RGB results are relative visible-light proxies for personal longitudinal tracking. They are not diagnoses and are not substitutes for polarized, UV, or clinical skin assessment.':'Kết quả RGB điện thoại là các chỉ số tương đối dưới ánh sáng khả kiến để theo dõi cá nhân theo thời gian. Chúng không phải chẩn đoán và không thay thế đánh giá da bằng ảnh phân cực, UV hoặc đánh giá lâm sàng.',
    'Artifact pixels are excluded rather than reconstructed. Compare scans only when capture conditions are similar.':'Các điểm ảnh nhiễu bị loại bỏ thay vì tái tạo. Chỉ so sánh các lần quét khi điều kiện chụp tương tự.',
    'Choose a scan type, then capture or upload an image.':'Chọn loại quét, sau đó chụp hoặc tải ảnh lên.',
    'Status':'Trạng thái','Rejected':'Không đạt','Issues':'Vấn đề','Retake guidance':'Hướng dẫn chụp lại','not added to History or trends':'không được thêm vào lịch sử hoặc xu hướng','quality gate':'kiểm tra chất lượng','See guidance':'Xem hướng dẫn',
    'Retake with steady focus, even frontal light, and the face centered in frame.':'Chụp lại với máy ổn định, ánh sáng đều từ phía trước và khuôn mặt ở giữa khung hình.',

    // Study mode / access
    'TESTER STUDY MODE':'CHẾ ĐỘ NGHIÊN CỨU THỬ NGHIỆM','Repeatable RGB capture study':'Nghiên cứu độ lặp lại khi chụp RGB','Study mode':'Chế độ nghiên cứu','Study notice':'Thông báo nghiên cứu',
    'This research beta records your pseudonymous tester code, scan-session ID, capture time, image, and RGB analysis so repeatability can be evaluated. It is not a medical or diagnostic assessment.':'Bản thử nghiệm nghiên cứu này lưu mã người thử ẩn danh, ID phiên quét, thời điểm chụp, hình ảnh và phân tích RGB để đánh giá độ lặp lại. Đây không phải đánh giá y tế hay chẩn đoán.',
    'Use only the tester ID and access code provided by the study organizer. Do not enter your name, email address, phone number, or other identifying information.':'Chỉ dùng ID người thử và mã truy cập do người tổ chức nghiên cứu cung cấp. Không nhập tên, email, số điện thoại hoặc thông tin nhận dạng khác.',
    'I have read this study notice and agree to submit this test capture.':'Tôi đã đọc thông báo nghiên cứu này và đồng ý gửi ảnh chụp thử nghiệm.',
    'This acknowledgment supports this engineering beta workflow; it is not a substitute for any formal research consent process that may be required.':'Xác nhận này phục vụ quy trình thử nghiệm kỹ thuật và không thay thế quy trình đồng thuận nghiên cứu chính thức nếu được yêu cầu.',
    'Tester ID':'ID người thử','Access code':'Mã truy cập','Provided by study organizer':'Do người tổ chức nghiên cứu cung cấp','Sign in & start session':'Đăng nhập & bắt đầu phiên','Exit study mode':'Thoát chế độ nghiên cứu',
    'Enter the assigned tester ID and access code to begin.':'Nhập ID người thử và mã truy cập được cấp để bắt đầu.','Study session active':'Phiên nghiên cứu đang hoạt động','Study capture saved':'Ảnh nghiên cứu đã được lưu','Start another study session':'Bắt đầu phiên nghiên cứu khác','Start study session':'Bắt đầu phiên nghiên cứu',
    'Take one front-facing RGB capture below. Only your study records are available in this signed-in session.':'Chụp một ảnh RGB chính diện bên dưới. Trong phiên đăng nhập này chỉ có hồ sơ nghiên cứu của bạn được hiển thị.',
    'Your result is available above. Start another session for a repeat capture.':'Kết quả của bạn hiển thị ở trên. Hãy bắt đầu phiên khác để chụp lặp lại.',
    'Start a study session to attach a unique session ID to the next RGB capture.':'Bắt đầu phiên nghiên cứu để gắn ID phiên duy nhất cho lần chụp RGB tiếp theo.',
    "Enter the assigned tester ID (2–32 letters, numbers, '-' or '_').":"Nhập ID người thử được cấp (2–32 ký tự chữ, số, '-' hoặc '_').",
    'Read and acknowledge the study notice before starting a study session.':'Đọc và xác nhận thông báo nghiên cứu trước khi bắt đầu phiên.','Enter the access code provided by the study organizer.':'Nhập mã truy cập do người tổ chức nghiên cứu cung cấp.','Finish the active session before starting another tester session.':'Hoàn tất phiên đang hoạt động trước khi bắt đầu phiên người thử khác.',

    // Tracking context / dashboard
    'TRACKING CONTEXT':'NGỮ CẢNH THEO DÕI','Who and where are you scanning?':'Bạn đang quét cho ai và vùng nào?','+ Profile':'+ Hồ sơ','Subject':'Đối tượng','Region':'Vùng',
    'Analysis only / no subject':'Chỉ phân tích / không chọn đối tượng','Analysis only / no region':'Chỉ phân tích / không chọn vùng','Choose both to enable longitudinal comparison. Leave both blank for analysis-only.':'Chọn cả hai để bật so sánh theo thời gian. Để trống cả hai nếu chỉ muốn phân tích.',
    'All subjects':'Tất cả đối tượng','All regions':'Tất cả vùng','All modalities':'Tất cả phương thức','LONGITUDINAL DASHBOARD':'BẢNG THEO DÕI DÀI HẠN','Profile & region view':'Xem theo hồ sơ & vùng',
    'Saved scans':'Lần quét đã lưu','matching current filters':'khớp bộ lọc hiện tại','Trend eligible':'Đủ điều kiện xu hướng','structured + quality compatible':'đúng cấu trúc + tương thích chất lượng','Subjects':'Đối tượng','represented in view':'có trong chế độ xem','Regions':'Vùng',
    'No scans match these filters yet.':'Chưa có lần quét nào khớp các bộ lọc này.','Baseline only':'Chỉ có mốc ban đầu','Latest in view':'Mới nhất trong chế độ xem','Scans are saved, but none are longitudinally eligible under these filters yet.':'Đã có lần quét được lưu nhưng chưa có lần nào đủ điều kiện theo dõi dài hạn với bộ lọc hiện tại.',
    'Tracking identity.':'Danh tính theo dõi.','Analysis-only identity.':'Danh tính chỉ phân tích.','This scan has no structured subject/region assignment, so it is excluded from longitudinal profile trends.':'Lần quét này chưa được gán đối tượng/vùng có cấu trúc nên bị loại khỏi xu hướng hồ sơ theo thời gian.',
    'Longitudinal comparison is restricted to this exact profile/region series plus compatible analysis versions.':'So sánh theo thời gian chỉ giới hạn trong đúng chuỗi hồ sơ/vùng này và các phiên bản phân tích tương thích.',
    'Unassigned':'Chưa gán','Legacy / unspecified region':'Vùng cũ / chưa xác định','Full face':'Toàn mặt','Skin closeup':'Cận cảnh da','Forehead':'Trán','Left cheek':'Má trái','Right cheek':'Má phải','Nose':'Mũi','Chin':'Cằm',
    'forehead':'trán','left cheek':'má trái','right cheek':'má phải','nose':'mũi','chin':'cằm','center face':'giữa mặt',

    // Guided session
    'GUIDED SESSION':'PHIÊN HƯỚNG DẪN','Capture regions in one visit':'Chụp các vùng trong một lần','Start session':'Bắt đầu phiên','UV sessions guide 5 regions. Phone RGB sessions use one full-face capture.':'Phiên UV hướng dẫn 5 vùng. Phiên RGB điện thoại dùng một ảnh toàn mặt.',
    'Choose a subject profile before starting a guided session.':'Chọn hồ sơ đối tượng trước khi bắt đầu phiên hướng dẫn.','Session identity is locked for this completed visit.':'Danh tính phiên đã được khóa cho lần chụp đã hoàn tất.',
    'View summary':'Xem tổng kết','Start new session':'Bắt đầu phiên mới','Return to overview':'Quay lại tổng quan','Session active':'Phiên đang hoạt động','Session complete':'Phiên đã hoàn tất','All required regions are saved.':'Tất cả vùng yêu cầu đã được lưu.',
    'Use the same UV device, distance and angle for every region.':'Dùng cùng thiết bị UV, khoảng cách và góc chụp cho mọi vùng.','Front-facing full-face photo · neutral light · no beauty filters.':'Ảnh toàn mặt chính diện · ánh sáng trung tính · không bộ lọc làm đẹp.',

    // Misc
    'NEW MILESTONE':'MỐC MỚI','NEXT MILESTONE':'MỐC TIẾP THEO','Add your second comparable scan':'Thêm lần quét thứ hai có thể so sánh','With two scans, Journey can start showing visible changes from your personal baseline.':'Khi có hai lần quét, Hành trình có thể bắt đầu hiển thị thay đổi nhìn thấy so với mốc ban đầu của bạn.',
    'Not a diagnosis':'Không phải chẩn đoán','legacy':'phiên bản cũ'
  }

  const VI_EN=Object.fromEntries(Object.entries(EN_VI).map(([en,vi])=>[vi,en]))
  const PLACEHOLDER={
    'Optional note, e.g. started a new cleanser today':'Ghi chú tùy chọn, ví dụ: hôm nay bắt đầu dùng sữa rửa mặt mới',
    'Provided by study organizer':'Do người tổ chức nghiên cứu cung cấp'
  }
  const MONTHS={Jan:'Thg 1',Feb:'Thg 2',Mar:'Thg 3',Apr:'Thg 4',May:'Thg 5',Jun:'Thg 6',Jul:'Thg 7',Aug:'Thg 8',Sep:'Thg 9',Oct:'Thg 10',Nov:'Thg 11',Dec:'Thg 12'}
  const WEEKDAYS={Sun:'CN',Mon:'Th 2',Tue:'Th 3',Wed:'Th 4',Thu:'Th 5',Fri:'Th 6',Sat:'Th 7'}

  function dateVi(text){
    let out=text
    out=out.replace(/\b(Sun|Mon|Tue|Wed|Thu|Fri|Sat),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b/g,(_,d,m,day)=>`${WEEKDAYS[d]}, ${day} ${MONTHS[m]}`)
    out=out.replace(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b/g,(_,m,day)=>`${day} ${MONTHS[m]}`)
    return out
  }

  function dynamicVi(en){
    if(EN_VI[en])return EN_VI[en]
    let m
    if((m=en.match(/^YOUR SKIN TODAY · V(.+)$/)))return `LÀN DA HÔM NAY · V${m[1]}`
    if((m=en.match(/^TESTER STUDY MODE · V(.+)$/)))return `CHẾ ĐỘ NGHIÊN CỨU THỬ NGHIỆM · V${m[1]}`
    if((m=en.match(/^(\d+) comparable scans?$/)))return `${m[1]} lần quét có thể so sánh`
    if((m=en.match(/^(\d+) comparable (scan|scans)$/)))return `${m[1]} lần quét có thể so sánh`
    if((m=en.match(/^(\d+) scans?$/)))return `${m[1]} lần quét`
    if((m=en.match(/^(\d+) scans? · start to latest$/)))return `${m[1]} lần quét · từ đầu đến gần nhất`
    if((m=en.match(/^(\d+) saved scans?$/)))return `${m[1]} lần quét đã lưu`
    if((m=en.match(/^(\d+) of (\d+) saved scans?$/)))return `${m[1]} / ${m[2]} lần quét đã lưu`
    if((m=en.match(/^(\d+) issue(s)?$/)))return `${m[1]} vấn đề`
    if((m=en.match(/^Compared with your baseline from (.+)\.$/)))return `So với mốc ban đầu ngày ${dateVi(m[1])}.`
    if((m=en.match(/^Strong · (\d+)\/100$/)))return `Rất phù hợp · ${m[1]}/100`
    if((m=en.match(/^Usable · (\d+)\/100$/)))return `Có thể dùng · ${m[1]}/100`
    if((m=en.match(/^Review · (\d+)\/100$/)))return `Cần xem lại · ${m[1]}/100`
    if((m=en.match(/^([+-]?\d+(?:\.\d+)?) pp vs previous$/)))return `${m[1]} điểm % so với lần trước`
    if((m=en.match(/^([+-]?\d+(?:\.\d+)?) pp vs first$/)))return `${m[1]} điểm % so với lần đầu`
    if((m=en.match(/^(↑|↓|→)\s*([+-]?\d+(?:\.\d+)?) pp$/)))return `${m[1]} ${m[2]} điểm %`
    if((m=en.match(/^(↑|↓|→)\s*([+-]?\d+(?:\.\d+)?)$/)))return `${m[1]} ${m[2]}`
    if((m=en.match(/^([<>]?\d+(?:\.\d+)?) pp from baseline$/)))return `${m[1]} điểm % so với mốc ban đầu`
    if((m=en.match(/^([+-]?\d+(?:\.\d+)?) from baseline$/)))return `${m[1]} so với mốc ban đầu`
    if(en==='Stable from baseline')return 'Ổn định so với mốc ban đầu'
    if((m=en.match(/^(↑|↓)\s*([\d.]+) pp redness area$/)))return `${m[1]} ${m[2]} điểm % vùng đỏ`
    if(en==='RGB stable vs previous')return 'RGB ổn định so với lần trước'
    if((m=en.match(/^([↑↓])\s*(\d+) spots vs previous$/)))return `${m[1]} ${m[2]} điểm huỳnh quang so với lần trước`
    if((m=en.match(/^([\d.]+)% redness$/)))return `${m[1]}% đỏ da`
    if((m=en.match(/^(\d+) fluorescent spots$/)))return `${m[1]} điểm huỳnh quang`
    if((m=en.match(/^(\d+) comparable scan(s)? · (.+)$/)))return `${m[1]} lần quét có thể so sánh · ${dynamicVi(m[3])}`
    if((m=en.match(/^Tester (.+) · session (.+)$/)))return `Người thử ${m[1]} · phiên ${m[2]}`
    if((m=en.match(/^Tester (.+) signed in$/)))return `Người thử ${m[1]} đã đăng nhập`
    if((m=en.match(/^All (\d+) captures? saved$/)))return `Đã lưu đủ ${m[1]} ảnh chụp`
    if((m=en.match(/^(\d+) captures? saved under one session\.$/)))return `${m[1]} ảnh chụp đã được lưu trong cùng một phiên.`
    if((m=en.match(/^Next: (.+)$/)))return `Tiếp theo: ${dynamicVi(m[1])}`
    if((m=en.match(/^(\d+) of (\d+) regions complete\. Upload the current region below\.$/)))return `Đã hoàn tất ${m[1]}/${m[2]} vùng. Tải ảnh vùng hiện tại ở bên dưới.`
    if((m=en.match(/^Capture (.+)$/)))return `Chụp ${dynamicVi(m[1])}`
    if((m=en.match(/^Eligible: (.+)$/)))return `Đủ điều kiện: ${m[1].split(', ').map(dynamicVi).join(', ')}`
    if((m=en.match(/^Held: (.+)$/)))return `Tạm giữ: ${m[1].split(', ').map(dynamicVi).join(', ')}`
    let out=dateVi(en)
    if(/Thg \d/.test(out) && out.includes(' vs '))out=out.replace(' vs ',' so với ')
    return out
  }

  function canonicalEnglish(core){
    if(EN_VI[core])return core
    if(VI_EN[core])return VI_EN[core]
    return core
  }

  function translatedCore(en){return locale==='vi'?dynamicVi(en):en}
  function translateNode(node){
    if(node.nodeType!==Node.TEXT_NODE)return
    const parent=node.parentElement
    if(!parent||['SCRIPT','STYLE','TEXTAREA'].includes(parent.tagName))return
    // User-entered diary body is content, not interface copy.
    if(parent.closest('.pjNoteRow p'))return
    const current=node.data
    const leading=current.match(/^\s*/)?.[0]||''
    const trailing=current.match(/\s*$/)?.[0]||''
    const core=current.trim()
    if(!core)return
    let state=nodeState.get(node)
    if(!state){state={en:canonicalEnglish(core),last:null};nodeState.set(node,state)}
    else if(core!==state.last){
      const expected=translatedCore(state.en)
      if(core!==expected)state.en=canonicalEnglish(core)
    }
    const targetCore=translatedCore(state.en)
    state.last=targetCore
    const target=`${leading}${targetCore}${trailing}`
    if(current!==target)node.data=target
  }

  function attrMap(el,attr){
    let state=attrState.get(el)
    if(!state){state={};attrState.set(el,state)}
    const current=el.getAttribute(attr)||''
    const slot=state[attr]||{en:canonicalEnglish(current),last:null}
    if(current!==slot.last){
      const expected=locale==='vi'?(PLACEHOLDER[slot.en]||dynamicVi(slot.en)):slot.en
      if(current!==expected)slot.en=canonicalEnglish(current)
    }
    const target=locale==='vi'?(PLACEHOLDER[slot.en]||dynamicVi(slot.en)):slot.en
    slot.last=target;state[attr]=slot
    if(current!==target)el.setAttribute(attr,target)
  }

  function translateTree(root=document.body){
    if(!root)return
    if(root.nodeType===Node.TEXT_NODE){translateNode(root);return}
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT)
    let node
    while((node=walker.nextNode()))translateNode(node)
    root.querySelectorAll?.('[placeholder]').forEach(el=>attrMap(el,'placeholder'))
    root.querySelectorAll?.('[aria-label]').forEach(el=>{
      if(el.closest('.languageSwitchV160'))return
      attrMap(el,'aria-label')
    })
    root.querySelectorAll?.('[title]').forEach(el=>attrMap(el,'title'))
  }

  const STRUCTURE={
    vi:{home:'Hôm nay',progress:'Tiến trình',scan:'+ Quét',routine:'Chu trình',journey:'Hành trình',title:{home:'Làn da hôm nay',progress:'Tiến trình của bạn',scan:'Quét da',routine:'Chu trình của bạn',journey:'Hành trình của bạn',history:'Lịch sử quét'}},
    en:{home:'Today',progress:'Progress',scan:'+ Scan',routine:'Routine',journey:'Journey',title:{home:'Your skin today',progress:'Your progress',scan:'Take a skin scan',routine:'Your routine',journey:'Your journey',history:'Scan history'}}
  }
  function setText(el,text){if(el&&el.textContent!==text)el.textContent=text}
  function updateTitles(){
    const target=STRUCTURE[locale].title
    try{if(typeof titles!=='undefined')Object.assign(titles,target)}catch(_e){}
    const active=document.querySelector('.view.active')?.id||'home'
    setText(document.querySelector('#title'),target[active]||target.home)
  }
  function localizeStructure(){
    const s=STRUCTURE[locale]
    ;['home','progress','scan','routine','journey'].forEach(tab=>setText(document.querySelector(`nav [data-tab="${tab}"]`),s[tab]))
    setText(document.querySelector('.brand small'),locale==='vi'?'Theo dõi da cá nhân':'Personal skin tracking')
    setText(document.querySelector('main>header .eyebrow'),locale==='vi'?'THEO DÕI DA CÁ NHÂN':'PERSONAL SKIN TRACKING')
    setText(document.querySelector('aside .science'),locale==='vi'?'Theo dõi các tín hiệu da của chính bạn theo thời gian dưới ánh sáng khả kiến. Không phải thiết bị chẩn đoán.':'Tracks your own visible-light skin signals over time. Not a diagnostic device.')
    updateTitles()
  }

  function ensureSwitcher(){
    const header=document.querySelector('main>header')
    if(!header)return
    let wrap=document.querySelector('.languageSwitchV160')
    if(!wrap){
      wrap=document.createElement('div');wrap.className='languageSwitchV160';wrap.setAttribute('role','group');wrap.setAttribute('aria-label','Language / Ngôn ngữ')
      wrap.innerHTML='<button type="button" data-locale="vi" aria-label="Tiếng Việt">VI</button><button type="button" data-locale="en" aria-label="English">EN</button>'
      header.appendChild(wrap)
      wrap.addEventListener('click',e=>{const button=e.target.closest('[data-locale]');if(button)setLocale(button.dataset.locale)})
    }
    wrap.querySelectorAll('[data-locale]').forEach(btn=>btn.classList.toggle('active',btn.dataset.locale===locale))
  }

  function applyLocale(){
    document.documentElement.lang=locale
    document.documentElement.dataset.locale=locale
    ensureSwitcher();localizeStructure();translateTree(document.body);localizeStructure()
  }
  function rerenderKnownUI(){
    try{if(typeof render==='function')render()}catch(_e){}
    try{if(typeof applyModeUI==='function'&&document.querySelector('#scan.view.active'))applyModeUI()}catch(_e){}
    try{if(window.skinJourneyV158?.render)window.skinJourneyV158.render()}catch(_e){}
  }
  function setLocale(next){
    if(!SUPPORTED.includes(next))return
    locale=next;localStorage.setItem(STORAGE_KEY,locale);updateTitles();rerenderKnownUI();requestAnimationFrame(applyLocale)
    window.dispatchEvent(new CustomEvent('skin-ai:locale-change',{detail:{locale}}))
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;applyLocale()})}

  // Localize known browser prompts created by the tracking layer.
  const nativePrompt=window.prompt?.bind(window)
  if(nativePrompt)window.prompt=function(message,defaultValue){return nativePrompt(locale==='vi'?dynamicVi(String(message||'')):String(message||''),defaultValue)}

  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true,characterData:true})
  document.addEventListener('click',e=>{if(e.target.closest('[data-tab],[data-go],[data-result-view],[data-session-action]'))setTimeout(schedule,0)})
  window.addEventListener('skin-ai:rendered',schedule)
  window.skinI18n={version:VERSION,getLocale:()=>locale,setLocale,t:(en)=>locale==='vi'?dynamicVi(en):en}
  setTimeout(applyLocale,0)
})()
