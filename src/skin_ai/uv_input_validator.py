from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass
class UVInputValidation:
    accepted: bool
    score: float
    flags: list[str]
    guidance: list[str]
    features: dict[str, Any]
    validator_version: str
    profile: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class UVInputValidator:
    """Conservative preflight gate for the current UVFD-like workflow.

    This does not prove that an image was captured under UV illumination. It is
    designed to reject obvious ordinary RGB/natural-scene inputs before the UV
    artifact/porphyrin pipeline runs. V1 is calibrated to the close-up
    fluorescence-dermatoscopy profile used to develop the current UV engine.
    """

    VERSION = "1.0"
    PROFILE = "uvfd_like_closeup_v1"

    def __init__(self) -> None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.face_detector = cv2.CascadeClassifier(str(cascade_path))
        if self.face_detector.empty():
            raise RuntimeError(f"Unable to load OpenCV face detector: {cascade_path}")

    def _largest_face_fraction(self, image_rgb: np.ndarray) -> float:
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape
        min_side = max(48, int(min(h, w) * 0.10))
        faces = self.face_detector.detectMultiScale(
            cv2.equalizeHist(gray), scaleFactor=1.08, minNeighbors=5,
            minSize=(min_side, min_side),
        )
        if len(faces) == 0:
            return 0.0
        _, _, fw, fh = max(faces, key=lambda r: int(r[2]) * int(r[3]))
        return float((fw * fh) / max(1, h * w))

    @staticmethod
    def _features(image_rgb: np.ndarray, face_fraction: float) -> dict[str, Any]:
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        small = cv2.resize(gray, (256, 256), interpolation=cv2.INTER_AREA)
        blur = cv2.GaussianBlur(small, (0, 0), 5.0)
        residual = np.abs(small.astype(np.float32) - blur.astype(np.float32))
        p05 = float(np.percentile(gray, 5))
        p95 = float(np.percentile(gray, 95))
        return {
            "frontal_face_area_fraction": float(face_fraction),
            "gray_p05_0_255": p05,
            "gray_p95_0_255": p95,
            "gray_p05_p95_range": float(p95 - p05),
            "gray_std": float(gray.std()),
            "local_residual_mean": float(residual.mean()),
            "height": int(image_rgb.shape[0]),
            "width": int(image_rgb.shape[1]),
        }

    def validate(self, image_rgb: np.ndarray) -> UVInputValidation:
        if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
            return UVInputValidation(False, 0.0, ["invalid_rgb_shape"], ["Upload a standard RGB PNG or JPEG exported by the UV capture device."], {}, self.VERSION, self.PROFILE)
        if min(image_rgb.shape[:2]) < 160:
            return UVInputValidation(False, 0.0, ["image_too_small"], ["Use the original UV capture at 160 px or larger on the shortest side."], {"height": int(image_rgb.shape[0]), "width": int(image_rgb.shape[1])}, self.VERSION, self.PROFILE)

        face_fraction = self._largest_face_fraction(image_rgb)
        f = self._features(image_rgb, face_fraction)
        score = 100.0
        flags: list[str] = []

        # Current UV engine was developed on close-up dermatoscopy crops, not
        # ordinary full-face portraits. A large frontal face is therefore a
        # strong wrong-modality signal for this V1 profile.
        if face_fraction >= 0.10:
            score -= 80.0
            flags.append("ordinary_frontal_photo_detected")

        # UVFD development samples have relatively compressed scene contrast;
        # broad natural-scene tonal ranges/backgrounds are a wrong-input cue.
        if f["gray_p05_0_255"] < 30:
            score -= 25.0
            flags.append("very_dark_natural_scene_background")
        elif f["gray_p05_0_255"] < 45:
            score -= 10.0

        if f["gray_p05_p95_range"] > 120:
            score -= 30.0
            flags.append("natural_scene_dynamic_range")
        elif f["gray_p05_p95_range"] > 100:
            score -= 15.0

        if f["gray_std"] > 42:
            score -= 30.0
            flags.append("natural_scene_contrast")
        elif f["gray_std"] > 35:
            score -= 15.0

        if f["local_residual_mean"] > 12:
            score -= 20.0
            flags.append("natural_scene_detail_profile")

        score = float(np.clip(score, 0.0, 100.0))
        accepted = bool(score >= 60.0 and "ordinary_frontal_photo_detected" not in flags)

        guidance_map = {
            "ordinary_frontal_photo_detected": "Switch to Phone RGB for ordinary face photos. UV mode currently expects a close-up UV-fluorescence/dermatoscopy image.",
            "very_dark_natural_scene_background": "Use the original UV capture rather than a darkened or edited normal photo.",
            "natural_scene_dynamic_range": "Upload the direct UV-device image; avoid normal photographs with bright and dark scene backgrounds.",
            "natural_scene_contrast": "Use an unedited close-up UV-fluorescence capture from the supported workflow.",
            "natural_scene_detail_profile": "This image looks more like a normal scene than the current close-up UV capture profile.",
        }
        guidance = [guidance_map[x] for x in flags if x in guidance_map]
        if not guidance:
            guidance = ["Input is compatible with the current UVFD-like close-up profile. Passing this gate does not independently verify UV illumination."]

        f["passing_does_not_verify_uv"] = True
        f["validation_scope"] = "obvious wrong-modality rejection for UVFD-like close-up fluorescence dermatoscopy"
        return UVInputValidation(accepted, round(score, 1), flags, guidance, f, self.VERSION, self.PROFILE)
