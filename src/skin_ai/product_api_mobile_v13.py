from __future__ import annotations

"""Production entrypoint with phone-camera capture calibration V1.3.

The RGB measurement engine remains V1.1. V1.3 recalibrates phone capture
quality severity for sharpness, face framing, and segmentation regularity.
Borderline phone captures can be saved as `usable`; genuinely poor captures
remain rejected. Longitudinal eligibility still requires `good` quality.
"""

import numpy as np

from skin_ai.rgb_engine import RGBAnalysisEngine


_CAPTURE_PROTOCOL_VERSION = "1.3"
_ORIGINAL_QUALITY = RGBAnalysisEngine._quality


def _remove_guidance(items: list[str], prefixes: tuple[str, ...]) -> list[str]:
    return [g for g in items if not any(g.startswith(prefix) for prefix in prefixes)]


def _mobile_quality(image_rgb, face, skin_mask):
    metrics = _ORIGINAL_QUALITY(image_rgb, face, skin_mask)
    subscores = metrics.setdefault("quality_subscores", {})

    # 1) Sharpness: preserve V1.2 phone calibration.
    blur_var = float(metrics.get("sharpness_laplacian_var", 0.0))
    subscores["sharpness"] = round(float(np.clip((blur_var - 12.0) / 48.0 * 100.0, 0.0, 100.0)), 1)

    flags = [f for f in metrics.get("quality_flags", []) if f not in {
        "blurry", "face_too_small", "segmentation_unstable",
        "face_smaller_than_preferred", "segmentation_variation",
    }]
    guidance = list(metrics.get("quality_guidance", []))
    guidance = _remove_guidance(
        guidance,
        (
            "Hold the phone steady and refocus",
            "Move closer so the face fills",
            "Retake with sharper, more even lighting",
            "Capture conditions are suitable.",
        ),
    )

    if blur_var < 28.0:
        flags.append("blurry")
        guidance.append("Hold the phone steady for a moment and tap the face to refocus before capture.")

    # 2) Framing: the original 15% face-area hard stop was too strict for
    # handheld portrait framing. Keep <6.5% as severe; 6.5–12% is advisory.
    face_area = float(metrics.get("face_area_fraction", 0.0))
    if face_area < 0.065:
        flags.append("face_too_small")
        guidance.append("Move closer so the full face is clearly visible and occupies more of the center of the frame.")
    elif face_area < 0.12:
        flags.append("face_smaller_than_preferred")
        guidance.append("For more repeatable tracking, move slightly closer next time while keeping the full face visible.")

    # 3) Segmentation: the V1.1 hard flag was intentionally conservative but
    # too sensitive for real phone images (e.g. one tiny secondary component
    # could reject a high-scoring capture). Escalate only when several signals
    # show real mask breakdown; otherwise mark advisory variation.
    seg_score = float(metrics.get("segmentation_regularity_score", 0.0))
    largest = float(metrics.get("skin_mask_largest_component_fraction", 0.0))
    components = int(metrics.get("skin_mask_component_count", 0))
    holes = int(metrics.get("skin_mask_hole_count", 0))
    perimeter = float(metrics.get("skin_mask_perimeter_ratio", 999.0))

    severe_segmentation = (
        seg_score < 35.0
        or largest < 0.80
        or components > 6
        or holes > 12
        or perimeter > 3.2
    )
    advisory_segmentation = (
        seg_score < 60.0
        or largest < 0.93
        or components > 2
        or holes > 8
        or perimeter > 2.6
    )

    if severe_segmentation:
        flags.append("segmentation_unstable")
        guidance.append("Use more even frontal light and a slightly closer, centered framing so the analyzed skin boundary is stable.")
    elif advisory_segmentation:
        flags.append("segmentation_variation")
        guidance.append("Skin-boundary consistency was acceptable but not ideal; use more even light for repeat scans.")

    metrics["quality_flags"] = list(dict.fromkeys(flags))
    metrics["quality_guidance"] = list(dict.fromkeys(guidance))
    metrics["capture_protocol_version"] = _CAPTURE_PROTOCOL_VERSION

    RGBAnalysisEngine._reclassify_quality(metrics)
    if not metrics["quality_guidance"]:
        metrics["quality_guidance"] = [
            "Capture conditions are suitable. Reuse similar lighting, distance and angle for repeat scans."
        ]
    return metrics


RGBAnalysisEngine._quality = staticmethod(_mobile_quality)
RGBAnalysisEngine.CAPTURE_PROTOCOL_VERSION = _CAPTURE_PROTOCOL_VERSION

# Import only after applying calibration so the singleton engine and /health
# endpoint report protocol V1.3 from process start.
from skin_ai.product_api import app  # noqa: E402,F401
