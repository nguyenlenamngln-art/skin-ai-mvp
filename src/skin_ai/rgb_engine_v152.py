from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from skin_ai.rgb_engine_v151 import RGBAnalysisEngineV151, RGBAnalysisResult


class RGBAnalysisEngineV152(RGBAnalysisEngineV151):
    """RGB Measurement V1.5.2 — anatomical mask stabilization.

    Redness/pigmentation measurement thresholds stay unchanged from V1.5 and
    regional trend gating stays unchanged from V1.5.1. This patch separates the
    conservative measurement mask from a stabilized anatomical outer envelope
    used for boundary visualization and segmentation-repeatability scoring.
    """

    VERSION = "1.5.2"
    CAPTURE_PROTOCOL_VERSION = "1.4"
    MEASUREMENT_MASK_VERSION = "feature_confidence_anatomical_v1_5_2"
    SEGMENTATION_REFINEMENT_VERSION = "anatomical_outer_envelope_v1_5_2"

    @staticmethod
    def _largest_component(mask: np.ndarray) -> np.ndarray:
        src = mask.astype(np.uint8)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(src, 8)
        if n <= 1:
            return np.zeros_like(mask, dtype=bool)
        label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        return labels == label

    @classmethod
    def _stabilize_anatomical_measurement_mask(
        cls,
        valid: np.ndarray,
        base: np.ndarray,
        excluded: np.ndarray,
        face: tuple[int, int, int, int],
    ) -> tuple[np.ndarray, dict[str, float | int | bool | str]]:
        """Repair only small exterior notches near already-supported skin.

        Additions are constrained to the existing face envelope, never enter
        explicit feature exclusions, and must remain within a few pixels of
        existing valid skin. If cleanup changes too much area, V1.5.1 is kept.
        """
        raw = valid.astype(bool)
        candidate = (base > 0) & (excluded == 0)
        raw_n = max(1, int(raw.sum()))
        _, _, fw, fh = face
        bridge_px = max(2.0, min(5.0, min(fw, fh) * 0.018))

        close_size = max(5, int(round(min(fw, fh) * 0.035)))
        if close_size % 2 == 0:
            close_size += 1
        close_size = min(close_size, 11)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_size, close_size))
        closed = cv2.morphologyEx(raw.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=1) > 0

        # Distance to the nearest original valid skin pixel. This prevents the
        # anatomical prior from creating unsupported skin across large gaps.
        inverse = (~raw).astype(np.uint8)
        distance = cv2.distanceTransform(inverse, cv2.DIST_L2, 3)
        additions = closed & candidate & ~raw & (distance <= bridge_px)
        stabilized = raw | additions
        stabilized = cls._largest_component(stabilized)
        stabilized &= candidate

        stabilized_n = int(stabilized.sum())
        retained = int((stabilized & raw).sum())
        retention = float(retained / raw_n)
        added_fraction = float((stabilized & ~raw).sum() / raw_n)
        changed_fraction = float(np.logical_xor(raw, stabilized).sum() / raw_n)

        fallback = (
            stabilized_n < 2500
            or retention < 0.90
            or added_fraction > 0.05
            or changed_fraction > 0.10
        )
        if fallback:
            stabilized = raw
            stabilized_n = int(stabilized.sum())
            retention = 1.0
            added_fraction = 0.0
            changed_fraction = 0.0

        return stabilized, {
            "segmentation_refinement_version": cls.SEGMENTATION_REFINEMENT_VERSION,
            "anatomical_mask_fallback": bool(fallback),
            "anatomical_mask_bridge_px": round(float(bridge_px), 2),
            "anatomical_mask_retention_fraction": retention,
            "anatomical_mask_added_fraction": added_fraction,
            "anatomical_mask_changed_fraction": changed_fraction,
        }

    @classmethod
    def _outer_boundary_mask(
        cls,
        skin_mask: np.ndarray,
        face: tuple[int, int, int, int] | None = None,
    ) -> np.ndarray:
        """Create a smooth external facial envelope without internal feature holes.

        This mask is never used for redness/pigmentation measurement. It is only
        used for outer-boundary drawing and segmentation repeatability scoring.
        """
        largest = cls._largest_component(skin_mask)
        if not largest.any():
            return largest
        contours, _ = cv2.findContours(largest.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return largest
        contour = max(contours, key=cv2.contourArea)
        hull = cv2.convexHull(contour)
        envelope = np.zeros_like(largest, dtype=np.uint8)
        cv2.fillConvexPoly(envelope, hull, 1)

        if face is not None:
            base, _ = cls._face_geometry(skin_mask.shape, face)
            envelope &= (base > 0).astype(np.uint8)

        # A mild blur removes stair-step artifacts while preserving the jaw and
        # temple scale established by the detected face ellipse.
        smooth = cv2.GaussianBlur(envelope.astype(np.float32), (0, 0), 1.4) >= 0.50
        if face is not None:
            base, _ = cls._face_geometry(skin_mask.shape, face)
            smooth &= base > 0
        return cls._largest_component(smooth)

    @classmethod
    def _anatomical_regularity(
        cls,
        skin_mask: np.ndarray,
        face: tuple[int, int, int, int],
    ) -> dict[str, float | int | bool]:
        base, excluded = cls._face_geometry(skin_mask.shape, face)
        envelope = cls._outer_boundary_mask(skin_mask, face)
        regularity = dict(cls._segmentation_regularity(envelope, base))

        measurable_envelope = envelope & (excluded == 0)
        support_n = int((skin_mask & measurable_envelope).sum())
        envelope_n = max(1, int(measurable_envelope.sum()))
        support_fraction = float(support_n / envelope_n)
        if support_fraction >= 0.78:
            support_score = 100.0
        elif support_fraction <= 0.52:
            support_score = 0.0
        else:
            support_score = 100.0 * (support_fraction - 0.52) / (0.78 - 0.52)

        outer_score = float(regularity["segmentation_regularity_score"])
        score = float(np.clip(0.68 * outer_score + 0.32 * support_score, 0.0, 100.0))
        unstable = bool(
            score < 42.0
            or support_fraction < 0.58
            or int(regularity["skin_mask_component_count"]) > 1
            or float(regularity["skin_mask_perimeter_ratio"]) > 2.35
        )
        regularity["segmentation_regularity_score"] = round(score, 1)
        regularity["segmentation_unstable"] = unstable
        regularity["anatomical_outer_boundary_score"] = round(outer_score, 1)
        regularity["anatomical_skin_support_fraction"] = support_fraction
        regularity["anatomical_skin_support_score"] = round(float(support_score), 1)
        regularity["anatomical_outer_envelope_fraction_of_face"] = float(envelope.sum() / max(1, (base > 0).sum()))
        return regularity

    @classmethod
    def _adaptive_skin_mask(
        cls,
        image_rgb: np.ndarray,
        face: tuple[int, int, int, int],
        base: np.ndarray,
        excluded: np.ndarray,
    ) -> tuple[np.ndarray, dict[str, float | str | int | bool]]:
        valid, info = super()._adaptive_skin_mask(image_rgb, face, base, excluded)
        stabilized, anatomical = cls._stabilize_anatomical_measurement_mask(valid, base, excluded, face)
        info = dict(info)
        info.update(anatomical)
        info["segmentation_method"] = f"{info.get('segmentation_method', 'adaptive')}+anatomical_v1_5_2"
        base_n = max(1, int((base > 0).sum()))
        candidate_n = max(1, int(((base > 0) & (excluded == 0)).sum()))
        info["skin_region_fraction_of_face"] = float(stabilized.sum() / base_n)
        info["skin_region_fraction_of_candidate"] = float(stabilized.sum() / candidate_n)
        return stabilized, info

    @staticmethod
    def _quality(
        image_rgb: np.ndarray,
        face: tuple[int, int, int, int],
        skin_mask: np.ndarray,
    ) -> dict[str, Any]:
        # Start with all established V1.5/V1.4 capture metrics, then replace only
        # the segmentation subscore with the anatomical outer-boundary score.
        metrics = RGBAnalysisEngineV151._quality(image_rgb, face, skin_mask)
        raw_regular = {
            "score": metrics.get("segmentation_regularity_score"),
            "components": metrics.get("skin_mask_component_count"),
            "holes": metrics.get("skin_mask_hole_count"),
            "perimeter_ratio": metrics.get("skin_mask_perimeter_ratio"),
        }
        anatomical = RGBAnalysisEngineV152._anatomical_regularity(skin_mask.astype(bool), face)
        metrics["raw_measurement_segmentation_regularity_score"] = raw_regular["score"]
        metrics["raw_measurement_skin_mask_component_count"] = raw_regular["components"]
        metrics["raw_measurement_skin_mask_hole_count"] = raw_regular["holes"]
        metrics["raw_measurement_skin_mask_perimeter_ratio"] = raw_regular["perimeter_ratio"]
        metrics.update(anatomical)
        metrics.setdefault("quality_subscores", {})["segmentation"] = float(anatomical["segmentation_regularity_score"])

        flags = [f for f in metrics.get("quality_flags", []) if f != "segmentation_unstable"]
        guidance = [g for g in metrics.get("quality_guidance", []) if not g.startswith("Retake with sharper, more even lighting")]
        if anatomical["segmentation_unstable"]:
            flags.append("segmentation_unstable")
            guidance.append("Use even frontal light and keep the full face centered so the outer facial skin boundary remains stable.")
        metrics["quality_flags"] = list(dict.fromkeys(flags))
        metrics["quality_guidance"] = list(dict.fromkeys(guidance))
        metrics["capture_protocol_version"] = RGBAnalysisEngineV152.CAPTURE_PROTOCOL_VERSION
        RGBAnalysisEngineV151._reclassify_quality(metrics)
        return metrics

    @classmethod
    def _draw_skin_boundary(cls, image_rgb: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
        out = image_rgb.copy()
        envelope = cls._outer_boundary_mask(skin_mask)
        contours, _ = cv2.findContours(envelope.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            contour = max(contours, key=cv2.contourArea)
            epsilon = 0.0025 * cv2.arcLength(contour, True)
            contour = cv2.approxPolyDP(contour, epsilon, True)
            cv2.drawContours(out, [contour], -1, (70, 210, 140), 2, cv2.LINE_AA)
        return out

    def analyze_rgb(self, image_rgb: np.ndarray) -> RGBAnalysisResult:
        result = super().analyze_rgb(image_rgb)
        result.metrics["interpretation"]["segmentation_note"] = (
            "V1.5.2 keeps feature exclusions for measurement but scores and draws a separate stabilized anatomical outer envelope."
        )
        result.metrics["interpretation"]["regional_trend_note"] = (
            "V1.5.2 preserves the V1.5.1 regional gate: only regions meeting usable-pixel confidence and minimum-pixel thresholds contribute to regional deltas."
        )
        return result


RGBAnalysisEngine = RGBAnalysisEngineV152
