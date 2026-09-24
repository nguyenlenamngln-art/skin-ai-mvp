from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "visual_registration_v1592.js"
CSS = ROOT / "web" / "visual_registration_v1592.css"
LOADER = ROOT / "web" / "comparison_credibility_v1591.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1592_registration_assets_exist_and_are_loaded():
    js = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    loader = LOADER.read_text(encoding="utf-8")
    assert "V1.5.9.2 — Visual Registration & Comparison Layout" in js
    assert "V1.5.9.2 — Visual Registration & Comparison Layout" in css
    assert "/app/visual_registration_v1592.css?v=1592" in loader
    assert "/app/visual_registration_v1592.js?v=1592" in loader


def test_v1592_desktop_comparison_uses_full_width_and_resets_aspect_ratio():
    css = CSS.read_text(encoding="utf-8")
    assert "width:100%!important" in css
    assert "max-width:none!important" in css
    assert "aspect-ratio:auto!important" in css
    assert "height:clamp(460px,52vw,640px)!important" in css


def test_v1592_registration_goes_beyond_face_box_centering():
    js = JS.read_text(encoding="utf-8")
    assert "targetFaceW" in js
    assert "targetFaceH" in js
    assert "estimateResidual" in js
    assert "patchScore" in js
    assert "angles=[-4,0,4]" in js
    assert "scales=[.97,1,1.03]" in js
    assert "geometry+residual" in js
    assert "geometry-only fallback" in js


def test_v1592_registration_is_presentation_only():
    js = JS.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation-only refinement" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1592_pwa_cache_contains_registration_assets():
    sw = SW.read_text(encoding="utf-8")
    assert "skin-ai-beta-v1592" in sw
    assert "/app/visual_registration_v1592.css?v=1592" in sw
    assert "/app/visual_registration_v1592.js?v=1592" in sw
