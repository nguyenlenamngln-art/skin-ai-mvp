from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
CSS = ROOT / "web" / "ux_polish_v1581.css"
JS = ROOT / "web" / "ux_polish_v1581.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1581_assets_load_after_v158_product_layer():
    html = INDEX.read_text(encoding="utf-8")
    assert "/app/ux_polish_v1581.css?v=1581" in html
    assert "/app/ux_polish_v1581.js?v=1581" in html
    assert html.index("personal_journey_v158.js") < html.index("ux_polish_v1581.js")


def test_v1581_hides_research_dashboard_from_primary_tester_home():
    css = CSS.read_text(encoding="utf-8")
    assert "#trackingDashboard{display:none!important}" in css
    assert "#status{display:none!important}" in css


def test_v1581_uses_progressive_disclosure_for_scan_controls():
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert "uxShowAdvancedScan" in css
    assert "#trackingContext" in css
    assert "#sessionPanel" in css
    assert "Advanced scan settings" in js
    assert "Take a clear photo" in js
    assert "Open camera" in js


def test_v1581_simplifies_single_scan_empty_states():
    js = JS.read_text(encoding="utf-8")
    assert "Your baseline is saved" in js
    assert "Add your second comparable scan" in js
    assert "Take another scan" in js


def test_v1581_keeps_five_destination_navigation_and_mobile_product():
    html = INDEX.read_text(encoding="utf-8")
    for tab in ("home", "progress", "scan", "routine", "journey"):
        assert f'data-tab="{tab}"' in html
    assert 'data-tab="history"' not in html


def test_v1581_is_presentation_only_and_engine_remains_frozen():
    js = JS.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "No measurement or access-control changes" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1582_routine_page_has_breathing_room_between_sections():
    css = CSS.read_text(encoding="utf-8")
    assert "V1.5.8.2 — Routine page spacing and visual rhythm" in css
    assert "margin-bottom:36px" in css
    assert "#journeyRoutineAddon{display:grid;gap:30px" in css
    assert "#routine .pjContext{padding:26px;gap:14px}" in css
    assert "#routine .pjNoteRow{padding:16px 2px 18px;gap:18px}" in css
    assert "#routine #saveRoutine{padding:12px 18px}" in css


def test_v1582_mobile_routine_spacing_remains_touch_friendly():
    css = CSS.read_text(encoding="utf-8")
    assert "#routine #saveRoutine{width:100%}" in css
    assert "#journeyRoutineAddon{gap:26px}" in css
    assert "#routine .routine{padding:20px}" in css


def test_v1582_assets_remain_cached_after_later_pwa_bumps():
    sw = SW.read_text(encoding="utf-8")
    assert "const CACHE='skin-ai-beta-v" in sw
    assert "/app/ux_polish_v1581.css?v=1581" in sw
    assert "/app/ux_polish_v1581.js?v=1581" in sw
