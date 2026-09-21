from __future__ import annotations

import hashlib
from typing import Any

TRACKING_IDENTITY_VERSION = "1.0"

REGIONS: tuple[dict[str, Any], ...] = (
    {"code": "full_face", "label": "Full face", "modalities": ["rgb"]},
    {"code": "forehead", "label": "Forehead", "modalities": ["rgb", "uv"]},
    {"code": "left_cheek", "label": "Left cheek", "modalities": ["rgb", "uv"]},
    {"code": "right_cheek", "label": "Right cheek", "modalities": ["rgb", "uv"]},
    {"code": "nose", "label": "Nose", "modalities": ["rgb", "uv"]},
    {"code": "chin", "label": "Chin", "modalities": ["rgb", "uv"]},
    {"code": "jawline", "label": "Jawline", "modalities": ["rgb", "uv"]},
    {"code": "other_face", "label": "Other facial area", "modalities": ["uv"]},
    {"code": "other_body", "label": "Other body area", "modalities": ["uv"]},
)

_REGION_BY_CODE = {x["code"]: x for x in REGIONS}


def get_region(code: str | None, modality: str | None = None) -> dict[str, Any] | None:
    if not code:
        return None
    region = _REGION_BY_CODE.get(code)
    if not region:
        return None
    if modality and modality not in region["modalities"]:
        return None
    return dict(region)


def region_options(modality: str | None = None) -> list[dict[str, Any]]:
    rows = REGIONS if modality is None else tuple(x for x in REGIONS if modality in x["modalities"])
    return [dict(x) for x in rows]


def tracking_series_key(subject_id: str | None, region_code: str | None) -> str | None:
    if not subject_id or not region_code:
        return None
    raw = f"{TRACKING_IDENTITY_VERSION}|{subject_id}|{region_code}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def stamp_tracking_metadata(
    metrics: dict[str, Any],
    *,
    subject: dict[str, Any] | None,
    region: dict[str, Any] | None,
) -> dict[str, Any]:
    subject_id = subject.get("id") if subject else None
    subject_name = subject.get("display_name") if subject else None
    region_code = region.get("code") if region else None
    region_label = region.get("label") if region else None
    key = tracking_series_key(subject_id, region_code)
    metrics.update(
        {
            "tracking_identity_version": TRACKING_IDENTITY_VERSION,
            "tracking_subject_id": subject_id,
            "tracking_subject_name": subject_name,
            "tracking_region_code": region_code,
            "tracking_region_label": region_label,
            "tracking_series_key": key,
        }
    )
    return metrics
