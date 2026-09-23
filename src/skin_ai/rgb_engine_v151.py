from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from skin_ai.rgb_engine_v15 import RGBAnalysisEngineV15, RGBAnalysisResult


class RGBAnalysisEngineV151(RGBAnalysisEngineV15):
    """RGB Measurement V1.5.1 — conservative segmentation refinement.

    Redness/pigmentation measurement thresholds remain V1.5. Capture Protocol
    remains V1.4. This patch only stabilizes the facial skin mask and adds
    region-level trend eligibility based on usable-pixel confidence.
    """

    VERSION = "1.5.1"
    CAPTURE_PROTOCOL_VERSION = "1.4"
    MEASUREMENT_MASK_VERSION = "feature_confidence_segmentation_v1_5_1"
    SEGMENTATION_REFINEMENT_VERSION = "dominant_component_smooth_v1_5_1"
    REGIONAL_TREND_CONFIDENCE_MIN = 0.65
    REGIONAL_TREND_MIN_PIXELS = 250

    @staticmethod
    def _component_summary(mask: np.ndarray) -> tuple[int, float]:
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
        if n <= 1:
            return 0, 0.0
        areas = stats[1:, cv2.CC_STAT_AREA].astype(np.float64)
        return int(n - 1), float(areas.max() / max(1.0, areas.sum()))

    @classmethod
    def _refine_skin_mask(
        cls,
        valid: np.ndarray,
        base: np.ndarray,
        excluded: np.ndarray,
    ) -> tuple[np.ndarray, dict[str, float | int | bool | str]]:
        raw = valid.astype(bool)
        candidate = (base > 0) & (excluded == 0)
        raw_n = max(1, int(raw.sum()))
        before_components, before_largest = cls._component_summary(raw)

        mask = raw.astype(np.uint8)
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel, iterations=1)

        # Smooth jagged exterior boundaries without allowing pixels outside the
        # existing face envelope or inside explicit feature exclusions.
        smooth = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.25) >= 0.48
        smooth &= candidate

        # Keep the dominant facial component. Small detached islands are the
        # common source of unstable temple/eye contours in phone captures.
        n, labels, stats, _ = cv2.connectedComponentsWithStats(smooth.astype(np.uint8), 8)
        refined = np.zeros_like(smooth, dtype=bool)
        if n > 1:
            areas = stats[1:, cv2.CC_STAT_AREA]
            dominant_label = 1 + int(np.argmax(areas))
            refined = labels == dominant_label

        refined &= candidate
        refined_n = int(refined.sum())
        retention = float(refined_n / raw_n)

        # Never trade stability for a materially smaller analysis region.
        fallback = refined_n < 2500 or retention < 0.82
        if fallback:
            refined = raw
            refined_n = int(refined.sum())
            retention = float(refined_n / raw_n)

        after_components, after_largest = cls._component_summary(refined)
        changed_fraction = float(np.logical_xor(raw, refined).sum() / raw_n)
        return refined, {
            "segmentation_refinement_version": cls.SEGMENTATION_REFINEMENT_VERSION,
            "segmentation_refinement_fallback": bool(fallback),
            "segmentation_component_count_before_refinement": before_components,
            "segmentation_component_count_after_refinement": after_components,
            "segmentation_largest_component_fraction_before_refinement": before_largest,
            "segmentation_largest_component_fraction_after_refinement": after_largest,
            "segmentation_refinement_retention_fraction": retention,
            "segmentation_refinement_changed_fraction": changed_fraction,
        }

    @classmethod
    def _adaptive_skin_mask(
        cls,
        image_rgb: np.ndarray,
        face: tuple[int, int, int, int],
        base: np.ndarray,
        excluded: np.ndarray,
    ) -> tuple[np.ndarray, dict[str, float | str | int | bool]]:
        valid, info = super()._adaptive_skin_mask(image_rgb, face, base, excluded)
        refined, refinement = cls._refine_skin_mask(valid, base, excluded)
        base_n = max(1, int((base > 0).sum()))
        candidate_n = max(1, int(((base > 0) & (excluded == 0)).sum()))
        info = dict(info)
        info.update(refinement)
        info["segmentation_method"] = f"{info.get('segmentation_method', 'adaptive')}+v1_5_1_refinement"
        info["skin_region_fraction_of_face"] = float(refined.sum() / base_n)
        info["skin_region_fraction_of_candidate"] = float(refined.sum() / candidate_n)
        return refined, info

    @classmethod
    def _regional_measurements(
        cls,
        face: tuple[int, int, int, int],
        analysis_valid: np.ndarray,
        measurement_valid: np.ndarray,
        pigmentation_valid: np.ndarray,
        redness_mask: np.ndarray,
        pigmentation_mask: np.ndarray,
    ) -> dict[str, dict[str, float | int | bool | str]]:
        out = super()._regional_measurements(
            face,
            analysis_valid,
            measurement_valid,
            pigmentation_valid,
            redness_mask,
            pigmentation_mask,
        )
        for region in out.values():
            confidence = float(region.get("confidence", 0.0))
            usable_pixels = int(region.get("usable_pixels", 0))
            eligible = bool(
                confidence >= cls.REGIONAL_TREND_CONFIDENCE_MIN
                and usable_pixels >= cls.REGIONAL_TREND_MIN_PIXELS
            )
            region["trend_eligible"] = eligible
            if eligible:
                region["trend_reason"] = "eligible"
            elif confidence < cls.REGIONAL_TREND_CONFIDENCE_MIN:
                region["trend_reason"] = "usable_pixel_confidence_low"
            else:
                region["trend_reason"] = "too_few_usable_pixels"
        return out

    def analyze_rgb(self, image_rgb: np.ndarray) -> RGBAnalysisResult:
        result = super().analyze_rgb(image_rgb)
        regional = result.metrics.get("regional_measurements", {})
        eligible = [name for name, values in regional.items() if values.get("trend_eligible") is True]
        held = [name for name, values in regional.items() if values.get("trend_eligible") is False]
        result.metrics["regional_trend_confidence_min"] = self.REGIONAL_TREND_CONFIDENCE_MIN
        result.metrics["regional_trend_min_pixels"] = self.REGIONAL_TREND_MIN_PIXELS
        result.metrics["regional_trend_eligible_regions"] = eligible
        result.metrics["regional_trend_held_regions"] = held
        result.metrics["regional_trend_eligible_count"] = len(eligible)
        result.metrics["interpretation"]["regional_trend_note"] = (
            "V1.5.1 regional deltas use only regions meeting usable-pixel confidence and minimum-pixel gates."
        )
        return result


RGBAnalysisEngine = RGBAnalysisEngineV151
