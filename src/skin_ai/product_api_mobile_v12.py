from __future__ import annotations

"""Production entrypoint with phone-camera capture calibration V1.2.

The RGB measurement engine remains V1.1. This module only recalibrates the
capture-quality sharpness gate for real handheld phone camera output before
loading the existing FastAPI application.
"""

import numpy as np

from skin_ai.rgb_engine import RGBAnalysisEngine


_CAPTURE_PROTOCOL_VERSION = "1.2"
_ORIGINAL_QUALITY = RGBAnalysisEngine._quality


def _mobile_quality(image_rgb, face, skin_mask):
    metrics = _ORIGINAL_QUALITY(image_rgb, face, skin_mask)

    blur_var = float(metrics.get("sharpness_laplacian_var", 0.0))
    subscores = metrics.setdefault("quality_subscores", {})

    # V1.1 was tuned mostly with desktop/upload samples: blur < 50 was a hard
    # flag and the sharpness score only became useful above ~25. Real phone
    # selfie streams are softer because of browser resizing, denoising and
    # handheld motion. V1.2 keeps very soft frames rejectable while allowing
    # normal handheld captures through to the rest of the quality gate.
    subscores["sharpness"] = round(float(np.clip((blur_var - 12.0) / 48.0 * 100.0, 0.0, 100.0)), 1)

    flags = list(metrics.get("quality_flags", []))
    flags = [f for f in flags if f != "blurry"]
    if blur_var < 28.0:
        flags.append("blurry")
    metrics["quality_flags"] = list(dict.fromkeys(flags))

    guidance = [
        g for g in metrics.get("quality_guidance", [])
        if g != "Hold the phone steady and refocus before capture."
        and not g.startswith("Capture conditions are suitable.")
    ]
    if blur_var < 28.0:
        guidance.insert(0, "Hold the phone steady for a moment and tap the face to refocus before capture.")
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

# Import only after applying the capture calibration so the singleton engine
# and /health endpoint use protocol V1.2 from process start.
from skin_ai.product_api import app  # noqa: E402,F401
