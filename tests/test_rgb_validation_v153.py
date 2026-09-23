import numpy as np
import cv2

from skin_ai.rgb_engine_v152 import RGBAnalysisEngineV152
from skin_ai.rgb_validation_v153 import _iou, validate_rgb_image


def _synthetic_phone_rgb() -> np.ndarray:
    image = np.full((420, 360, 3), 72, dtype=np.uint8)
    cv2.ellipse(image, (180, 205), (90, 125), 0, 0, 360, (188, 142, 118), -1)
    cv2.circle(image, (150, 180), 10, (65, 55, 50), -1)
    cv2.circle(image, (210, 180), 10, (65, 55, 50), -1)
    cv2.ellipse(image, (180, 255), (26, 9), 0, 0, 360, (120, 72, 68), -1)
    return image


def test_v153_iou_identity():
    a = np.zeros((20, 20), dtype=bool)
    a[3:16, 5:15] = True
    assert _iou(a, a) == 1.0


def test_v153_real_image_harness_preserves_v152_engine(monkeypatch):
    image = _synthetic_phone_rgb()
    monkeypatch.setattr(
        RGBAnalysisEngineV152,
        "_detect_largest_face",
        staticmethod(lambda detector, image_rgb: (90, 70, 180, 260)),
    )

    report = validate_rgb_image(image, source_name="synthetic_phone_rgb.png")

    assert report["validation_version"] == "1.5.3"
    assert report["engine_under_test"] == "1.5.2"
    assert report["face_detected"] is True
    assert report["summary"]["variants_detected"] == 5
    assert report["summary"]["fallback_rate"] <= 0.20
    assert report["summary"]["min_anatomical_skin_support_fraction"] >= 0.70


def test_v153_reports_missing_face(monkeypatch):
    image = np.full((300, 300, 3), 128, dtype=np.uint8)
    monkeypatch.setattr(
        RGBAnalysisEngineV152,
        "_detect_largest_face",
        staticmethod(lambda detector, image_rgb: None),
    )

    report = validate_rgb_image(image, source_name="no_face.png")

    assert report["validation_pass"] is False
    assert report["failure_reasons"] == ["baseline_face_not_detected"]
