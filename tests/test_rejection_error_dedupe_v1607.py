from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "web" / "rejected_state_i18n_v1606.js"
INDEX = ROOT / "web" / "index.html"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1607_suppresses_top_banner_for_handled_422_rejection():
    js = PATCH.read_text(encoding="utf-8")
    assert "const VERSION='1.6.0.7'" in js
    assert "function handledCaptureRejection()" in js
    assert "Number(attempt.status)===422" in js
    assert "if(handledCaptureRejection())return baseShowError('')" in js


def test_v1607_keeps_non_capture_errors_visible():
    js = PATCH.read_text(encoding="utf-8")
    assert "return baseShowError(translateQualityText(lastErrorCanonical))" in js
    assert "else if(lastErrorCanonical)baseShowError(translateQualityText(lastErrorCanonical))" in js


def test_v1607_rejected_result_card_still_renders_guidance():
    js = PATCH.read_text(encoding="utf-8")
    assert "renderRejectedAttempt=function()" in js
    assert "Ảnh chụp chưa đạt — chưa được lưu." in js
    assert "Hướng dẫn chụp lại" in js
    assert "flags.map(flagLabel).join(', ')" in js


def test_v1607_cache_and_asset_version_bumped():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    asset = "/app/rejected_state_i18n_v1606.js?v=1607"
    assert asset in html
    assert asset in sw
    assert "skin-ai-beta-v1607" in sw


def test_v1607_is_presentation_only_and_measurement_frozen():
    js = PATCH.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
