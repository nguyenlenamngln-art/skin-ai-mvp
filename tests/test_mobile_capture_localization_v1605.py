from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "web" / "capture_guidance_v2.js"
MOBILE = ROOT / "web" / "capture_guidance_mobile_v12.js"
TRACKING = ROOT / "web" / "rgb_capture_tracking_v14.js"
COMPARE = ROOT / "web" / "comparable_progress_v159.js"
PATCH = ROOT / "web" / "localization_runtime_patch_v1602.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1605_runtime_dictionary_covers_mobile_capture_release_blockers():
    js = PATCH.read_text(encoding="utf-8")
    assert "const VERSION='1.6.0.5'" in js
    required = {
        "Even light · Face centered · Hold steady": "Ánh sáng đều · Đặt mặt vào giữa khung · Giữ máy ổn định",
        "We’ll compare framing and lighting with your previous good scan.": "Hệ thống sẽ so sánh khung hình và ánh sáng với lần quét đạt yêu cầu trước đó.",
        "Match previous framing": "Căn theo khung hình trước",
        "Move less": "Giữ yên hơn",
        "Too much movement": "Di chuyển quá nhiều",
        "Distance good": "Khoảng cách phù hợp",
    }
    for en, vi in required.items():
        assert en in js
        assert vi in js


def test_v1605_mobile_live_writer_localizes_before_dom_write():
    js = MOBILE.read_text(encoding="utf-8")
    assert "window.skinCaptureI18n?.t" in js
    assert "t('Good')" in js
    assert "t('Move less')" in js
    assert "t('Too much movement')" in js
    assert "skin-ai:locale-change" in js


def test_v1605_tracking_distance_writer_localizes_at_source():
    js = TRACKING.read_text(encoding="utf-8")
    assert "window.skinCaptureI18n?.t" in js
    for text in ("Distance", "Checking…", "Center face", "Distance good", "Move back", "Move closer", "Use face guide"):
        assert f"t('{text}')" in js or f"setDistance('{text}'" in js
    assert "skin-ai:locale-change" in js


def test_v1605_previous_scan_overlay_localizes_at_source():
    js = COMPARE.read_text(encoding="utf-8")
    assert "window.skinCaptureI18n?.t" in js
    assert "t('Match previous framing')" in js
    assert "t('We’ll compare framing and lighting with your previous good scan.')" in js
    assert "t('Previous comparable scan alignment reference')" in js
    assert "skin-ai:locale-change" in js


def test_v1605_base_capture_guidance_localizes_camera_and_preflight_at_source():
    js = BASE.read_text(encoding="utf-8")
    assert "const cgT=" in js
    for text in (
        "CAPTURE GUIDANCE V2",
        "Improve repeatability before analysis",
        "Use camera",
        "Lighting",
        "Sharpness",
        "Stability",
        "Cancel",
        "Capture photo",
        "Camera access was not available.",
        "PRE-CAPTURE CHECK",
        "Retake recommended",
        "Capture can be improved",
        "Choose another image",
        "Analyze anyway",
    ):
        assert text in js
    assert "cgT('Good')" in js
    assert "cgT('Hold steady')" in js


def test_v1605_locale_switch_keeps_camera_dom_in_place():
    js = BASE.read_text(encoding="utf-8")
    assert "function cgRelocalizeActiveUI" in js
    assert "window.addEventListener('skin-ai:locale-change',cgRelocalizeActiveUI)" in js
    assert "panel.remove()" not in js
    assert "if(captureGuideStream)cgLiveSample()" in js


def test_v1605_pwa_cache_bumped():
    sw = SW.read_text(encoding="utf-8")
    # Later releases may advance the global PWA cache version.
    assert "const CACHE='skin-ai-beta-v" in sw
    assert "/app/capture_guidance_mobile_v12.js?v=12" in sw
    assert "/app/rgb_capture_tracking_v14.js?v=14" in sw
    assert "/app/comparable_progress_v159.js?v=159" in sw
    assert "/app/localization_runtime_patch_v1602.js?v=1602" in sw


def test_v1605_is_presentation_only_and_measurement_stays_frozen():
    patch = PATCH.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in patch
    assert "redness_threshold" not in patch
    assert "pigmentation_threshold" not in patch
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
