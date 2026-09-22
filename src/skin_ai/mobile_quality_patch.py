"""Mobile camera quality calibration.

Keeps RGB measurements unchanged. It only softens the capture accept/reject
boundary for moderately soft phone-camera images so they can be stored as
"usable" scans. Longitudinal eligibility remains strict: only "good" captures
are eligible for trends.
"""
from __future__ import annotations

from .rgb_engine import RGBAnalysisEngine


_ORIGINAL_QUALITY = RGBAnalysisEngine._quality


def _mobile_calibrated_quality(image_rgb, face, skin_mask):
    metrics = _ORIGINAL_QUALITY(image_rgb, face, skin_mask)
    blur_var = float(metrics.get("sharpness_laplacian_var", 0.0) or 0.0)
    flags = list(metrics.get("quality_flags", []))

    # Front-camera JPEG processing can produce lower Laplacian variance than
    # desktop/sample images even when facial detail is visibly usable. Treat
    # 30–50 as moderate softness rather than a severe blur failure.
    if 30.0 <= blur_var < 50.0 and "blurry" in flags:
        flags = [f for f in flags if f != "blurry"]
        metrics["quality_flags"] = flags
        guidance = [g for g in metrics.get("quality_guidance", []) if "refocus" not in g.lower() and "steady" not in g.lower()]
        if not guidance:
            guidance = ["Capture is usable. For repeat scans, keep lighting, distance and angle as consistent as possible."]
        metrics["quality_guidance"] = guidance

        subscores = metrics.setdefault("quality_subscores", {})
        # Keep this deliberately below a perfect score so moderate softness
        # does not become a "good" longitudinal capture solely from this patch.
        subscores["sharpness"] = max(float(subscores.get("sharpness", 0.0)), min(80.0, 45.0 + (blur_var - 30.0) * 1.75))
        RGBAnalysisEngine._reclassify_quality(metrics)
        metrics["mobile_softness_tolerance_applied"] = True
        metrics["longitudinal_eligible"] = bool(metrics.get("capture_quality") == "good")
    else:
        metrics["mobile_softness_tolerance_applied"] = False

    return metrics


RGBAnalysisEngine._quality = staticmethod(_mobile_calibrated_quality)
