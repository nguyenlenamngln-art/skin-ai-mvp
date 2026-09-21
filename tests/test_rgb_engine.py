import numpy as np
import pytest

from skin_ai.rgb_engine import RGBAnalysisEngine


def synthetic_face_image():
    h=w=360
    img=np.full((h,w,3),[198,150,132],dtype=np.uint8)
    yy,xx=np.ogrid[:h,:w]
    grad=((xx-180)/180*10).astype(np.int16)
    for c in range(3): img[...,c]=np.clip(img[...,c].astype(np.int16)+grad,0,255).astype(np.uint8)
    img[150:175,115:140]=[225,105,105]
    img[205:225,215:240]=[125,90,82]
    return img


def test_rgb_engine_returns_finite_proxies_and_skin_region(monkeypatch):
    engine=RGBAnalysisEngine(); monkeypatch.setattr(engine,'_detect_largest_face',lambda detector,image:(70,45,220,260))
    result=engine.analyze_rgb(synthetic_face_image()); m=result.metrics
    for key in ['redness_index_proxy','redness_area_fraction','pigmentation_area_fraction','texture_index_proxy','skin_region_fraction_of_face','capture_quality_score','skin_luminance_median_0_255','segmentation_regularity_score']:
        assert np.isfinite(m[key])
    assert 0 <= m['redness_area_fraction'] <= 1
    assert 0 <= m['pigmentation_area_fraction'] <= 1
    assert 0 <= m['capture_quality_score'] <= 100
    assert 0 <= m['segmentation_regularity_score'] <= 100
    assert m['capture_quality'] in {'good','usable','poor'}
    assert isinstance(m['longitudinal_eligible'], bool)
    assert m['capture_protocol_version'] == '1.1'
    assert m['rgb_engine_version'] == '1.1'
    assert result.skin_region_rgb.shape == (360,360,3)
    assert result.overlay_rgb.shape == (360,360,3)
    assert m['interpretation']['diagnostic_use'] is False


def test_feature_exclusions_are_smooth_not_rectangular():
    engine=RGBAnalysisEngine(); face=(70,45,220,260)
    base, excluded=engine._face_geometry((360,360),face)
    assert base.max() == 255 and excluded.max() == 255
    row=excluded[45+int(260*0.38)]
    assert np.count_nonzero(row[1:] != row[:-1]) >= 4


def test_capture_quality_detects_too_dark():
    image=np.full((360,360,3),35,dtype=np.uint8)
    mask=np.zeros((360,360),dtype=np.uint8); mask[70:300,90:270]=255
    q=RGBAnalysisEngine._quality(image,(90,55,180,250),mask)
    assert q['capture_quality'] == 'poor'
    assert 'too_dark' in q['quality_flags']
    assert q['longitudinal_eligible'] is False
    assert q['quality_guidance']
    assert q['quality_subscores']['lighting'] < 100


def test_reference_exposure_mismatch_blocks_longitudinal_use():
    current={
        'rgb_engine_version':'1.1',
        'capture_protocol_version':'1.1',
        'skin_luminance_median_0_255':75.0,
        'capture_quality':'usable',
        'capture_quality_score':75.0,
        'longitudinal_eligible':False,
        'quality_flags':['blurry'],
        'quality_guidance':['Hold the phone steady and refocus before capture.'],
        'quality_subscores':{'lighting':100.0,'sharpness':40.0,'framing':90.0,'centering':100.0,'clipping':100.0,'symmetry':90.0,'segmentation':90.0},
    }
    reference={'rgb_engine_version':'1.1','skin_luminance_median_0_255':162.0}
    out=RGBAnalysisEngine.apply_reference_capture_quality(current,reference)
    assert out['reference_exposure_delta_ev'] < -1.0
    assert out['reference_lighting_score'] == 0.0
    assert 'lighting_not_comparable' in out['quality_flags']
    assert out['longitudinal_eligible'] is False
    assert any('baseline' in x.lower() for x in out['quality_guidance'])


def test_segmentation_regularity_flags_fragmented_mask():
    base=np.zeros((300,300),dtype=np.uint8)
    cv=np.indices(base.shape)
    yy,xx=cv
    base[((xx-150)/100)**2+((yy-150)/120)**2 <= 1]=255
    skin=base.copy()
    skin[80:130,100:140]=0
    skin[80:130,160:200]=0
    skin[180:210,130:170]=0
    skin[130:150,145:155]=0
    skin[20:25,20:25]=255
    q=RGBAnalysisEngine._segmentation_regularity(skin,base)
    assert q['segmentation_unstable'] is True
    assert q['segmentation_regularity_score'] < 100


def test_rgb_engine_rejects_missing_face(monkeypatch):
    engine=RGBAnalysisEngine(); monkeypatch.setattr(engine,'_detect_largest_face',lambda detector,image:None)
    with pytest.raises(ValueError,match='No frontal face detected'):
        engine.analyze_rgb(np.full((360,360,3),180,dtype=np.uint8))
