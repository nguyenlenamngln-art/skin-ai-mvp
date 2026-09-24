from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "visual_registration_v1592.js"
CSS = ROOT / "web" / "visual_registration_v1592.css"
LOADER = ROOT / "web" / "comparison_credibility_v1591.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1592_registration_assets_exist_as_compatibility_layer():
    js = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "V1.5.9.2" in js
    assert "V1.5.9.2 — Visual Registration & Comparison Layout" in css
    assert "/app/visual_registration_v1592.css?v=1592" in sw
    assert "/app/visual_registration_v1592.js?v=1592" in sw


def test_v1592_desktop_comparison_uses_full_width_and_resets_aspect_ratio():
    css = CSS.read_text(encoding="utf-8")
    assert "width:100%!important" in css
    assert "max-width:none!important" in css
    assert "aspect-ratio:auto!important" in css
    assert "height:clamp(460px,52vw,640px)!important" in css


def test_v1592_compatibility_loader_hands_registration_to_latest_layer():
    js = JS.read_text(encoding="utf-8")
    assert "compatibility loader" in js
    assert "V1.5.9.3 is now the single authority" in js
    assert "/app/mobile_comparison_registration_v1593.css?v=1593" in js
    assert "/app/mobile_comparison_registration_v1593.js?v=1593" in js


def test_v1592_registration_is_presentation_only():
    js = JS.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1592_pwa_cache_keeps_registration_assets_after_future_bumps():
    sw = SW.read_text(encoding="utf-8")
    assert "const CACHE='skin-ai-beta-v" in sw
    assert "/app/visual_registration_v1592.css?v=1592" in sw
    assert "/app/visual_registration_v1592.js?v=1592" in sw
