from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "dermatoscope_guided_capture_v171.js"
CSS = ROOT / "web" / "dermatoscope_guided_capture_v171.css"
TRANSITION = ROOT / "web" / "dermatoscope_transition_v1700.js"
SW = ROOT / "web" / "sw.js"
API = ROOT / "src" / "skin_ai" / "dermatoscope_capture_v171.py"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v171_guided_regions_and_multi_shot_cheeks():
    js = JS.read_text(encoding="utf-8")
    for region in ("forehead", "left_cheek", "right_cheek", "nose", "chin", "custom"):
        assert region in js
    assert "left_cheek:{en:'Left cheek',vi:'Má trái',shots:['upper','middle','lower']}" in js
    assert "right_cheek:{en:'Right cheek',vi:'Má phải',shots:['upper','middle','lower']}" in js


def test_v171_auto_capture_quality_gate_and_audio_guidance():
    js = JS.read_text(encoding="utf-8")
    assert "const HOLD_MS=800" in js
    assert "q.exposure&&q.sharpness&&q.stability&&q.glare" in js
    assert "speechSynthesis" in js
    assert "Image captured." in js
    assert "Đã chụp ảnh." in js
    assert "capture(m)" in js
    assert "COOLDOWN_MS" in js


def test_v171_uses_rear_camera_and_is_simulator_until_hardware_validation():
    js = JS.read_text(encoding="utf-8")
    assert "facingMode:{ideal:'environment'}" in js
    assert "form.append('simulator','true')" in js
    assert "camera sau chỉ được dùng để kiểm tra quy trình chụp tự động" in js
    api = API.read_text(encoding="utf-8")
    assert '"thresholds_provisional": True' in api
    assert '"validated_for_de500": False' in api


def test_v1711_consumer_copy_uses_product_language_and_alias():
    js = JS.read_text(encoding="utf-8")
    assert "const VERSION='1.7.1.1'" in js
    assert "const DEVICE_NAME='SkinScope One'" in js
    assert "QUÉT DA CHI TIẾT" in js
    assert "THIẾT LẬP THIẾT BỊ" in js
    assert "Hướng dẫn bằng giọng nói" in js
    assert "Ánh sáng" in js
    assert "DERMATOSCOPE SCAN" not in js
    assert "QUÉT DERMATOSCOPE" not in js
    assert "IBOOLO DE-500" not in js


def test_v1711_visuals_reuse_existing_app_design_tokens():
    css = CSS.read_text(encoding="utf-8")
    for token in ("var(--line)", "var(--ink)", "var(--muted)", "var(--green)", "var(--sage)"):
        assert token in css
    for cls in (".dermIntroCard", ".dermRegion", ".dermSetupFooter", ".dermCaptureLayout", ".dermCompleteCard"):
        assert cls in css
    assert ".dermRegion.active" in css
    assert "background:#e8eee6" in css


def test_v171_capture_metadata_is_modality_specific_and_not_rgb_analysis():
    api = API.read_text(encoding="utf-8")
    for field in (
        "device_model", "region", "subregion", "sequence_index",
        "illumination_mode", "brightness_level", "simulator", "quality_json",
    ):
        assert field in api
    assert 'DEVICE = "IBOOLO_DE500"' in api
    assert '"analysis_status": "capture_only"' in api
    assert "/v1/rgb/analyze" not in api


def test_v171_api_is_installed_without_changing_frozen_rgb_engine():
    entry = ENTRY.read_text(encoding="utf-8")
    assert "install_dermatoscope_capture_v171(product_api)" in entry
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1711_assets_are_loaded_and_cached():
    transition = TRANSITION.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    for asset in (
        "/app/dermatoscope_guided_capture_v171.css?v=1711",
        "/app/dermatoscope_guided_capture_v171.js?v=1711",
    ):
        assert asset in transition
        assert asset in sw
    assert re.search(r"const CACHE='skin-ai-beta-v[0-9]+'", sw)
    assert CSS.exists()
