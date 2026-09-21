import numpy as np
import pytest

from skin_ai.rgb_engine import RGBAnalysisEngine


def synthetic_face_image():
    h=w=360
    img=np.full((h,w,3),[198,150,132],dtype=np.uint8)
    yy,xx=np.ogrid[:h,:w]
    grad=((xx-180)/180*10).astype(np.int16)
    for c in range(3):
        img[...,c]=np.clip(img[...,c].astype(np.int16)+grad,0,255).astype(np.uint8)
    img[150:175,115:140]=[225,105,105]
    img[205:225,215:240]=[125,90,82]
    return img


def test_rgb_engine_returns_finite_proxies_and_skin_region(monkeypatch):
    engine=RGBAnalysisEngine()
    monkeypatch.setattr(engine,'_detect_largest_face',lambda detector,image:(70,45,220,260))
    result=engine.analyze_rgb(synthetic_face_image())
    m=result.metrics
    for key in ['redness_index_proxy','redness_area_fraction','pigmentation_area_fraction','texture_index_proxy','skin_region_fraction_of_face']:
        assert np.isfinite(m[key])
    assert 0 <= m['redness_area_fraction'] <= 1
    assert 0 <= m['pigmentation_area_fraction'] <= 1
    assert 0 < m['skin_region_fraction_of_face'] <= 1
    assert m['red_spot_count_proxy'] >= 0
    assert m['pigmented_spot_count_proxy'] >= 0
    assert m['rgb_engine_version'] == '1.1'
    assert m['segmentation_method'] in {'adaptive_lab_chroma_v1_1','geometry_exposure_fallback_v1_1'}
    assert result.skin_region_rgb.shape == (360,360,3)
    assert result.overlay_rgb.shape == (360,360,3)
    assert m['interpretation']['diagnostic_use'] is False


def test_feature_exclusions_are_smooth_not_rectangular(monkeypatch):
    engine=RGBAnalysisEngine()
    face=(70,45,220,260)
    base, excluded=engine._face_geometry((360,360),face)
    assert base.max() == 255
    assert excluded.max() == 255
    # Elliptical masks should contain partial rows, not full rectangular blocks.
    row=excluded[45+int(260*0.38)]
    transitions=np.count_nonzero(row[1:] != row[:-1])
    assert transitions >= 4


def test_rgb_engine_rejects_missing_face(monkeypatch):
    engine=RGBAnalysisEngine()
    monkeypatch.setattr(engine,'_detect_largest_face',lambda detector,image:None)
    with pytest.raises(ValueError,match='No frontal face detected'):
        engine.analyze_rgb(np.full((360,360,3),180,dtype=np.uint8))
