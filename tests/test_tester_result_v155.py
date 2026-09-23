from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
SCRIPT = ROOT / "web" / "tester_result_v155.js"
STYLE = ROOT / "web" / "tester_result_v155.css"
SW = ROOT / "web" / "sw.js"


def test_v155_assets_are_loaded_after_measurement_ui():
    html = INDEX.read_text(encoding="utf-8")

    assert "/app/tester_result_v155.css?v=155" in html
    assert "/app/tester_result_v155.js?v=155" in html
    assert html.index("rgb_measurement_v15.js") < html.index("tester_result_v155.js")


def test_v155_is_presentation_only_and_keeps_v152_engine():
    js = SCRIPT.read_text(encoding="utf-8")

    assert "TESTER_RESULT_VERSION = '1.5.5'" in js
    assert "ENGINE_UNDER_TEST = '1.5.2'" in js
    assert "Your skin today".lower() in js.lower()
    assert "Technical details" in js
    assert "not diagnoses" in js


def test_v155_exposes_baseline_comparison_quality_and_technical_sections():
    js = SCRIPT.read_text(encoding="utf-8")

    for label in (
        "YOUR SKIN TODAY",
        "CHANGE SINCE LAST COMPARABLE SCAN",
        "WHAT WE DETECTED",
        "SCAN QUALITY",
        "Technical details",
        "This scan is your baseline",
    ):
        assert label in js


def test_v155_avoids_unvalidated_severity_labels():
    js = SCRIPT.read_text(encoding="utf-8").lower()

    for unsupported_label in ("mild redness", "moderate redness", "severe redness", "healthy skin score"):
        assert unsupported_label not in js


def test_v155_assets_are_cached_by_pwa():
    sw = SW.read_text(encoding="utf-8")

    assert "skin-ai-beta-v155" in sw
    assert "/app/tester_result_v155.css?v=155" in sw
    assert "/app/tester_result_v155.js?v=155" in sw


def test_v155_style_has_mobile_layout():
    css = STYLE.read_text(encoding="utf-8")

    assert ".testerResultV155" in css
    assert ".testerTechnical" in css
    assert "@media(max-width:650px)" in css
