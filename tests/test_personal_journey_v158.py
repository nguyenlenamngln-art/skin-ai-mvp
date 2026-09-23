from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
JS = ROOT / "web" / "personal_journey_v158.js"
CSS = ROOT / "web" / "personal_journey_v158.css"
STUDY_CSS = ROOT / "web" / "tester_study_v157.css"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v158_has_simple_five_destination_navigation():
    html = INDEX.read_text(encoding="utf-8")
    for tab in ("home", "progress", "scan", "routine", "journey"):
        assert f'data-tab="{tab}"' in html
    assert 'data-tab="history"' not in html
    assert html.index('data-tab="home"') < html.index('data-tab="progress"') < html.index('data-tab="scan"')


def test_v158_builds_today_progress_before_after_and_journey():
    js = JS.read_text(encoding="utf-8")
    assert "VERSION='1.5.8'" in js
    assert "YOUR SKIN TODAY" in js
    assert "FROM YOUR BASELINE" in js
    assert "BEFORE & AFTER" in js
    assert "MY JOURNEY" in js
    assert "SKIN DIARY" in js
    assert "pjCompareSlider" in js
    assert "comparableScans" in js


def test_v158_uses_personal_baseline_and_descriptive_changes():
    js = JS.read_text(encoding="utf-8")
    assert "baselineComparable" in js
    assert "your own comparable RGB scans" in js
    assert "Higher/lower is descriptive, not good/bad" in js
    assert "population rankings" in js
    for prohibited in ("healthy skin score", "severity score", "mild", "moderate", "severe"):
        assert prohibited not in js.lower()


def test_v158_diary_is_optional_and_local_device_only():
    js = JS.read_text(encoding="utf-8")
    assert "saved on this device only" in js
    assert "localStorage" in js
    assert "New product" in js
    assert "Outdoor / sun" in js
    assert "Poor sleep" in js


def test_v158_study_mode_no_longer_hides_product_navigation():
    css = STUDY_CSS.read_text(encoding="utf-8")
    assert 'nav button:not([data-tab="scan"])' not in css
    assert '[data-go="home"]' not in css
    js = JS.read_text(encoding="utf-8")
    assert "pjStudySignedIn" in js
    assert "setTab('home')" in js


def test_v158_is_mobile_first_with_persistent_five_tab_nav():
    css = CSS.read_text(encoding="utf-8")
    assert "@media(max-width:650px)" in css
    assert "position:fixed!important" in css
    assert "grid-template-columns:repeat(5,1fr)!important" in css
    assert "padding-bottom:74px" in css


def test_v158_assets_load_after_study_access_and_pwa_is_bumped():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "/app/personal_journey_v158.css?v=158" in html
    assert "/app/personal_journey_v158.js?v=158" in html
    assert html.index("tester_study_v157.js") < html.index("personal_journey_v158.js")
    assert "skin-ai-beta-v158" in sw
    assert "/app/personal_journey_v158.css?v=158" in sw
    assert "/app/personal_journey_v158.js?v=158" in sw


def test_v158_keeps_rgb_engine_and_capture_protocol_frozen():
    js = JS.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Measurement remains RGB engine V1.5.2 / Capture Protocol V1.4" in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
