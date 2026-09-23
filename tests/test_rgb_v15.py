import numpy as np

from skin_ai.rgb_engine_v15 import RGBAnalysisEngine


def synthetic_face_image():
    h = w = 360
    img = np.full((h, w, 3), [198, 150, 132], dtype=np.uint8)
    yy, xx = np.ogrid[:h, :w]
    grad = ((xx - 180) / 180 * 10).astype(np.int16)
    for c in range(3):
        img[..., c] = np.clip(img[..., c].astype(np.int16) + grad, 0, 255).astype(np.uint8)

    # Red cheek patch that should survive V1.5 confidence masking.
    img[155:180, 105:135] = [230, 112, 108]
    # Compact dark cheek patch that should remain measurable.
    img[205:225, 220:242] = [125, 90, 82]
    # Dark horizontal eyebrow-like structures should be in the geometry-risk zone.
    img[125:132, 105:155] = [65, 50, 48]
    img[125:132, 205:255] = [65, 50, 48]
    # Dense lower-face dark/high-gradient pixels imitate stubble.
    for y in range(245, 285, 6):
        for x in range(135, 225, 7):
            img[y:y+2, x:x+2] = [75, 65, 62]
    return img


def test_v15_keeps_capture_protocol_v14(monkeypatch):
    engine = RGBAnalysisEngine()
    monkeypatch.setattr(engine, '_detect_largest_face', lambda detector, image: (70, 45, 220, 260))
    result = engine.analyze_rgb(synthetic_face_image())
    m = result.metrics
    assert m['rgb_engine_version'] == '1.5'
    assert m['capture_protocol_version'] == '1.4'
    assert m['measurement_mask_version'] == 'feature_confidence_v1_5'
    assert 0 <= m['measurement_confidence_score'] <= 100
    assert 0 <= m['measurement_usable_pixel_fraction'] <= 1
    assert 0 <= m['pigmentation_usable_pixel_fraction'] <= 1
    assert isinstance(m['regional_measurements'], dict)


def test_v15_feature_mask_removes_some_low_confidence_pixels(monkeypatch):
    engine = RGBAnalysisEngine()
    face = (70, 45, 220, 260)
    monkeypatch.setattr(engine, '_detect_largest_face', lambda detector, image: face)
    image = synthetic_face_image()
    base, excluded = engine._face_geometry(image.shape[:2], face)
    valid, _ = engine._adaptive_skin_mask(image, face, base, excluded)
    analysis_valid = valid.astype(bool)
    measurement_valid, pigmentation_valid, info = engine._measurement_masks(image, face, analysis_valid)
    assert measurement_valid.sum() < analysis_valid.sum()
    assert pigmentation_valid.sum() <= measurement_valid.sum()
    assert info['feature_geometry_exclusion_fraction'] > 0
    assert info['hair_like_exclusion_fraction'] >= 0
    assert info['measurement_usable_pixel_fraction'] > 0


def test_v15_red_patch_produces_nonzero_redness(monkeypatch):
    engine = RGBAnalysisEngine()
    monkeypatch.setattr(engine, '_detect_largest_face', lambda detector, image: (70, 45, 220, 260))
    result = engine.analyze_rgb(synthetic_face_image())
    m = result.metrics
    assert m['redness_area_fraction'] > 0
    assert m['red_spot_count_proxy'] >= 1
    assert m['redness_excess_mean_lab_a'] > 0


def test_v15_overlay_uses_only_filtered_components(monkeypatch):
    engine = RGBAnalysisEngine()
    monkeypatch.setattr(engine, '_detect_largest_face', lambda detector, image: (70, 45, 220, 260))
    result = engine.analyze_rgb(synthetic_face_image())
    m = result.metrics
    assert m['red_spot_count_proxy'] == len(m['red_components'])
    assert m['pigmented_spot_count_proxy'] == len(m['pigmentation_components'])
    assert 0 <= m['redness_area_fraction'] <= 1
    assert 0 <= m['pigmentation_area_fraction'] <= 1
    assert m['interpretation']['diagnostic_use'] is False


def test_v15_reference_quality_rejects_cross_version_reference():
    current = {
        'rgb_engine_version': '1.5',
        'capture_protocol_version': '1.4',
        'skin_luminance_median_0_255': 150.0,
        'capture_quality': 'good',
        'capture_quality_score': 92.0,
        'longitudinal_eligible': True,
        'measurement_confidence_score': 90.0,
        'quality_flags': [],
        'quality_guidance': [],
        'quality_subscores': {
            'lighting': 100.0, 'sharpness': 100.0, 'framing': 100.0,
            'centering': 100.0, 'clipping': 100.0, 'symmetry': 100.0,
            'segmentation': 80.0,
        },
    }
    legacy = {'rgb_engine_version': '1.1', 'skin_luminance_median_0_255': 120.0}
    out = RGBAnalysisEngine.apply_reference_capture_quality(current.copy(), legacy)
    assert 'reference_exposure_delta_ev' not in out


def test_v15_low_measurement_confidence_blocks_trend_eligibility():
    current = {
        'rgb_engine_version': '1.5',
        'capture_protocol_version': '1.4',
        'skin_luminance_median_0_255': 150.0,
        'capture_quality': 'good',
        'capture_quality_score': 95.0,
        'longitudinal_eligible': True,
        'measurement_confidence_score': 40.0,
        'quality_flags': [],
        'quality_guidance': [],
        'quality_subscores': {
            'lighting': 100.0, 'sharpness': 100.0, 'framing': 100.0,
            'centering': 100.0, 'clipping': 100.0, 'symmetry': 100.0,
            'segmentation': 90.0,
        },
    }
    reference = {
        'rgb_engine_version': '1.5',
        'skin_luminance_median_0_255': 150.0,
    }
    out = RGBAnalysisEngine.apply_reference_capture_quality(current, reference)
    assert out['capture_quality'] == 'good'
    assert out['longitudinal_eligible'] is False
    assert out['longitudinal_reason'] == 'measurement_confidence_low'
