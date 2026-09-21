import numpy as np

from skin_ai.uv_input_validator import UVInputValidator


def smooth_uvfd_like_image() -> np.ndarray:
    h = w = 512
    yy, xx = np.ogrid[:h, :w]
    base = 125 + 12 * np.sin(xx / 55.0) + 9 * np.cos(yy / 70.0)
    img = np.stack([
        base - 18,
        base + 2,
        base + 24,
    ], axis=2)
    return np.clip(img, 0, 255).astype(np.uint8)


def natural_portrait_like_image() -> np.ndarray:
    h = w = 512
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = [18, 24, 42]
    img[60:460, 100:410] = [120, 92, 82]
    img[120:220, :90] = [235, 235, 235]
    img[280:500, 400:512] = [25, 45, 125]
    return img


def test_uvfd_like_closeup_is_accepted(monkeypatch):
    validator = UVInputValidator()
    monkeypatch.setattr(validator, '_largest_face_fraction', lambda image: 0.0)
    result = validator.validate(smooth_uvfd_like_image())
    assert result.accepted is True
    assert result.score >= 60
    assert result.validator_version == '1.0'
    assert result.profile == 'uvfd_like_closeup_v1'
    assert result.features['passing_does_not_verify_uv'] is True


def test_large_frontal_photo_is_rejected(monkeypatch):
    validator = UVInputValidator()
    monkeypatch.setattr(validator, '_largest_face_fraction', lambda image: 0.18)
    result = validator.validate(natural_portrait_like_image())
    assert result.accepted is False
    assert 'ordinary_frontal_photo_detected' in result.flags
    assert any('Phone RGB' in item for item in result.guidance)


def test_small_input_is_rejected_without_claiming_uv():
    validator = UVInputValidator()
    result = validator.validate(np.full((100, 100, 3), 120, dtype=np.uint8))
    assert result.accepted is False
    assert 'image_too_small' in result.flags
