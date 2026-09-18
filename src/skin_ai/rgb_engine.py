from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


@dataclass
class RGBAnalysisResult:
    metrics: dict[str, Any]
    original_rgb: np.ndarray
    redness_map_rgb: np.ndarray
    pigmentation_map_rgb: np.ndarray
    overlay_rgb: np.ndarray


class RGBAnalysisEngine:
    """Transparent phone-RGB skin tracking baseline.

    This engine is intentionally a measurement/proxy pipeline, not a disease
    classifier. It detects a frontal face, applies capture-quality checks, and
    measures relative chromatic/texture changes inside a conservative facial
    region. Metrics are most useful longitudinally when capture conditions are
    similar.
    """

    def __init__(self) -> None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.face_detector = cv2.CascadeClassifier(str(cascade_path))
        if self.face_detector.empty():
            raise RuntimeError(f"Unable to load OpenCV face detector: {cascade_path}")

    @staticmethod
    def _detect_largest_face(detector: cv2.CascadeClassifier, image_rgb: np.ndarray) -> tuple[int, int, int, int] | None:
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.equalizeHist(gray)
        h, w = gray.shape
        min_side = max(48, int(min(h, w) * 0.12))
        faces = detector.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(min_side, min_side))
        if len(faces) == 0:
            return None
        x, y, fw, fh = max(faces, key=lambda r: int(r[2]) * int(r[3]))
        return int(x), int(y), int(fw), int(fh)

    @staticmethod
    def _face_mask(shape: tuple[int, int], face: tuple[int, int, int, int]) -> np.ndarray:
        h, w = shape
        x, y, fw, fh = face
        mask = np.zeros((h, w), np.uint8)
        center = (x + fw // 2, y + int(fh * 0.52))
        axes = (max(1, int(fw * 0.43)), max(1, int(fh * 0.48)))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)

        def rect(rx0: float, ry0: float, rx1: float, ry1: float) -> None:
            x0 = max(0, int(x + fw * rx0)); y0 = max(0, int(y + fh * ry0))
            x1 = min(w, int(x + fw * rx1)); y1 = min(h, int(y + fh * ry1))
            cv2.rectangle(mask, (x0, y0), (x1, y1), 0, -1)

        rect(0.08, 0.20, 0.47, 0.47)
        rect(0.53, 0.20, 0.92, 0.47)
        rect(0.23, 0.70, 0.77, 0.91)
        return mask

    @staticmethod
    def _quality(image_rgb: np.ndarray, face: tuple[int, int, int, int], mask: np.ndarray) -> dict[str, Any]:
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        valid = mask > 0
        x, y, fw, fh = face
        face_area_fraction = float((fw * fh) / (image_rgb.shape[0] * image_rgb.shape[1]))
        brightness = float(hsv[..., 2][valid].mean()) if valid.any() else 0.0
        blur_var = float(cv2.Laplacian(gray[y:y+fh, x:x+fw], cv2.CV_64F).var())
        clipped_dark = float((hsv[..., 2][valid] < 25).mean()) if valid.any() else 1.0
        clipped_bright = float((hsv[..., 2][valid] > 245).mean()) if valid.any() else 1.0

        flags: list[str] = []
        if brightness < 65: flags.append("too_dark")
        if brightness > 210: flags.append("too_bright")
        if blur_var < 45: flags.append("blurry")
        if face_area_fraction < 0.10: flags.append("face_too_small")
        if face_area_fraction > 0.78: flags.append("face_too_close")
        if clipped_dark > 0.12: flags.append("shadow_clipping")
        if clipped_bright > 0.12: flags.append("highlight_clipping")

        return {
            "capture_quality": "good" if not flags else ("usable" if len(flags) <= 2 else "poor"),
            "quality_flags": flags,
            "brightness_mean_0_255": brightness,
            "sharpness_laplacian_var": blur_var,
            "face_area_fraction": face_area_fraction,
            "dark_clipped_fraction": clipped_dark,
            "bright_clipped_fraction": clipped_bright,
        }

    @staticmethod
    def _valid_skin_mask(image_rgb: np.ndarray, base_mask: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        valid = (base_mask > 0) & (hsv[..., 2] > 30) & (hsv[..., 2] < 248)
        valid &= hsv[..., 1] < 215
        return valid

    @staticmethod
    def _connected_count(binary: np.ndarray, min_area: int, max_area: int) -> tuple[int, list[dict[str, float]]]:
        n, _, stats, centroids = cv2.connectedComponentsWithStats(binary.astype(np.uint8), 8)
        comps = []
        for i in range(1, n):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if min_area <= area <= max_area:
                comps.append({"x": float(centroids[i, 0]), "y": float(centroids[i, 1]), "area_px": area})
        return len(comps), comps

    def analyze_rgb(self, image_rgb: np.ndarray) -> RGBAnalysisResult:
        if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
            raise ValueError("Expected an RGB image with shape HxWx3")
        if min(image_rgb.shape[:2]) < 160:
            raise ValueError("Image is too small; use at least 160 px on the shortest side")

        face = self._detect_largest_face(self.face_detector, image_rgb)
        if face is None:
            raise ValueError("No frontal face detected. Use a well-lit, front-facing photo with one face visible.")

        base_mask = self._face_mask(image_rgb.shape[:2], face)
        valid = self._valid_skin_mask(image_rgb, base_mask)
        if int(valid.sum()) < 2500:
            raise ValueError("Not enough usable facial skin pixels. Try a closer, evenly lit front-facing photo.")

        quality = self._quality(image_rgb, face, base_mask)
        rgb = image_rgb.astype(np.float32)
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        L, a = lab[..., 0], lab[..., 1]

        denom = rgb.sum(axis=2) + 1.0
        red_chroma = rgb[..., 0] / denom
        redness_index = float(red_chroma[valid].mean())

        a_blur = cv2.GaussianBlur(a, (0, 0), 5.0)
        red_resid = a - a_blur
        rv = red_resid[valid]
        r_med = float(np.median(rv)); r_mad = float(np.median(np.abs(rv - r_med))) + 1.0
        red_thr = max(4.0, r_med + 2.2 * r_mad)
        redness_mask = valid & (red_resid > red_thr)
        redness_mask = cv2.morphologyEx(redness_mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2,2),np.uint8)) > 0
        red_spot_count, _ = self._connected_count(redness_mask, 5, 1200)

        L_blur = cv2.GaussianBlur(L, (0, 0), 7.0)
        dark_resid = L_blur - L
        dv = dark_resid[valid]
        d_med = float(np.median(dv)); d_mad = float(np.median(np.abs(dv - d_med))) + 1.0
        dark_thr = max(7.0, d_med + 2.2 * d_mad)
        pigmentation_mask = valid & (dark_resid > dark_thr)
        pigmentation_mask = cv2.morphologyEx(pigmentation_mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2,2),np.uint8)) > 0
        pigmentation_count, _ = self._connected_count(pigmentation_mask, 5, 1600)

        local_texture = np.abs(L - cv2.GaussianBlur(L, (0, 0), 1.6))
        texture_index = float(local_texture[valid].mean() / 255.0)
        valid_n = max(1, int(valid.sum()))

        x, y, fw, fh = face
        metrics: dict[str, Any] = {
            "redness_index_proxy": redness_index,
            "redness_area_fraction": float(redness_mask.sum() / valid_n),
            "red_spot_count_proxy": red_spot_count,
            "pigmentation_area_fraction": float(pigmentation_mask.sum() / valid_n),
            "pigmented_spot_count_proxy": pigmentation_count,
            "texture_index_proxy": texture_index,
            "face_bbox": {"x": x, "y": y, "w": fw, "h": fh},
            "valid_skin_area_fraction_of_image": float(valid.mean()),
            **quality,
            "interpretation": {
                "measurement_type": "relative_phone_rgb_proxies",
                "best_use": "longitudinal_tracking_under_similar_capture_conditions",
                "diagnostic_use": False,
                "not_equivalent_to": ["dermatologist assessment", "polarized imaging", "UV fluorescence imaging"],
            },
        }

        redness_map = image_rgb.copy(); pigmentation_map = image_rgb.copy(); overlay = image_rgb.copy()
        redness_map[~valid] = (redness_map[~valid] * 0.35).astype(np.uint8)
        pigmentation_map[~valid] = (pigmentation_map[~valid] * 0.35).astype(np.uint8)
        overlay[~valid] = (overlay[~valid] * 0.55).astype(np.uint8)
        redness_map[redness_mask] = (0.45 * redness_map[redness_mask] + 0.55 * np.array([255,55,70])).astype(np.uint8)
        pigmentation_map[pigmentation_mask] = (0.45 * pigmentation_map[pigmentation_mask] + 0.55 * np.array([90,70,210])).astype(np.uint8)
        overlay[redness_mask] = (0.50 * overlay[redness_mask] + 0.50 * np.array([255,55,70])).astype(np.uint8)
        overlay[pigmentation_mask] = (0.50 * overlay[pigmentation_mask] + 0.50 * np.array([90,70,210])).astype(np.uint8)
        cv2.rectangle(overlay, (x, y), (x + fw, y + fh), (80,210,140), 2)

        return RGBAnalysisResult(metrics, image_rgb, redness_map, pigmentation_map, overlay)

    def analyze_file(self, path: str | Path) -> RGBAnalysisResult:
        return self.analyze_rgb(np.asarray(Image.open(path).convert("RGB")))

    @staticmethod
    def save_result(result: RGBAnalysisResult, out_dir: str | Path) -> None:
        import json
        out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(result.original_rgb).save(out / "original.jpg", quality=92)
        Image.fromarray(result.redness_map_rgb).save(out / "redness_map.png")
        Image.fromarray(result.pigmentation_map_rgb).save(out / "pigmentation_map.png")
        Image.fromarray(result.overlay_rgb).save(out / "rgb_overlay.png")
        (out / "metrics.json").write_text(json.dumps(result.metrics, indent=2))
