from __future__ import annotations

import math
from typing import Any

VERSION = "1.5.9"
MIN_ELIGIBLE_SCORE = 65.0
STRONG_SCORE = 80.0


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _one_sided(value: float, good_max: float, fail_max: float) -> float:
    if value <= good_max:
        return 100.0
    if value >= fail_max:
        return 0.0
    return 100.0 * (fail_max - value) / max(1e-9, fail_max - good_max)


def _num(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _bbox_aspect(metrics: dict[str, Any]) -> float | None:
    box = metrics.get("face_bbox")
    if not isinstance(box, dict):
        return None
    w = box.get("w")
    h = box.get("h")
    if not isinstance(w, (int, float)) or not isinstance(h, (int, float)) or float(h) <= 0:
        return None
    return float(w) / float(h)


def _reason_and_guidance(component_scores: dict[str, float]) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    guidance: list[str] = []
    if component_scores.get("lighting", 100.0) < 60.0:
        reasons.append("lighting_differs")
        guidance.append("Use lighting closer to your previous comparable scan.")
    if component_scores.get("face_scale", 100.0) < 60.0:
        reasons.append("face_scale_differs")
        guidance.append("Match the previous face size by moving slightly closer or farther away.")
    if component_scores.get("centering", 100.0) < 60.0:
        reasons.append("face_position_differs")
        guidance.append("Center your face in a position similar to the reference scan.")
    if component_scores.get("balance", 100.0) < 60.0:
        reasons.append("pose_or_light_balance_differs")
        guidance.append("Face the camera more directly and keep left/right lighting even.")
    if component_scores.get("bbox_aspect", 100.0) < 60.0:
        reasons.append("face_shape_projection_differs")
        guidance.append("Keep your head angle closer to the previous scan.")
    return reasons, guidance


def comparison_match(current: dict[str, Any], reference: dict[str, Any] | None) -> dict[str, Any]:
    """Score whether two otherwise valid RGB scans are suitable for visual/trend comparison.

    This is a longitudinal comparability layer, not a skin measurement model. It uses
    capture metadata already emitted by RGB V1.5.2 / Capture Protocol V1.4 and does
    not alter redness, pigmentation, texture, segmentation, or capture-quality gates.
    """
    out: dict[str, Any] = {
        "comparison_protocol_version": VERSION,
        "comparison_match_available": False,
        "comparison_match_score": None,
        "comparison_match_label": "baseline",
        "comparison_match_eligible": False,
        "comparison_match_reasons": [],
        "comparison_match_guidance": [],
        "comparison_match_components": {},
    }
    if not reference:
        return out
    if str(current.get("rgb_engine_version")) != str(reference.get("rgb_engine_version")):
        out["comparison_match_label"] = "version_mismatch"
        out["comparison_match_reasons"] = ["engine_version_differs"]
        return out

    curr_area = _num(current, "face_area_fraction")
    ref_area = _num(reference, "face_area_fraction")
    curr_center = _num(current, "face_center_offset_fraction")
    ref_center = _num(reference, "face_center_offset_fraction")
    curr_luma = _num(current, "skin_luminance_median_0_255")
    ref_luma = _num(reference, "skin_luminance_median_0_255")
    curr_balance = _num(current, "left_right_luminance_asymmetry")
    ref_balance = _num(reference, "left_right_luminance_asymmetry")
    curr_aspect = _bbox_aspect(current)
    ref_aspect = _bbox_aspect(reference)

    required = (curr_area, ref_area, curr_center, ref_center, curr_luma, ref_luma)
    if any(value is None for value in required):
        out["comparison_match_label"] = "metadata_unavailable"
        out["comparison_match_reasons"] = ["comparison_metadata_missing"]
        return out

    scale_delta = abs(math.sqrt(max(curr_area, 1e-9) / max(ref_area, 1e-9)) - 1.0)
    face_scale_score = _one_sided(scale_delta, 0.10, 0.35)

    center_delta = abs(curr_center - ref_center)
    centering_score = min(
        _one_sided(curr_center, 0.10, 0.26),
        _one_sided(center_delta, 0.04, 0.18),
    )

    reference_lighting = _num(current, "reference_lighting_score")
    if reference_lighting is None:
        ev_delta = abs(math.log2(max(curr_luma, 1.0) / max(ref_luma, 1.0)))
        lighting_score = _one_sided(ev_delta, 0.25, 0.90)
    else:
        lighting_score = _clamp(reference_lighting)

    if curr_balance is None or ref_balance is None:
        balance_score = 70.0
        balance_delta = None
    else:
        balance_delta = abs(curr_balance - ref_balance)
        balance_score = min(
            _one_sided(max(curr_balance, ref_balance), 0.16, 0.42),
            _one_sided(balance_delta, 0.08, 0.28),
        )

    if curr_aspect is None or ref_aspect is None:
        bbox_aspect_score = 70.0
        aspect_delta = None
    else:
        aspect_delta = abs(math.log(max(curr_aspect, 1e-9) / max(ref_aspect, 1e-9)))
        bbox_aspect_score = _one_sided(aspect_delta, 0.08, 0.30)

    components = {
        "lighting": round(lighting_score, 1),
        "face_scale": round(face_scale_score, 1),
        "centering": round(centering_score, 1),
        "balance": round(balance_score, 1),
        "bbox_aspect": round(bbox_aspect_score, 1),
    }
    score = (
        0.30 * lighting_score
        + 0.25 * face_scale_score
        + 0.15 * centering_score
        + 0.15 * balance_score
        + 0.15 * bbox_aspect_score
    )
    score = round(_clamp(score), 1)
    severe_component = min(components.values()) < 30.0
    eligible = bool(score >= MIN_ELIGIBLE_SCORE and not severe_component)
    label = "strong" if eligible and score >= STRONG_SCORE else "usable" if eligible else "review"
    reasons, guidance = _reason_and_guidance(components)

    out.update(
        {
            "comparison_match_available": True,
            "comparison_match_score": score,
            "comparison_match_label": label,
            "comparison_match_eligible": eligible,
            "comparison_match_reasons": reasons,
            "comparison_match_guidance": guidance,
            "comparison_match_components": components,
            "comparison_face_scale_delta_fraction": round(scale_delta, 4),
            "comparison_center_offset_delta_fraction": round(center_delta, 4),
            "comparison_balance_delta_fraction": round(balance_delta, 4) if balance_delta is not None else None,
            "comparison_bbox_aspect_log_delta": round(aspect_delta, 4) if aspect_delta is not None else None,
        }
    )
    return out


def stamp_comparison_match(current: dict[str, Any], reference: dict[str, Any] | None) -> dict[str, Any]:
    current.update(comparison_match(current, reference))
    return current
