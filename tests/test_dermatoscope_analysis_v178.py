from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from skin_ai.dermatoscope_analysis_v178 import (
    VERSION,
    _glare_mask,
    _hair_mask,
    _metrics,
    _optical_field,
    _ruler_mask,
    analyze_image,
)

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "src" / "skin_ai" / "dermatoscope_analysis_v178.py"
RESUME = ROOT / "src" / "skin_ai" / "dermatoscope_resume_v177.py"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def _synthetic_scope(size=320):
    img = Image.new("RGB", (size, size), (5, 5, 5))
    draw = ImageDraw.Draw(img)
    draw.ellipse((12, 12, size - 12, size - 12), fill=(190, 142, 132))
    # glare patch
    draw.ellipse((210, 70, 250, 110), fill=(252, 250, 248))
    # dark hair-like line
    draw.line((55, 80, 235, 225), fill=(35, 28, 25), width=3)
    # simple ruler-like lower band/ticks
    y = int(size * .72)
    draw.line((65, y, 255, y), fill=(45, 45, 45), width=2)
    for x in range(75, 250, 18):
        draw.line((x, y - 12, x, y + 9), fill=(38, 38, 38), width=3)
    return np.asarray(img)


def test_v178_optical_field_excludes_dark_outer_border():
    rgb = _synthetic_scope()
    field, info = _optical_field(rgb)
    assert field.dtype == bool
    assert 0.5 < field.mean() < 0.9
    assert field[160, 160]
    assert not field[0, 0]
    assert info["method"] in {"largest_nonblack_component", "central_ellipse_fallback"}


def test_v178_artifact_masks_find_glare_and_dark_thin_structures():
    rgb = _synthetic_scope()
    field, _ = _optical_field(rgb)
    glare = _glare_mask(rgb, field)
    hair = _hair_mask(rgb, field)
    assert glare.sum() > 0
    assert hair.sum() > 0
    assert glare[90, 230]


def test_v178_ruler_detection_is_provisional_and_masks_detected_band():
    rgb = _synthetic_scope()
    field, _ = _optical_field(rgb)
    mask, info = _ruler_mask(rgb, field)
    assert info["provisional"] is True
    assert "pixels_per_mm" in info
    assert "confidence" in info
    # Synthetic pattern should at least identify a candidate ruler region.
    assert info["detected"] is True
    assert mask.sum() > 0


def test_v178_metrics_are_interpretable_relative_measurements():
    rgb = _synthetic_scope()
    field, _ = _optical_field(rgb)
    glare = _glare_mask(rgb, field)
    hair = _hair_mask(rgb, field)
    ruler, _ = _ruler_mask(rgb, field)
    valid = field & ~glare & ~hair & ~ruler
    out = _metrics(rgb, valid)
    assert out["measurement_status"] == "provisional_relative_only"
    assert out["valid_skin_pixels"] > 500
    assert set(out) >= {"redness", "pigmentation", "texture"}
    assert "median_relative_a" in out["redness"]
    assert "median_inverse_lightness" in out["pigmentation"]
    assert "laplacian_abs_mean" in out["texture"]


def test_v178_full_analysis_writes_debug_masks(tmp_path):
    path = tmp_path / "scope.jpg"
    Image.fromarray(_synthetic_scope()).save(path, quality=95)
    result = analyze_image(path, tmp_path)
    assert result["analysis_version"] == VERSION == "1.7.8"
    assert result["analysis_type"] == "classical_interpretable_foundation"
    assert result["validated_for_de500"] is False
    assert result["clinically_calibrated"] is False
    assert result["masks"]["valid_skin_fraction"] > 0
    for name in ("valid_skin", "glare", "hair", "ruler", "optical_field"):
        assert (tmp_path / result["artifacts"][name]).exists()


def test_v178_api_gates_analysis_to_accepted_longitudinal_captures_and_deltas():
    api = API.read_text(encoding="utf-8")
    assert '/v1/dermatoscope/captures/{capture_id}/analyze' in api
    assert '/v1/dermatoscope/captures/{capture_id}/analysis' in api
    assert 'Only accepted captures can enter longitudinal analysis' in api
    assert "longitudinal_status='accepted'" in api
    assert 'result["delta"] = _numeric_delta' in api
    assert '"delta_status"] = "provisional_relative_only"' in api
    assert 'simulator=?' in api


def test_v178_is_installed_after_session_recovery_without_touching_frozen_rgb():
    resume = RESUME.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "from skin_ai.dermatoscope_analysis_v178 import install_dermatoscope_analysis_v178" in resume
    assert "install_dermatoscope_analysis_v178(product_api)" in resume
    assert "install_dermatoscope_resume_v177(product_api)" in entry
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
