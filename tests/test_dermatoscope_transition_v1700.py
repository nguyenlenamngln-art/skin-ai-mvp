from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "web" / "dermatoscope_transition_v1700.js"
INDEX = ROOT / "web" / "index.html"
SW = ROOT / "web" / "sw.js"
APP = ROOT / "web" / "app.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_consumer_phone_rgb_is_research_only_not_deleted():
    js = PATCH.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    assert "data-mode=\"rgb\"" in html
    assert "data-legacy-research-only=\"true\"" in html
    assert "button.hidden=!researchMode" in js
    assert "research=\"1\"" not in js
    assert "params.get('research')==='1'" in js
    assert "/v1/rgb/analyze" in app


def test_legacy_rgb_history_is_preserved_and_labeled():
    js = PATCH.read_text(encoding="utf-8")
    assert "Legacy Phone RGB" in js
    assert "Historical Phone RGB scan — view only" in js
    assert "row.dataset.legacyRgb='true'" in js
    assert "scan?.modality!=='rgb'" in js


def test_consumer_cannot_resume_legacy_rgb_capture_from_history():
    js = PATCH.read_text(encoding="utf-8")
    assert "legacyView=!researchMode" in js
    assert "capture.classList.toggle('hidden',legacyView)" in js
    assert "Legacy Phone RGB · read only" in js
    assert "returnConsumerToAvailableScan" in js
    assert "scanMode='uv'" in js


def test_transition_is_presentation_only_and_engine_remains_frozen():
    js = PATCH.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1700_asset_loads_last_and_cache_is_bumped():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    asset = "/app/dermatoscope_transition_v1700.js?v=1700"
    assert asset in html
    assert asset in sw
    assert html.index("rejected_state_i18n_v1606.js?v=1607") < html.index("dermatoscope_transition_v1700.js?v=1700")
    assert "skin-ai-beta-v1700" in sw


def test_empty_home_copy_no_longer_promotes_phone_rgb():
    html = INDEX.read_text(encoding="utf-8")
    assert "Start a scan to create your baseline." in html
    assert "Start with a Phone RGB or UV scan to create your baseline." not in html
