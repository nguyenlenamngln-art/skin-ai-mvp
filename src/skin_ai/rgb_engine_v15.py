from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from skin_ai.rgb_engine import RGBAnalysisEngine as RGBAnalysisEngineV11
from skin_ai.rgb_engine import RGBAnalysisResult


class RGBAnalysisEngineV15(RGBAnalysisEngineV11):
    """Phone RGB measurement refinement V1.5.

    Capture/repeatability protocol stays V1.4. Measurement V1.5 refines the
    visible-light proxies by excluding low-confidence facial-feature pixels,
    filtering displayed components, and using a robust skin-relative redness
    rule. It remains a research/wellness proxy and is not diagnostic.
    """

    VERSION = "1.5"
    CAPTURE_PROTOCOL_VERSION = "1.4"
    MEASUREMENT_MASK_VERSION = "feature_confidence_v1_5"

    @staticmethod
    def _quality(image_rgb: np.ndarray, face: tuple[int, int, int, int], skin_mask: np.ndarray) -> dict[str, Any]:
        """Reuse the stable quality model while stamping V1.4 capture protocol."""
        metrics = RGBAnalysisEngineV11._quality(image_rgb, face, skin_mask)
        metrics["capture_protocol_version"] = RGBAnalysisEngineV15.CAPTURE_PROTOCOL_VERSION
        return metrics

    @staticmethod
    def _ellipse_mask(
        shape: tuple[int, int],
        face: tuple[int, int, int, int],
        specs: list[tuple[float, float, float, float]],
    ) -> np.ndarray:
        h, w = shape
        x, y, fw, fh = face
        out = np.zeros((h, w), np.uint8)
        for cx, cy, ax, ay in specs:
            cv2.ellipse(
                out,
                (int(x + fw * cx), int(y + fh * cy)),
                (max(1, int(fw * ax)), max(1, int(fh * ay))),
                0,
                0,
                360,
                255,
                -1,
            )
        return out > 0

    @classmethod
    def _measurement_masks(
        cls,
        image_rgb: np.ndarray,
        face: tuple[int, int, int, int],
        analysis_valid: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
        """Build conservative high-confidence masks for V1.5 measurements.

        Coarse geometry suppresses eyebrows/eyes, lips and nostril boundaries.
        A lower-face high-gradient/local-darkness detector additionally
        suppresses likely stubble/hair pixels from pigmentation measurement.
        """
        low_conf_geometry = cls._ellipse_mask(
            image_rgb.shape[:2],
            face,
            [
                (0.32, 0.35, 0.18, 0.11),
                (0.68, 0.35, 0.18, 0.11),
                (0.50, 0.62, 0.12, 0.065),
                (0.50, 0.77, 0.24, 0.11),
            ],
        )

        interior = cv2.erode(
            analysis_valid.astype(np.uint8),
            np.ones((3, 3), np.uint8),
            iterations=1,
        ) > 0
        measurement_valid = interior & ~low_conf_geometry
        if int(measurement_valid.sum()) < 1200:
            measurement_valid = analysis_valid & ~low_conf_geometry
        if int(measurement_valid.sum()) < 800:
            measurement_valid = analysis_valid.copy()

        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        L = lab[..., 0]
        local_dark = cv2.GaussianBlur(L, (0, 0), 1.8) - L
        gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
        gradient = cv2.magnitude(gx, gy)

        h, w = analysis_valid.shape
        x, y, fw, fh = face
        yy, xx = np.indices((h, w))
        lower_face = (
            (yy >= y + int(0.64 * fh))
            & (yy <= y + int(0.94 * fh))
            & (xx >= x + int(0.12 * fw))
            & (xx <= x + int(0.88 * fw))
        )
        lower_sample = measurement_valid & lower_face
        hair_like = np.zeros_like(analysis_valid, dtype=bool)
        if int(lower_sample.sum()) >= 200:
            dark_values = local_dark[lower_sample]
            grad_values = gradient[lower_sample]
            dark_thr = max(4.5, float(np.percentile(dark_values, 76)))
            grad_thr = max(7.0, float(np.percentile(grad_values, 72)))
            hair_like = lower_sample & (local_dark > dark_thr) & (gradient > grad_thr)
            hair_like = cv2.dilate(hair_like.astype(np.uint8), np.ones((2, 2), np.uint8), iterations=1) > 0

        pigmentation_valid = measurement_valid & ~hair_like
        if int(pigmentation_valid.sum()) < 800:
            pigmentation_valid = measurement_valid.copy()

        analysis_n = max(1, int(analysis_valid.sum()))
        measurement_fraction = float(measurement_valid.sum() / analysis_n)
        pigmentation_fraction = float(pigmentation_valid.sum() / analysis_n)
        return measurement_valid, pigmentation_valid, {
            "measurement_usable_pixel_fraction": measurement_fraction,
            "pigmentation_usable_pixel_fraction": pigmentation_fraction,
            "feature_geometry_exclusion_fraction": float((analysis_valid & low_conf_geometry).sum() / analysis_n),
            "hair_like_exclusion_fraction": float((measurement_valid & hair_like).sum() / analysis_n),
        }

    @staticmethod
    def _filter_components(
        binary: np.ndarray,
        min_area: int,
        max_area: int,
        *,
        max_aspect: float,
        min_extent: float,
    ) -> tuple[np.ndarray, list[dict[str, float]]]:
        labels_input = binary.astype(np.uint8)
        n, labels, stats, centroids = cv2.connectedComponentsWithStats(labels_input, 8)
        cleaned = np.zeros_like(labels_input, dtype=np.uint8)
        comps: list[dict[str, float]] = []
        for i in range(1, n):
            area = int(stats[i, cv2.CC_STAT_AREA])
            width = int(stats[i, cv2.CC_STAT_WIDTH])
            height = int(stats[i, cv2.CC_STAT_HEIGHT])
            if not (min_area <= area <= max_area):
                continue
            aspect = max(width / max(1, height), height / max(1, width))
            extent = area / max(1, width * height)
            if aspect > max_aspect or extent < min_extent:
                continue
            cleaned[labels == i] = 1
            comps.append({
                "x": float(centroids[i, 0]),
                "y": float(centroids[i, 1]),
                "area_px": float(area),
                "aspect": float(aspect),
                "extent": float(extent),
            })
        return cleaned > 0, comps

    @staticmethod
    def _rect_region(
        shape: tuple[int, int],
        face: tuple[int, int, int, int],
        rx0: float,
        ry0: float,
        rx1: float,
        ry1: float,
    ) -> np.ndarray:
        h, w = shape
        x, y, fw, fh = face
        out = np.zeros((h, w), dtype=bool)
        x0 = max(0, int(x + fw * rx0)); x1 = min(w, int(x + fw * rx1))
        y0 = max(0, int(y + fh * ry0)); y1 = min(h, int(y + fh * ry1))
        if x1 > x0 and y1 > y0:
            out[y0:y1, x0:x1] = True
        return out

    @classmethod
    def _regional_measurements(
        cls,
        face: tuple[int, int, int, int],
        analysis_valid: np.ndarray,
        measurement_valid: np.ndarray,
        pigmentation_valid: np.ndarray,
        redness_mask: np.ndarray,
        pigmentation_mask: np.ndarray,
    ) -> dict[str, dict[str, float | int]]:
        regions = {
            "forehead": (0.24, 0.16, 0.76, 0.34),
            "left_cheek": (0.08, 0.46, 0.44, 0.70),
            "right_cheek": (0.56, 0.46, 0.92, 0.70),
            "center_face": (0.38, 0.42, 0.62, 0.68),
            "chin": (0.30, 0.68, 0.70, 0.90),
        }
        out: dict[str, dict[str, float | int]] = {}
        for name, spec in regions.items():
            region = cls._rect_region(analysis_valid.shape, face, *spec)
            available = analysis_valid & region
            available_n = int(available.sum())
            if available_n < 40:
                continue
            measured = measurement_valid & region
            pigment_measured = pigmentation_valid & region
            measured_n = int(measured.sum())
            pigment_n = int(pigment_measured.sum())
            out[name] = {
                "confidence": round(float(measured_n / max(1, available_n)), 3),
                "usable_pixels": measured_n,
                "redness_area_fraction": float((redness_mask & region).sum() / max(1, measured_n)),
                "pigmentation_area_fraction": float((pigmentation_mask & region).sum() / max(1, pigment_n)),
            }
        return out

    @classmethod
    def apply_reference_capture_quality(cls, current: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
        out = super().apply_reference_capture_quality(current, reference)
        if float(out.get("measurement_confidence_score", 100.0)) < 55.0:
            out["longitudinal_eligible"] = False
            out["longitudinal_reason"] = "measurement_confidence_low"
        return out

    def analyze_rgb(self, image_rgb: np.ndarray) -> RGBAnalysisResult:
        if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
            raise ValueError("Expected an RGB image with shape HxWx3")
        if min(image_rgb.shape[:2]) < 160:
            raise ValueError("Image is too small; use at least 160 px on the shortest side")

        face = self._detect_largest_face(self.face_detector, image_rgb)
        if face is None:
            raise ValueError("No frontal face detected. Use a well-lit, front-facing photo with one face visible.")

        base, excluded = self._face_geometry(image_rgb.shape[:2], face)
        valid, segmentation = self._adaptive_skin_mask(image_rgb, face, base, excluded)
        if int(valid.sum()) < 2500:
            raise ValueError("Not enough usable facial skin pixels. Try a closer, evenly lit front-facing photo.")

        analysis_valid = cv2.erode(valid.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1) > 0
        if int(analysis_valid.sum()) < 2000:
            analysis_valid = valid

        quality = self._quality(image_rgb, face, valid)
        measurement_valid, pigmentation_valid, mask_info = self._measurement_masks(image_rgb, face, analysis_valid)

        rgb = image_rgb.astype(np.float32)
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        L, a = lab[..., 0], lab[..., 1]
        denom = rgb.sum(axis=2) + 1.0
        red_chroma = rgb[..., 0] / denom
        redness_index = float(red_chroma[measurement_valid].mean())

        a_values = a[measurement_valid]
        a_med = float(np.median(a_values))
        a_mad = max(1.0, float(1.4826 * np.median(np.abs(a_values - a_med))))
        a_blur = cv2.GaussianBlur(a, (0, 0), 5.0)
        red_resid = a - a_blur
        local_values = red_resid[measurement_valid]
        local_med = float(np.median(local_values))
        local_mad = max(0.8, float(1.4826 * np.median(np.abs(local_values - local_med))))
        global_red_thr = a_med + max(2.0, 1.05 * a_mad)
        local_red_thr = local_med + max(0.9, 0.65 * local_mad)
        strong_local_thr = local_med + max(2.4, 1.65 * local_mad)
        redness_raw = measurement_valid & (
            ((a > global_red_thr) & (red_resid > local_red_thr))
            | ((red_resid > strong_local_thr) & (a > a_med + 1.0))
        )
        redness_raw = cv2.morphologyEx(redness_raw.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        redness_raw = cv2.morphologyEx(redness_raw, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0

        x, y, fw, fh = face
        face_px = max(1, fw * fh)
        redness_mask, red_components = self._filter_components(
            redness_raw,
            5,
            max(900, int(face_px * 0.12)),
            max_aspect=5.0,
            min_extent=0.08,
        )
        red_spot_count = len(red_components)

        L_blur = cv2.GaussianBlur(L, (0, 0), 7.0)
        dark_resid = L_blur - L
        dark_values = dark_resid[pigmentation_valid]
        d_med = float(np.median(dark_values))
        d_mad = max(1.0, float(1.4826 * np.median(np.abs(dark_values - d_med))))
        dark_thr = d_med + max(6.0, 2.15 * d_mad)
        pigmentation_raw = pigmentation_valid & (dark_resid > dark_thr)
        pigmentation_raw = cv2.morphologyEx(pigmentation_raw.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0
        pigmentation_mask, pigmentation_components = self._filter_components(
            pigmentation_raw,
            5,
            max(1200, int(face_px * 0.06)),
            max_aspect=3.2,
            min_extent=0.12,
        )
        pigmentation_count = len(pigmentation_components)

        local_texture = np.abs(L - cv2.GaussianBlur(L, (0, 0), 1.6))
        texture_index = float(local_texture[measurement_valid].mean() / 255.0)
        measurement_n = max(1, int(measurement_valid.sum()))
        pigmentation_n = max(1, int(pigmentation_valid.sum()))

        coverage_score = 100.0 * float(mask_info["measurement_usable_pixel_fraction"])
        segmentation_score = float(quality.get("quality_subscores", {}).get("segmentation", 100.0))
        measurement_confidence = float(np.clip(0.70 * coverage_score + 0.30 * segmentation_score, 0.0, 100.0))
        measurement_warnings: list[str] = []
        if measurement_confidence < 55.0:
            measurement_warnings.append("low_measurement_confidence")

        regional = self._regional_measurements(
            face,
            analysis_valid,
            measurement_valid,
            pigmentation_valid,
            redness_mask,
            pigmentation_mask,
        )

        metrics: dict[str, Any] = {
            "rgb_engine_version": self.VERSION,
            "measurement_mask_version": self.MEASUREMENT_MASK_VERSION,
            "redness_index_proxy": redness_index,
            "redness_area_fraction": float(redness_mask.sum() / measurement_n),
            "redness_excess_mean_lab_a": float(np.maximum(a[measurement_valid] - a_med, 0).mean()),
            "redness_threshold_lab_a": float(global_red_thr),
            "red_spot_count_proxy": red_spot_count,
            "pigmentation_area_fraction": float(pigmentation_mask.sum() / pigmentation_n),
            "pigmented_spot_count_proxy": pigmentation_count,
            "pigmentation_dark_residual_threshold": float(dark_thr),
            "texture_index_proxy": texture_index,
            "measurement_confidence_score": round(measurement_confidence, 1),
            "measurement_warnings": measurement_warnings,
            "face_bbox": {"x": x, "y": y, "w": fw, "h": fh},
            "valid_skin_area_fraction_of_image": float(analysis_valid.mean()),
            "regional_measurements": regional,
            "red_components": red_components,
            "pigmentation_components": pigmentation_components,
            **mask_info,
            **segmentation,
            **quality,
            "interpretation": {
                "measurement_type": "relative_phone_rgb_proxies",
                "best_use": "longitudinal_tracking_under_similar_capture_conditions",
                "diagnostic_use": False,
                "segmentation_note": "adaptive color/geometry mask with V1.5 feature-confidence exclusions; not anatomical landmark segmentation",
                "measurement_confidence_note": "low-confidence feature/hair pixels are excluded from V1.5 redness/pigmentation trends",
                "capture_quality_note": "capture score is a repeatability gate, not a clinical quality score",
                "not_equivalent_to": ["dermatologist assessment", "polarized imaging", "UV fluorescence imaging"],
            },
        }

        if measurement_confidence < 55.0:
            metrics["longitudinal_eligible"] = False
            metrics["longitudinal_reason"] = "measurement_confidence_low"

        skin_region = image_rgb.copy()
        skin_region[~valid] = (skin_region[~valid] * 0.22).astype(np.uint8)
        skin_region[valid] = (0.85 * skin_region[valid] + 0.15 * np.array([70, 220, 140])).astype(np.uint8)
        skin_region = self._draw_skin_boundary(skin_region, valid)

        redness_map = image_rgb.copy()
        pigmentation_map = image_rgb.copy()
        overlay = image_rgb.copy()
        redness_map[~measurement_valid] = (redness_map[~measurement_valid] * 0.50).astype(np.uint8)
        pigmentation_map[~pigmentation_valid] = (pigmentation_map[~pigmentation_valid] * 0.50).astype(np.uint8)
        redness_map[redness_mask] = (0.45 * redness_map[redness_mask] + 0.55 * np.array([255, 55, 70])).astype(np.uint8)
        pigmentation_map[pigmentation_mask] = (0.45 * pigmentation_map[pigmentation_mask] + 0.55 * np.array([90, 70, 210])).astype(np.uint8)
        overlay[redness_mask] = (0.50 * overlay[redness_mask] + 0.50 * np.array([255, 55, 70])).astype(np.uint8)
        overlay[pigmentation_mask] = (0.50 * overlay[pigmentation_mask] + 0.50 * np.array([90, 70, 210])).astype(np.uint8)
        overlay = self._draw_skin_boundary(overlay, valid)

        return RGBAnalysisResult(metrics, image_rgb, skin_region, redness_map, pigmentation_map, overlay)


RGBAnalysisEngine = RGBAnalysisEngineV15
