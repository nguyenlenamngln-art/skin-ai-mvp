from pathlib import Path

from skin_ai.comparison_v159 import VERSION, comparison_match

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
JS = ROOT / "web" / "comparable_progress_v159.js"
CSS = ROOT / "web" / "comparable_progress_v159.css"
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
    }
    base.update(overrides)
    return base


def test_v159_version():
    assert VERSION == "1.5.9"


def test_v159_similar_capture_remains_eligible():
    result = comparison_match(metrics(face_area_fraction=0.31, face_center_offset_fraction=0.055, skin_luminance_median_0_255=132.0), metrics())
    assert result["comparison_match_available"] is True
    assert result["comparison_match_eligible"] is True
    assert result["comparison_match_label"] in {"strong", "usable"}


def test_v159_rejects_material_scale_mismatch_for_trending():
    result = comparison_match(metrics(face_area_fraction=0.58), metrics(face_area_fraction=0.22))
    assert result["comparison_match_available"] is True
    assert result["comparison_match_eligible"] is False
    assert result["comparison_match_label"] == "review"
    assert "face_scale_differs" in result["comparison_match_reasons"]


def test_v159_rejects_material_lighting_mismatch_for_trending():
    result = comparison_match(metrics(skin_luminance_median_0_255=210.0), metrics(skin_luminance_median_0_255=90.0))
    assert result["comparison_match_eligible"] is False
    assert "lighting_differs" in result["comparison_match_reasons"]


def test_v159_baseline_has_no_false_comparison_claim():
    result = comparison_match(metrics(), None)
    assert result["comparison_match_available"] is False
    assert result["comparison_match_label"] == "baseline"


def test_v159_entrypoint_keeps_measurement_engine_frozen_and_gates_only_longitudinal_use():
    entry = ENTRY.read_text(encoding="utf-8")
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
    assert "stamp_comparison_match" in entry
    assert 'out["longitudinal_reason"] = "comparison_match_low"' in entry
    assert "redness_threshold" not in entry
    assert "pigmentation_threshold" not in entry


def test_v159_frontend_shows_exact_deltas_and_comparison_match():
    js = JS.read_text(encoding="utf-8")
    assert "Comparison match" in js
    assert "face-centered for easier visual comparison" in js
    assert "Match previous framing" in js
    assert "redness_area_fraction" in js
    assert "pigmentation_area_fraction" in js
    assert "texture_index_proxy" in js


def test_v159_aligned_compare_and_capture_reference_styles_exist():
    css = CSS.read_text(encoding="utf-8")
    assert ".pjCompareFrame.v159Aligned" in css
    assert ".v159Ghost" in css
    assert ".v159DeltaGrid" in css
    assert ".v159Match.review" in css


def test_v159_assets_remain_loaded_and_cached_after_later_patches():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "/app/comparable_progress_v159.css?v=159" in html
    assert "/app/comparable_progress_v159.js?v=159" in html
    assert html.index("ios_nav_hotfix_v1584.js") < html.index("comparable_progress_v159.js")
    assert "const CACHE='skin-ai-beta-v" in sw
    assert "/app/comparable_progress_v159.css?v=159" in sw
    assert "/app/comparable_progress_v159.js?v=159" in sw
