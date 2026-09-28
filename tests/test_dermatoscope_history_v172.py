from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "src" / "skin_ai" / "dermatoscope_history_v172.py"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"
JS = ROOT / "web" / "dermatoscope_history_v172.js"
CSS = ROOT / "web" / "dermatoscope_history_v172.css"
POLISH = ROOT / "web" / "dermatoscope_ui_polish_v1711.js"


def test_v172_installs_baseline_history_without_touching_rgb_engine():
    api = API.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert 'VERSION = "1.7.2"' in api
    assert 'DEFAULT_SUBJECT_KEY = "my_profile"' in api
    assert "/v1/dermatoscope/history" in api
    assert "/v1/dermatoscope/baseline" in api
    assert "/v1/dermatoscope/position-summary" in api
    assert 'baseline_rule": "first_capture"' in api
    assert "simulator" in api
    assert "install_dermatoscope_history_v172(product_api)" in entry
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v172_simulator_history_is_separate_from_future_real_device_series():
    api = API.read_text(encoding="utf-8")
    assert "AND simulator=?" in api
    assert "GROUP BY region, subregion, illumination_mode, brightness_level, simulator" in api
    assert '"simulator": bool(r["simulator"])' in api


def test_v172_ui_explains_first_capture_baseline_and_simulator_status():
    js = JS.read_text(encoding="utf-8")
    assert "Baseline by skin position" in js
    assert "Mốc ban đầu theo từng vị trí da" in js
    assert "first accepted image" in js
    assert "Ảnh đạt yêu cầu đầu tiên" in js
    assert "Simulator series" in js
    assert "Chuỗi dữ liệu mô phỏng" in js
    assert "/v1/dermatoscope/position-summary" in js
    assert "my_profile" in js


def test_v172_history_ui_follows_existing_visual_tokens_and_is_loaded():
    css = CSS.read_text(encoding="utf-8")
    polish = POLISH.read_text(encoding="utf-8")
    for token in ("var(--line)", "var(--ink)", "var(--muted)", "var(--green)", "var(--sage)"):
        assert token in css
    assert ".dermHistoryCard" in css
    assert ".dermHistoryGrid" in css
    assert "/app/dermatoscope_history_v172.css?v=172" in polish
    assert "/app/dermatoscope_history_v172.js?v=172" in polish
