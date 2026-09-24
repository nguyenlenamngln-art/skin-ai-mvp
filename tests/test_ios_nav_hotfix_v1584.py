from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
CSS = ROOT / "web" / "ios_nav_hotfix_v1584.css"
JS = ROOT / "web" / "ios_nav_hotfix_v1584.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1584_assets_load_after_v1583_layer():
    html = INDEX.read_text(encoding="utf-8")
    assert "/app/ios_nav_hotfix_v1584.css?v=1584" in html
    assert "/app/ios_nav_hotfix_v1584.js?v=1584" in html
    assert html.index("mobile_navigation_v1583.css") < html.index("ios_nav_hotfix_v1584.css")
    assert html.index("mobile_navigation_v1583.js") < html.index("ios_nav_hotfix_v1584.js")


def test_v1584_renders_body_level_five_tab_navigation():
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert "#mobileBottomNavV1584" in css
    assert "grid-template-columns:repeat(5,minmax(0,1fr))" in css
    assert "z-index:9999" in css
    assert "document.body.appendChild(nav)" in js
    for label in ("Today", "Progress", "+ Scan", "Routine", "Journey"):
        assert label in js


def test_v1584_does_not_depend_on_legacy_sidebar_nav_on_phone():
    css = CSS.read_text(encoding="utf-8")
    assert "body.mobileV1584 aside nav{display:none!important" in css
    assert "bottom:calc(8px + env(safe-area-inset-bottom))" in css
    assert "main{padding-bottom:calc(122px + env(safe-area-inset-bottom))" in css


def test_v1584_removes_duplicate_one_scan_progress_cta_on_mobile():
    css = CSS.read_text(encoding="utf-8")
    assert "#progress .uxBaselineNext{display:none!important" in css


def test_v1584_is_presentation_only_and_measurement_is_frozen():
    js = JS.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1584_assets_remain_cached_after_later_pwa_bumps():
    sw = SW.read_text(encoding="utf-8")
    assert "const CACHE='skin-ai-beta-v" in sw
    assert "/app/ios_nav_hotfix_v1584.css?v=1584" in sw
    assert "/app/ios_nav_hotfix_v1584.js?v=1584" in sw
