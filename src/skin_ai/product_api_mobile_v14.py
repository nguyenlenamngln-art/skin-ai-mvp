from __future__ import annotations

"""Production entrypoint for RGB Capture & Tracking V1.4.

RGB measurement V1.5 runs under Capture Protocol V1.4. Capture protocol V1.4
separates advisory warnings from blocking failures and keeps good,
high-scoring phone captures eligible for longitudinal comparison when only
advisory warnings are present.
"""

import numpy as np

from skin_ai.rgb_engine_v15 import RGBAnalysisEngine


_CAPTURE_PROTOCOL_VERSION = "1.4"
_ORIGINAL_QUALITY = RGBAnalysisEngine._quality
_BLOCKING_FLAGS = {
    "too_dark",
    "too_bright",
    "blurry",
    "face_too_small",
    "face_too_close",
    "lighting_not_comparable",
    "segmentation_unstable",
}


def _remove_guidance(items: list[str], prefixes: tuple[str, ...]) -> list[str]:
    return [g for g in items if not any(g.startswith(prefix) for prefix in prefixes)]


def _classify_v14(metrics):
    subscores = metrics.get("quality_subscores", {})
    score = float(sum(float(subscores.get(k, 0.0)) * w for k, w in RGBAnalysisEngine.QUALITY_WEIGHTS.items()))
    flags = list(dict.fromkeys(metrics.get("quality_flags", [])))
    blockers = [f for f in flags if f in _BLOCKING_FLAGS]
    warnings = [f for f in flags if f not in _BLOCKING_FLAGS]

    if blockers:
        quality = "poor"
    elif score >= 85.0:
        quality = "good"
    elif score >= 65.0:
        quality = "usable"
    else:
        quality = "poor"

    metrics["capture_quality_score"] = round(score, 1)
    metrics["capture_quality"] = quality
    metrics["quality_flags"] = flags
    metrics["quality_blockers"] = blockers
    metrics["quality_warnings"] = warnings
    metrics["longitudinal_eligible"] = bool(quality == "good" and not blockers)
    return metrics


def _mobile_quality(image_rgb, face, skin_mask):
    metrics = _ORIGINAL_QUALITY(image_rgb, face, skin_mask)
    subscores = metrics.setdefault("quality_subscores", {})

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

    face_area = float(metrics.get("face_area_fraction", 0.0))
    if face_area < 0.065:
        flags.append("face_too_small")
        guidance.append("Move closer so the full face is clearly visible and occupies more of the center of the frame.")
    elif face_area < 0.12:
        flags.append("face_smaller_than_preferred")
        guidance.append("For more repeatable tracking, move slightly closer next time while keeping the full face visible.")

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
    _classify_v14(metrics)

    if not metrics["quality_guidance"]:
        metrics["quality_guidance"] = [
            "Capture conditions are suitable. Reuse similar lighting, distance and angle for repeat scans."
        ]
    return metrics


RGBAnalysisEngine._quality = staticmethod(_mobile_quality)
RGBAnalysisEngine._reclassify_quality = classmethod(lambda cls, metrics: _classify_v14(metrics))
RGBAnalysisEngine.CAPTURE_PROTOCOL_VERSION = _CAPTURE_PROTOCOL_VERSION

# Import after calibration so all API handlers, including the core live
# distance endpoint, use capture protocol V1.4 from process start.
import skin_ai.product_api as product_api  # noqa: E402

# product_api imports the stable V1.1 base class by default. Rebind its runtime
# engine symbol to V1.5 before requests are served, and clear any eager instance.
# Existing route functions resolve this module-global symbol at call time.
product_api.RGBAnalysisEngine = RGBAnalysisEngine
product_api._rgb_engine = None

_ORIGINAL_RESOLVE_TRACKING = product_api.resolve_tracking


def _resolve_tracking_v14(subject_id, region_code, modality):
    # Standard standalone Phone RGB scans default to a persistent personal
    # tracking series. Explicit profile/region choices still take precedence.
    if modality == "rgb" and not subject_id and not region_code:
        subject = product_api.store.create_subject(
            subject_id="my_profile",
            display_name="My profile",
            created_at=product_api.datetime.now(product_api.timezone.utc).isoformat(),
        )
        region = product_api.get_region("full_face", "rgb")
        return subject, region
    return _ORIGINAL_RESOLVE_TRACKING(subject_id, region_code, modality)


product_api.resolve_tracking = _resolve_tracking_v14
app = product_api.app
