from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
I18N = ROOT / "web" / "i18n_v1601.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1601_is_the_single_live_localization_runtime():
    html = INDEX.read_text(encoding="utf-8")
    assert "/app/i18n_v1601.js?v=1601" in html
    assert "/app/i18n_v160.js?v=160" not in html
    assert '<html lang="vi">' in html


def test_v1601_translates_primary_navigation_and_page_titles_both_ways():
    js = I18N.read_text(encoding="utf-8")
    for text in (
        "'Today':'Hôm nay'",
        "'Progress':'Tiến trình'",
        "'Scan':'Quét'",
        "'Routine':'Chu trình'",
        "'Journey':'Hành trình'",
        "home:'Your skin today'",
        "progress:'Your progress'",
        "scan:'Take a skin scan'",
    ):
        assert text in js
    assert "VI_EN=Object.fromEntries" in js
    assert "setLocale(next)" in js


def test_v1601_covers_untranslated_screenshot_fields():
    js = I18N.read_text(encoding="utf-8")
    for text in (
        "Tester access",
        "Use study code",
        "Take a clear photo",
        "Open camera",
        "Or upload a front-facing photo",
        "Visible-light skin signals",
        "CHANGE SINCE LAST COMPARABLE SCAN",
        "Compared only with a same-version, quality-eligible RGB scan.",
        "Higher than your previous comparable scan",
        "Lower than your previous comparable scan",
        "Advanced details",
        "Measurement and scan-quality details",
        "local redness",
        "local pigmentation",
        "analyzed skin boundary",
        "Latest",
        "Baseline",
        "Higher",
        "Lower",
        "Stable",
    ):
        assert f"'{text}'" in js or f'"{text}"' in js


def test_v1601_covers_study_capture_tracking_and_guided_session_copy():
    js = I18N.read_text(encoding="utf-8")
    for text in (
        "TESTER STUDY MODE",
        "Study notice",
        "Tester ID",
        "Access code",
        "Sign in & start session",
        "TRACKING CONTEXT",
        "Who and where are you scanning?",
        "GUIDED SESSION",
        "Capture regions in one visit",
        "CAPTURE GUIDANCE V2",
        "Improve repeatability before analysis",
        "Lighting",
        "Sharpness",
        "Stability",
    ):
        assert text in js


def test_v1601_dynamic_patterns_cover_deltas_counts_and_dates():
    js = I18N.read_text(encoding="utf-8")
    assert "comparable scans?" in js
    assert "saved scans?" in js
    assert "pp vs previous" in js
    assert "pp from baseline" in js
    assert "Tester (.+) · session" in js
    assert "dateVi" in js
    assert "MONTHS" in js and "WEEKDAYS" in js


def test_v1601_preserves_user_content_and_localizes_interface_attributes():
    js = I18N.read_text(encoding="utf-8")
    assert "parent.closest('.pjNoteRow p')" in js
    assert "[placeholder]" in js
    assert "[aria-label]" in js
    assert "[title]" in js


def test_v1601_pwa_cache_contains_new_runtime():
    sw = SW.read_text(encoding="utf-8")
    assert "skin-ai-beta-v1601" in sw
    assert "/app/i18n_v1601.js?v=1601" in sw
    assert "/app/i18n_v160.css?v=160" in sw


def test_v1601_is_presentation_only_and_measurement_remains_frozen():
    js = I18N.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
