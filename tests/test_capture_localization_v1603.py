from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "web" / "localization_runtime_patch_v1602.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1603_covers_live_capture_statuses_seen_in_vi_ui():
    js = PATCH.read_text(encoding="utf-8")
    # Later localization releases may supersede the runtime version while retaining
    # all V1.6.0.3 capture coverage.
    assert "const VERSION='1.6.0." in js
    required_english = (
        "Handheld",
        "Distance good",
        "Good",
        "Hold steady",
        "Move back",
        "Move closer",
        "Use face guide",
    )
    for text in required_english:
        assert text in js
    for vi in ("Cầm tay", "Khoảng cách phù hợp", "Tốt", "Giữ máy ổn định", "Đưa máy lại gần"):
        assert vi in js


def test_v1603_translates_capture_guidance_and_preflight_states():
    js = PATCH.read_text(encoding="utf-8")
    required = (
        "Lighting, sharpness and stability are browser estimates.",
        "preview frames are not saved.",
        "Camera access was not available.",
        "Low image resolution",
        "Lighting outside preferred range",
        "Image may be blurry",
        "PRE-CAPTURE CHECK",
        "Retake recommended",
        "Capture can be improved",
        "Choose another image",
        "Analyze anyway",
    )
    for text in required:
        assert text in js


def test_v1603_localizes_dynamic_capture_result_date_and_quality_value():
    js = PATCH.read_text(encoding="utf-8")
    assert "Intl.DateTimeFormat(vi?'vi-VN':'en-US'" in js
    assert "hour12:!vi" in js
    assert ".testerQualityScore strong" in js
    assert "el.textContent='Tốt'" in js
    assert "el.textContent='Good'" in js


def test_v1603_remains_reversible_and_observes_runtime_updates():
    js = PATCH.read_text(encoding="utf-8")
    assert "VI_TO_EN=Object.fromEntries" in js
    assert "skin-ai:locale-change" in js
    assert "characterData:true" in js
    assert "#cgCapture" in js
    assert "#cgContinue" in js
    assert "#cgRetake" in js


def test_v1603_pwa_cache_advances_and_keeps_localization_runtime():
    sw = SW.read_text(encoding="utf-8")
    assert "const CACHE='skin-ai-beta-v" in sw
    assert "/app/localization_runtime_patch_v1602.js?v=1602" in sw


def test_v1603_is_presentation_only_and_measurement_engine_stays_frozen():
    js = PATCH.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
