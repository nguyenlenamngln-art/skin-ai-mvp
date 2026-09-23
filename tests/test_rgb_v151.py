import numpy as np

from skin_ai.rgb_engine_v151 import RGBAnalysisEngine


def ellipse_base(shape=(240, 240)):
    yy, xx = np.indices(shape)
    return ((((xx-120)/80)**2 + ((yy-120)/100)**2) <= 1).astype(np.uint8) * 255


def test_v151_refinement_keeps_dominant_component_and_removes_islands():
    base = ellipse_base()
    excluded = np.zeros_like(base)
    valid = base > 0
    valid[30:36, 30:36] = True
    refined, info = RGBAnalysisEngine._refine_skin_mask(valid, base, excluded)
    assert info['segmentation_component_count_after_refinement'] <= 1
    assert info['segmentation_largest_component_fraction_after_refinement'] >= 0.99
    assert info['segmentation_refinement_retention_fraction'] >= 0.82
    assert refined.sum() <= valid.sum() + 500


def test_v151_refinement_falls_back_if_too_much_skin_would_be_lost():
    base = ellipse_base()
    excluded = np.zeros_like(base)
    valid = np.zeros_like(base, dtype=bool)
    valid[50:85, 65:100] = True
    valid[145:180, 140:175] = True
    refined, info = RGBAnalysisEngine._refine_skin_mask(valid, base, excluded)
    assert info['segmentation_refinement_fallback'] is True
    assert np.array_equal(refined, valid)


def test_v151_regional_trend_gate_uses_confidence_and_pixel_count():
    face = (20, 20, 200, 200)
    shape = (240, 240)
    analysis = np.zeros(shape, dtype=bool)
    analysis[20:220, 20:220] = True
    measurement = analysis.copy()
    pigment = analysis.copy()
    red = np.zeros(shape, dtype=bool)
    pig = np.zeros(shape, dtype=bool)

    # Reduce center-face usable coverage below the 65% confidence gate.
    center = RGBAnalysisEngine._rect_region(shape, face, 0.38, 0.42, 0.62, 0.68)
    measurement[center] = False
    pigment[center] = False

    regions = RGBAnalysisEngine._regional_measurements(face, analysis, measurement, pigment, red, pig)
    assert regions['center_face']['trend_eligible'] is False
    assert regions['center_face']['trend_reason'] == 'usable_pixel_confidence_low'
    assert any(v['trend_eligible'] for k, v in regions.items() if k != 'center_face')
