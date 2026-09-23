import numpy as np

from skin_ai.rgb_engine_v152 import RGBAnalysisEngine


def ellipse_base(shape=(260, 260)):
    yy, xx = np.indices(shape)
    return ((((xx-130)/88)**2 + ((yy-132)/108)**2) <= 1).astype(np.uint8) * 255


def test_v152_outer_boundary_ignores_internal_feature_holes():
    base = ellipse_base()
    skin = base > 0
    # Deliberate internal holes imitate eye/lip exclusions.
    skin[95:112, 82:112] = False
    skin[95:112, 148:178] = False
    skin[174:188, 108:152] = False
    face = (42, 24, 176, 216)

    regular = RGBAnalysisEngine._anatomical_regularity(skin, face)
    # Internal feature exclusions should not explode outer contour complexity.
    assert regular['skin_mask_component_count'] <= 1
    assert regular['skin_mask_hole_count'] <= 1
    assert regular['anatomical_outer_boundary_score'] >= 80
    assert regular['anatomical_skin_support_fraction'] > 0.60


def test_v152_stabilization_bridges_small_supported_notch_only():
    base = ellipse_base()
    excluded = np.zeros_like(base)
    raw = base > 0
    # Small cheek notch should be repairable.
    raw[128:138, 64:72] = False
    face = (42, 24, 176, 216)
    stabilized, info = RGBAnalysisEngine._stabilize_anatomical_measurement_mask(raw, base, excluded, face)

    assert info['anatomical_mask_fallback'] is False
    assert info['anatomical_mask_added_fraction'] <= 0.05
    assert info['anatomical_mask_retention_fraction'] >= 0.90
    assert stabilized.sum() >= raw.sum()


def test_v152_stabilization_falls_back_on_large_unsupported_change():
    base = ellipse_base()
    excluded = np.zeros_like(base)
    raw = np.zeros_like(base, dtype=bool)
    raw[65:115, 72:118] = True
    raw[145:195, 142:188] = True
    face = (42, 24, 176, 216)
    stabilized, info = RGBAnalysisEngine._stabilize_anatomical_measurement_mask(raw, base, excluded, face)

    assert info['anatomical_mask_fallback'] is True
    assert np.array_equal(stabilized, raw)


def test_v152_keeps_v151_regional_trend_gate():
    assert RGBAnalysisEngine.REGIONAL_TREND_CONFIDENCE_MIN == 0.65
    assert RGBAnalysisEngine.REGIONAL_TREND_MIN_PIXELS == 250
    assert RGBAnalysisEngine.VERSION == '1.5.2'
    assert RGBAnalysisEngine.CAPTURE_PROTOCOL_VERSION == '1.4'
