from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
CSS = ROOT / "web" / "mobile_navigation_v1583.css"
JS = ROOT / "web" / "mobile_navigation_v1583.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1583_assets_load_last_in_product_shell():
    html = INDEX.read_text(encoding="utf-8")
    assert "/app/mobile_navigation_v1583.css?v=1583" in html
    assert "/app/mobile_navigation_v1583.js?v=1583" in html
    assert html.index("ux_polish_v1581.css") < html.index("mobile_navigation_v1583.css")
    assert html.index("ux_polish_v1581.js") < html.index("mobile_navigation_v1583.js")


def test_v1583_uses_one_five_destination_bottom_navigation():
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert "grid-template-columns:repeat(5,minmax(0,1fr))" in css
    assert "button::before{content:none!important" in css
    assert "progress:'Progress'" in js
    assert "scan:'+ Scan'" in js
    assert ".mobileScanJump" in css and "display:none!important" in css
    assert "jump.remove()" in js


def test_v1583_active_state_does_not_make_scan_selected_on_every_tab():
    css = CSS.read_text(encoding="utf-8")
    assert 'button[data-tab="scan"]' in css
    assert 'button[data-tab="scan"].active' in css
    assert 'button.active:not([data-tab="scan"])' in css


def test_v1583_title_follows_active_tab_not_rgb_mode():
    js = JS.read_text(encoding="utf-8")
    assert "home:'Your skin today'" in js
    assert "scan:'Take a skin scan'" in js
    assert "syncTitle(activeTab())" in js
    assert "const baseApplyModeUI=applyModeUI" in js
    assert "baseSetTab(tab)" in js


def test_v1583_simplifies_phone_capture_flow():
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert "Take a clear photo" in js
    assert "Even light · Face centered · Hold steady" in js
    assert "Open camera" in js
    assert "Or upload a photo" in js
    assert "Choose photo" in js
    assert ".mobileCaptureHint" in css and "display:none!important" in css
    assert ".pjQuickLinks" in css and "display:none!important" in css


def test_v1583_preserves_touch_targets_and_safe_area():
    css = CSS.read_text(encoding="utf-8")
    assert "min-height:48px!important" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "padding:22px 16px calc(104px + env(safe-area-inset-bottom))" in css


def test_v1583_is_presentation_only_and_engine_protocol_are_frozen():
    js = JS.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1583_pwa_cache_is_bumped():
    sw = SW.read_text(encoding="utf-8")
    assert "skin-ai-beta-v1583" in sw
    assert "/app/mobile_navigation_v1583.css?v=1583" in sw
    assert "/app/mobile_navigation_v1583.js?v=1583" in sw
