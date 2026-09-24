from pathlib import Path

from skin_ai.comparison_v159 import SCORING_VERSION, comparison_match

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
JS = ROOT / "web" / "comparison_credibility_v1591.js"
CSS = ROOT / "web" / "comparison_credibility_v1591.css"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def metrics(**overrides):
    base = {
        "rgb_engine_version": "1.5.2",
        "face_area_fraction": 0.30,
        "face_center_offset_fraction": 0.05,
        "skin_luminance_median_0_255": 130.0,
        "left_right_luminance_asymmetry": 0.08,
        "face_bbox": {"x": 100, "y": 80, "w": 260, "h": 320},
        "capture_image_width_px": 640,
        "capture_image_height_px": 960,
    }
    base.update(overrides)
    return base


def test_v1591_scoring_version_and_strong_requires_complete_geometry():
    assert SCORING_VERSION == "1.5.9.1"
    complete = comparison_match(metrics(face_area_fraction=0.305), metrics())
    assert complete["comparison_geometry_complete"] is True
    assert complete["comparison_match_eligible"] is True

    legacy_current = metrics(capture_image_width_px=None, capture_image_height_px=None)
    legacy_reference = metrics(capture_image_width_px=None, capture_image_height_px=None)
    legacy = comparison_match(legacy_current, legacy_reference)
    assert legacy["comparison_geometry_complete"] is False
    assert legacy["comparison_match_score"] <= 79.0
    assert legacy["comparison_match_label"] != "strong"


def test_v1591_tighter_scale_and_position_gate():
    reference = metrics()
    current = metrics(
        face_area_fraction=0.45,
        face_bbox={"x": 190, "y": 120, "w": 330, "h": 400},
    )
    result = comparison_match(current, reference)
    assert result["comparison_match_label"] == "review"
    assert result["comparison_match_eligible"] is False


def test_v1591_future_scans_store_normalized_geometry_without_changing_engine():
    entry = ENTRY.read_text(encoding="utf-8")
    assert 'metrics["capture_image_width_px"]' in entry
    assert 'metrics["capture_image_height_px"]' in entry
    assert 'metrics["face_center_x_fraction"]' in entry
    assert 'metrics["face_center_y_fraction"]' in entry
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v1591_display_delta_policy_uses_displayed_endpoints():
    js = JS.read_text(encoding="utf-8")
    assert "round(c-b,1)" in js
    assert "round(c-b,4)" in js
    assert "toFixed(4)" in js
    assert "displayed endpoints and displayed deltas always agree" in js


def test_v1591_two_scan_progress_uses_start_end_cards_not_line_charts():
    js = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "r.length!==2" in js
    assert "v1591TwoPointCard" in js
    assert "Your change from baseline" in js
    assert ".v1591TwoPointGrid" in css
    assert ".v1591Endpoints" in css


def test_v1591_recomputes_screen_match_against_exact_displayed_baseline():
    js = JS.read_text(encoding="utf-8")
    assert "strictMatch(cur,base)" in js
    assert "score=Math.min(score,79)" in js
    assert "older scans lack full framing metadata" in js


def test_v1591_mobile_progress_has_safe_space_above_fixed_nav():
    css = CSS.read_text(encoding="utf-8")
    assert "#progressRoot{padding-bottom:calc(150px + env(safe-area-inset-bottom))}" in css


def test_v1591_assets_load_after_v159_and_remain_cached_in_later_releases():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "/app/comparison_credibility_v1591.css?v=1591" in html
    assert "/app/comparison_credibility_v1591.js?v=1591" in html
    assert html.index("comparable_progress_v159.js") < html.index("comparison_credibility_v1591.js")
    assert "skin-ai-beta-v15" in sw
    assert "/app/comparison_credibility_v1591.css?v=1591" in sw
    assert "/app/comparison_credibility_v1591.js?v=1591" in sw
