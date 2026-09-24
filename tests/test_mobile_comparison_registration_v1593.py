from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
JS = ROOT / "web" / "mobile_comparison_registration_v1593.js"
CSS = ROOT / "web" / "mobile_comparison_registration_v1593.css"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1593_assets_are_loaded_directly_after_credibility_layer():
    html = INDEX.read_text(encoding="utf-8")
    assert "/app/mobile_comparison_registration_v1593.css?v=1593" in html
    assert "/app/mobile_comparison_registration_v1593.js?v=1593" in html
    assert html.index("comparison_credibility_v1591.js") < html.index("mobile_comparison_registration_v1593.js")


def test_v1593_mobile_uses_one_shared_portrait_viewport():
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert "aspect-ratio:3/4!important" in css
    assert "shared-viewport" in js
    assert "Both images are normalized into the same facial viewport" in js


def test_v1593_cover_is_computed_after_face_anchor_and_has_overscan():
    js = JS.read_text(encoding="utf-8")
    assert "anchoredCoverScale" in js
    assert "Cover is computed AFTER anchoring" in js
    assert "const overscan=mobile?1.07:1.025" in js
    assert "Math.max(faceScale,coverScale)*overscan" in js


def test_v1593_residual_alignment_cannot_shrink_or_uncover_edges():
    js = JS.read_text(encoding="utf-8")
    assert "const residualScale=Math.max(1,Math.min(1.025" in js
    assert "const maxDx=t.cw*.025,maxDy=t.ch*.022" in js
    assert "angle=Math.max(mobile?-1.5:-2.5" in js


def test_v1593_replaces_previous_registration_authority():
    js = JS.read_text(encoding="utf-8")
    assert "frame.classList.remove('v1592Registered')" in js
    assert "frame.classList.add('v1593Registered')" in js
    assert "registrationVersion=VERSION" in js


def test_v1593_is_presentation_only_and_engine_stays_frozen():
    js = JS.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1593_pwa_cache_bumped_and_contains_assets():
    sw = SW.read_text(encoding="utf-8")
    assert "skin-ai-beta-v1593" in sw
    assert "/app/mobile_comparison_registration_v1593.css?v=1593" in sw
    assert "/app/mobile_comparison_registration_v1593.js?v=1593" in sw
