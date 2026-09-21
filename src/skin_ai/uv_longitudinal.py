from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

UV_ANALYSIS_VERSION = "uvfd-v2-porphyrin-proxy-v1"


def normalize_label(value: str | None) -> str | None:
    if value is None:
        return None
    clean = " ".join(value.strip().split())
    return clean[:80] if clean else None


def checkpoint_signature(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def build_series_id(subject_label: str | None, anatomical_site: str | None) -> str | None:
    subject = normalize_label(subject_label)
    site = normalize_label(anatomical_site)
    if not subject or not site:
        return None
    raw = f"{subject.casefold()}|{site.casefold()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_comparison_key(
    *,
    series_id: str | None,
    analysis_version: str,
    model_signature: str,
    validator_version: str,
    validator_profile: str,
) -> str | None:
    if not series_id:
        return None
    raw = "|".join(
        [series_id, analysis_version, model_signature, validator_version, validator_profile]
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def stamp_uv_longitudinal_metadata(
    metrics: dict[str, Any],
    *,
    subject_label: str | None,
    anatomical_site: str | None,
    model_signature: str,
    validator_version: str,
    validator_profile: str,
) -> dict[str, Any]:
    subject = normalize_label(subject_label)
    site = normalize_label(anatomical_site)
    series_id = build_series_id(subject, site)
    comparison_key = build_comparison_key(
        series_id=series_id,
        analysis_version=UV_ANALYSIS_VERSION,
        model_signature=model_signature,
        validator_version=validator_version,
        validator_profile=validator_profile,
    )
    metrics.update(
        {
            "uv_analysis_version": UV_ANALYSIS_VERSION,
            "uv_model_signature": model_signature,
            "uv_subject_label": subject,
            "uv_anatomical_site": site,
            "uv_comparison_series_id": series_id,
            "uv_comparison_key": comparison_key,
            "uv_longitudinal_eligible": bool(comparison_key),
            "uv_longitudinal_reason": (
                "comparison_series_defined"
                if comparison_key
                else "subject_and_anatomical_site_required"
            ),
        }
    )
    return metrics


def uv_scans_comparable(current: dict[str, Any], previous: dict[str, Any]) -> bool:
    cm = current.get("metrics", current)
    pm = previous.get("metrics", previous)
    if cm.get("uv_longitudinal_eligible") is not True:
        return False
    if pm.get("uv_longitudinal_eligible") is not True:
        return False
    current_key = cm.get("uv_comparison_key")
    previous_key = pm.get("uv_comparison_key")
    return bool(current_key and previous_key and current_key == previous_key)
