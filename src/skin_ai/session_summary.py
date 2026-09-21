from __future__ import annotations

from typing import Any

SUMMARY_VERSION = "2.0"
UV_SPOT_STABLE_THRESHOLD = 1
UV_AREA_STABLE_THRESHOLD_PP = 0.5
RGB_AREA_STABLE_THRESHOLD_PP = 0.5


def _region_label(metrics: dict[str, Any], fallback: str) -> str:
    return metrics.get("tracking_region_label") or fallback.replace("_", " ").title()


def _eligible_previous(current: dict[str, Any], candidate: dict[str, Any]) -> bool:
    if candidate["id"] == current["id"] or candidate["modality"] != current["modality"]:
        return False
    if candidate["created_at"] >= current["created_at"]:
        return False
    cm = current.get("metrics", {})
    pm = candidate.get("metrics", {})
    if not cm.get("tracking_series_key") or cm.get("tracking_series_key") != pm.get("tracking_series_key"):
        return False
    if cm.get("scan_session_id") and cm.get("scan_session_id") == pm.get("scan_session_id"):
        return False
    if current["modality"] == "uv":
        return bool(
            cm.get("uv_longitudinal_eligible") is True
            and pm.get("uv_longitudinal_eligible") is True
            and cm.get("uv_comparison_key")
            and cm.get("uv_comparison_key") == pm.get("uv_comparison_key")
        )
    return bool(
        cm.get("longitudinal_eligible") is True
        and pm.get("longitudinal_eligible") is True
        and str(cm.get("rgb_engine_version")) == str(pm.get("rgb_engine_version"))
    )


def find_previous_comparable(current: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [scan for scan in candidates if _eligible_previous(current, scan)]
    if not matches:
        return None
    return max(matches, key=lambda x: x["created_at"])


def _direction(a: float, threshold: float) -> int:
    if a > threshold:
        return 1
    if a < -threshold:
        return -1
    return 0


def _uv_region_summary(current: dict[str, Any], previous: dict[str, Any] | None, region_code: str) -> dict[str, Any]:
    cm = current.get("metrics", {})
    region = {
        "region_code": region_code,
        "region_label": _region_label(cm, region_code),
        "scan_id": current["id"],
        "created_at": current["created_at"],
        "current": {
            "fluorescent_spots": cm.get("porphyrin_component_count_proxy"),
            "fluorescent_area_fraction": cm.get("porphyrin_area_fraction_valid"),
            "signal_intensity": cm.get("porphyrin_red_intensity_proxy"),
            "artifact_fraction": cm.get("artifact_area_fraction"),
            "validator_score": cm.get("uv_input_validation_score"),
        },
        "comparison": None,
        "status": "baseline",
        "status_label": "New baseline",
    }
    if not previous:
        return region
    pm = previous.get("metrics", {})
    spots_now = float(cm.get("porphyrin_component_count_proxy") or 0)
    spots_prev = float(pm.get("porphyrin_component_count_proxy") or 0)
    area_now = float(cm.get("porphyrin_area_fraction_valid") or 0)
    area_prev = float(pm.get("porphyrin_area_fraction_valid") or 0)
    spot_delta = spots_now - spots_prev
    area_delta_pp = (area_now - area_prev) * 100.0
    spot_dir = _direction(spot_delta, UV_SPOT_STABLE_THRESHOLD)
    area_dir = _direction(area_delta_pp, UV_AREA_STABLE_THRESHOLD_PP)
    if spot_dir == 0 and area_dir == 0:
        status, label = "stable", "Stable"
    elif spot_dir >= 0 and area_dir >= 0 and (spot_dir > 0 or area_dir > 0):
        status, label = "higher", "Higher measured signal"
    elif spot_dir <= 0 and area_dir <= 0 and (spot_dir < 0 or area_dir < 0):
        status, label = "lower", "Lower measured signal"
    else:
        status, label = "mixed", "Mixed change"
    region["comparison"] = {
        "previous_scan_id": previous["id"],
        "previous_created_at": previous["created_at"],
        "spot_delta": int(round(spot_delta)),
        "area_delta_percentage_points": round(area_delta_pp, 2),
        "previous_spots": pm.get("porphyrin_component_count_proxy"),
        "previous_area_fraction": pm.get("porphyrin_area_fraction_valid"),
    }
    region["status"] = status
    region["status_label"] = label
    return region


def _rgb_region_summary(current: dict[str, Any], previous: dict[str, Any] | None, region_code: str) -> dict[str, Any]:
    cm = current.get("metrics", {})
    region = {
        "region_code": region_code,
        "region_label": _region_label(cm, region_code),
        "scan_id": current["id"],
        "created_at": current["created_at"],
        "current": {
            "redness_area_fraction": cm.get("redness_area_fraction"),
            "pigmentation_area_fraction": cm.get("pigmentation_area_fraction"),
            "texture_index": cm.get("texture_index_proxy"),
            "capture_quality": cm.get("capture_quality"),
            "capture_quality_score": cm.get("capture_quality_score"),
        },
        "comparison": None,
        "status": "baseline",
        "status_label": "New baseline",
    }
    if not previous:
        return region
    pm = previous.get("metrics", {})
    redness_delta_pp = (float(cm.get("redness_area_fraction") or 0) - float(pm.get("redness_area_fraction") or 0)) * 100.0
    pigment_delta_pp = (float(cm.get("pigmentation_area_fraction") or 0) - float(pm.get("pigmentation_area_fraction") or 0)) * 100.0
    red_dir = _direction(redness_delta_pp, RGB_AREA_STABLE_THRESHOLD_PP)
    pig_dir = _direction(pigment_delta_pp, RGB_AREA_STABLE_THRESHOLD_PP)
    if red_dir == 0 and pig_dir == 0:
        status, label = "stable", "Stable"
    elif red_dir >= 0 and pig_dir >= 0 and (red_dir > 0 or pig_dir > 0):
        status, label = "higher", "Higher measured signal"
    elif red_dir <= 0 and pig_dir <= 0 and (red_dir < 0 or pig_dir < 0):
        status, label = "lower", "Lower measured signal"
    else:
        status, label = "mixed", "Mixed change"
    region["comparison"] = {
        "previous_scan_id": previous["id"],
        "previous_created_at": previous["created_at"],
        "redness_delta_percentage_points": round(redness_delta_pp, 2),
        "pigmentation_delta_percentage_points": round(pigment_delta_pp, 2),
    }
    region["status"] = status
    region["status_label"] = label
    return region


def build_session_summary(session: dict[str, Any], scans: list[dict[str, Any]], subject: dict[str, Any] | None = None) -> dict[str, Any]:
    scan_by_id = {scan["id"]: scan for scan in scans}
    regions: list[dict[str, Any]] = []
    for item in session.get("items", []):
        current = scan_by_id.get(item["scan_id"])
        if not current:
            continue
        previous = find_previous_comparable(current, scans)
        if session["modality"] == "uv":
            regions.append(_uv_region_summary(current, previous, item["region_code"]))
        else:
            regions.append(_rgb_region_summary(current, previous, item["region_code"]))

    counts = {"baseline": 0, "stable": 0, "higher": 0, "lower": 0, "mixed": 0}
    for region in regions:
        counts[region["status"]] = counts.get(region["status"], 0) + 1
    comparable = len(regions) - counts["baseline"]

    if not regions:
        headline = "No completed captures are available for this session."
    elif comparable == 0:
        headline = "Session complete. These captures establish region-specific baselines for future comparison."
    else:
        parts = []
        if counts["stable"]:
            parts.append(f'{counts["stable"]} stable')
        if counts["higher"]:
            parts.append(f'{counts["higher"]} higher')
        if counts["lower"]:
            parts.append(f'{counts["lower"]} lower')
        if counts["mixed"]:
            parts.append(f'{counts["mixed"]} mixed')
        if counts["baseline"]:
            parts.append(f'{counts["baseline"]} new baseline')
        headline = "Compared with each region's latest compatible baseline: " + ", ".join(parts) + "."

    caveats = [
        "Changes describe stored image-derived research measurements, not clinical improvement or worsening.",
        "Comparisons require the same subject, region, compatible analysis version, and accepted capture workflow.",
    ]
    if session["modality"] == "uv":
        caveats.append("Passing the UV input gate does not independently prove UV illumination.")

    return {
        "summary_version": SUMMARY_VERSION,
        "session_id": session["id"],
        "session_status": session["status"],
        "session_version": session.get("session_version"),
        "modality": session["modality"],
        "created_at": session["created_at"],
        "completed_at": session.get("completed_at"),
        "subject": subject,
        "region_count": len(regions),
        "comparable_region_count": comparable,
        "counts": counts,
        "headline": headline,
        "regions": regions,
        "display_thresholds": {
            "uv_spot_count": UV_SPOT_STABLE_THRESHOLD,
            "uv_area_percentage_points": UV_AREA_STABLE_THRESHOLD_PP,
            "rgb_area_percentage_points": RGB_AREA_STABLE_THRESHOLD_PP,
            "note": "Display thresholds suppress tiny visual fluctuations; they are not clinical significance thresholds.",
        },
        "caveats": caveats,
        "diagnostic_use": False,
    }
