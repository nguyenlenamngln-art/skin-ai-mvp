from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np

from skin_ai.rgb_engine_v152 import RGBAnalysisEngineV152
from skin_ai.rgb_validation_v153 import validate_rgb_image


VALIDATION_VERSION = "1.5.4"
ENGINE_UNDER_TEST = "1.5.2"
PER_IMAGE_VALIDATION_VERSION = "1.5.3"
CANONICAL_MASK_SIZE = 192

# Provisional engineering-completeness criteria. These are validation gates,
# not diagnostic or clinical thresholds.
MIN_PARTICIPANTS = 3
MIN_CAPTURES_PER_PARTICIPANT = 3
MIN_SESSIONS_PER_PARTICIPANT = 2
MIN_PER_IMAGE_PASS_RATE = 0.80
MIN_MEDIAN_CANONICAL_IOU = 0.80
MIN_MEDIAN_SESSION_IOU = 0.80
MAX_CANONICAL_AREA_CV = 0.12
MAX_FALLBACK_RATE = 0.20
MIN_ANATOMICAL_SUPPORT = 0.70
MIN_PARTICIPANT_PASS_RATE = 0.80


@dataclass(frozen=True)
class CaptureRecord:
    path: Path
    participant_id: str
    session_id: str
    capture_id: str
    device_id: str | None = None


def _clean_required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Manifest field '{field}' is required")
    return text


def _row_to_record(row: dict[str, Any], *, root: Path, index: int) -> CaptureRecord:
    raw_path = _clean_required(row.get("path"), "path")
    participant_id = _clean_required(row.get("participant_id"), "participant_id")
    session_id = _clean_required(row.get("session_id"), "session_id")
    capture_id = str(row.get("capture_id") or f"{participant_id}-{session_id}-{index + 1}").strip()
    device = str(row.get("device_id") or "").strip() or None
    path = Path(raw_path)
    if not path.is_absolute():
        path = root / path
    return CaptureRecord(
        path=path,
        participant_id=participant_id,
        session_id=session_id,
        capture_id=capture_id,
        device_id=device,
    )


def load_manifest(path: Path) -> list[CaptureRecord]:
    """Load a CSV or JSON repeatability manifest.

    Required fields are path, participant_id and session_id. capture_id and
    device_id are optional. Participant identifiers should be pseudonymous.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    elif suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("captures", []) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("JSON manifest must be a list or an object with a 'captures' list")
    else:
        raise ValueError("Manifest must be .csv or .json")

    records = [_row_to_record(dict(row), root=path.parent, index=i) for i, row in enumerate(rows)]
    if not records:
        raise ValueError("Manifest contains no captures")
    capture_ids = [record.capture_id for record in records]
    if len(set(capture_ids)) != len(capture_ids):
        raise ValueError("capture_id values must be unique")
    return records


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    intersection = int(np.logical_and(a, b).sum())
    union = int(np.logical_or(a, b).sum())
    return float(intersection / max(1, union))


def _coefficient_of_variation(values: Iterable[float]) -> float:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size == 0:
        return 0.0
    mean = float(arr.mean())
    if abs(mean) < 1e-12:
        return 0.0
    return float(arr.std(ddof=0) / abs(mean))


def _pairwise_ious(masks: list[np.ndarray]) -> list[float]:
    return [_iou(a, b) for a, b in combinations(masks, 2)]


def _consensus_mask(masks: list[np.ndarray]) -> np.ndarray:
    if not masks:
        raise ValueError("At least one mask is required")
    stack = np.stack([mask.astype(np.float32) for mask in masks], axis=0)
    return stack.mean(axis=0) >= 0.50


def _canonical_outer_envelope(
    engine: RGBAnalysisEngineV152,
    image_rgb: np.ndarray,
    *,
    size: int = CANONICAL_MASK_SIZE,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    face = engine._detect_largest_face(engine.face_detector, image_rgb)
    if face is None:
        return None, {"face_detected": False}

    base, excluded = engine._face_geometry(image_rgb.shape[:2], face)
    skin_mask, segmentation = engine._adaptive_skin_mask(image_rgb, face, base, excluded)
    anatomy = engine._anatomical_regularity(skin_mask, face)
    envelope = engine._outer_boundary_mask(skin_mask, face)

    x, y, fw, fh = face
    h, w = image_rgb.shape[:2]
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(w, x + fw)
    y1 = min(h, y + fh)
    crop = envelope[y0:y1, x0:x1].astype(np.uint8)
    if crop.size == 0 or int(crop.sum()) == 0:
        return None, {"face_detected": True, "canonical_mask_available": False}
    canonical = cv2.resize(crop, (size, size), interpolation=cv2.INTER_NEAREST) > 0

    return canonical, {
        "face_detected": True,
        "canonical_mask_available": True,
        "face_box": [int(v) for v in face],
        "face_area_fraction": float((fw * fh) / max(1, h * w)),
        "canonical_outer_area_fraction": float(canonical.mean()),
        "anatomical_mask_fallback": bool(segmentation.get("anatomical_mask_fallback", False)),
        "anatomical_skin_support_fraction": float(anatomy.get("anatomical_skin_support_fraction", 0.0)),
        "anatomical_outer_boundary_score": float(anatomy.get("anatomical_outer_boundary_score", 0.0)),
    }


def evaluate_capture(record: CaptureRecord) -> tuple[dict[str, Any], np.ndarray | None]:
    bgr = cv2.imread(str(record.path), cv2.IMREAD_COLOR)
    base = {
        "capture_id": record.capture_id,
        "participant_id": record.participant_id,
        "session_id": record.session_id,
        "device_id": record.device_id,
        "source_name": record.path.name,
    }
    if bgr is None:
        return {
            **base,
            "capture_available": False,
            "per_image_validation_pass": False,
            "failure_reasons": ["image_decode_failed"],
        }, None

    image_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    per_image = validate_rgb_image(image_rgb, source_name=record.path.name)
    engine = RGBAnalysisEngineV152()
    canonical, baseline = _canonical_outer_envelope(engine, image_rgb)

    reasons = list(per_image.get("failure_reasons", []))
    if canonical is None:
        reasons.append("canonical_outer_envelope_unavailable")

    return {
        **base,
        "capture_available": True,
        "per_image_validation_version": per_image.get("validation_version"),
        "per_image_validation_pass": bool(per_image.get("validation_pass")) and canonical is not None,
        "failure_reasons": list(dict.fromkeys(reasons)),
        "photometric_repeatability": per_image.get("summary", {}),
        "baseline": baseline,
    }, canonical


def _participant_summary(rows: list[dict[str, Any]], masks: dict[str, np.ndarray]) -> dict[str, Any]:
    participant_id = str(rows[0]["participant_id"])
    sessions = sorted({str(row["session_id"]) for row in rows})
    devices = sorted({str(row["device_id"]) for row in rows if row.get("device_id")})
    valid_masks = [masks[row["capture_id"]] for row in rows if row["capture_id"] in masks]
    pairwise = _pairwise_ious(valid_masks)

    session_masks: list[np.ndarray] = []
    for session_id in sessions:
        within = [
            masks[row["capture_id"]]
            for row in rows
            if row["session_id"] == session_id and row["capture_id"] in masks
        ]
        if within:
            session_masks.append(_consensus_mask(within))
    session_pairwise = _pairwise_ious(session_masks)

    area_fractions = [
        float(row.get("baseline", {}).get("canonical_outer_area_fraction", 0.0))
        for row in rows
        if row.get("baseline", {}).get("canonical_mask_available")
    ]
    supports = [
        float(row.get("baseline", {}).get("anatomical_skin_support_fraction", 0.0))
        for row in rows
        if row.get("baseline", {}).get("canonical_mask_available")
    ]
    fallbacks = [
        bool(row.get("baseline", {}).get("anatomical_mask_fallback", False))
        for row in rows
        if row.get("baseline", {}).get("face_detected")
    ]
    passed = sum(bool(row.get("per_image_validation_pass")) for row in rows)
    pass_rate = float(passed / max(1, len(rows)))
    median_iou = float(np.median(pairwise)) if pairwise else 0.0
    min_iou = float(min(pairwise)) if pairwise else 0.0
    median_session_iou = float(np.median(session_pairwise)) if session_pairwise else 0.0
    min_session_iou = float(min(session_pairwise)) if session_pairwise else 0.0
    area_cv = _coefficient_of_variation(area_fractions)
    fallback_rate = float(sum(fallbacks) / max(1, len(fallbacks))) if fallbacks else 1.0
    min_support = float(min(supports)) if supports else 0.0

    reasons: list[str] = []
    if len(rows) < MIN_CAPTURES_PER_PARTICIPANT:
        reasons.append("insufficient_captures")
    if len(sessions) < MIN_SESSIONS_PER_PARTICIPANT:
        reasons.append("insufficient_sessions")
    if pass_rate < MIN_PER_IMAGE_PASS_RATE:
        reasons.append("per_image_pass_rate_below_80pct")
    if len(valid_masks) >= 2 and median_iou < MIN_MEDIAN_CANONICAL_IOU:
        reasons.append("median_canonical_iou_below_0_80")
    if len(valid_masks) < 2:
        reasons.append("insufficient_valid_masks")
    if len(session_masks) >= 2 and median_session_iou < MIN_MEDIAN_SESSION_IOU:
        reasons.append("median_session_iou_below_0_80")
    if len(session_masks) < 2:
        reasons.append("insufficient_valid_sessions")
    if area_cv > MAX_CANONICAL_AREA_CV:
        reasons.append("canonical_area_cv_above_12pct")
    if fallback_rate > MAX_FALLBACK_RATE:
        reasons.append("fallback_rate_above_20pct")
    if min_support < MIN_ANATOMICAL_SUPPORT:
        reasons.append("anatomical_support_below_70pct")

    return {
        "participant_id": participant_id,
        "participant_pass": not reasons,
        "failure_reasons": reasons,
        "capture_count": len(rows),
        "valid_mask_count": len(valid_masks),
        "session_count": len(sessions),
        "device_count": len(devices),
        "devices": devices,
        "per_image_pass_rate": round(pass_rate, 4),
        "median_pairwise_canonical_iou": round(median_iou, 4),
        "min_pairwise_canonical_iou": round(min_iou, 4),
        "median_session_consensus_iou": round(median_session_iou, 4),
        "min_session_consensus_iou": round(min_session_iou, 4),
        "canonical_outer_area_cv": round(float(area_cv), 4),
        "fallback_rate": round(fallback_rate, 4),
        "min_anatomical_skin_support_fraction": round(min_support, 4),
    }


def summarize_cohort(
    capture_rows: list[dict[str, Any]],
    masks: dict[str, np.ndarray],
) -> dict[str, Any]:
    by_participant: dict[str, list[dict[str, Any]]] = {}
    for row in capture_rows:
        by_participant.setdefault(str(row["participant_id"]), []).append(row)

    participants = [
        _participant_summary(rows, masks)
        for _, rows in sorted(by_participant.items())
    ]
    participant_passes = sum(bool(row["participant_pass"]) for row in participants)
    participant_pass_rate = float(participant_passes / max(1, len(participants)))
    devices = sorted({str(row["device_id"]) for row in capture_rows if row.get("device_id")})
    sessions = {(str(row["participant_id"]), str(row["session_id"])) for row in capture_rows}

    cohort_reasons: list[str] = []
    if len(participants) < MIN_PARTICIPANTS:
        cohort_reasons.append("insufficient_participants")
    if participant_pass_rate < MIN_PARTICIPANT_PASS_RATE:
        cohort_reasons.append("participant_pass_rate_below_80pct")

    complete_participants = sum(
        row["capture_count"] >= MIN_CAPTURES_PER_PARTICIPANT
        and row["session_count"] >= MIN_SESSIONS_PER_PARTICIPANT
        for row in participants
    )
    if complete_participants < MIN_PARTICIPANTS:
        cohort_reasons.append("insufficient_complete_participants")

    return {
        "validation_version": VALIDATION_VERSION,
        "engine_under_test": ENGINE_UNDER_TEST,
        "per_image_validation_version": PER_IMAGE_VALIDATION_VERSION,
        "cohort_pass": not cohort_reasons,
        "failure_reasons": cohort_reasons,
        "summary": {
            "participant_count": len(participants),
            "complete_participant_count": int(complete_participants),
            "capture_count": len(capture_rows),
            "session_count": len(sessions),
            "device_count": len(devices),
            "participant_pass_rate": round(participant_pass_rate, 4),
        },
        "criteria": {
            "min_participants": MIN_PARTICIPANTS,
            "min_captures_per_participant": MIN_CAPTURES_PER_PARTICIPANT,
            "min_sessions_per_participant": MIN_SESSIONS_PER_PARTICIPANT,
            "min_per_image_pass_rate": MIN_PER_IMAGE_PASS_RATE,
            "min_median_canonical_iou": MIN_MEDIAN_CANONICAL_IOU,
            "min_median_session_iou": MIN_MEDIAN_SESSION_IOU,
            "max_canonical_area_cv": MAX_CANONICAL_AREA_CV,
            "max_fallback_rate": MAX_FALLBACK_RATE,
            "min_anatomical_support": MIN_ANATOMICAL_SUPPORT,
            "min_participant_pass_rate": MIN_PARTICIPANT_PASS_RATE,
        },
        "participants": participants,
        "captures": capture_rows,
    }


def validate_manifest(path: Path) -> dict[str, Any]:
    records = load_manifest(path)
    rows: list[dict[str, Any]] = []
    masks: dict[str, np.ndarray] = {}
    for record in records:
        row, mask = evaluate_capture(record)
        rows.append(row)
        if mask is not None:
            masks[record.capture_id] = mask
    return summarize_cohort(rows, masks)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RGB V1.5.4 multi-image / multi-user capture repeatability validation"
    )
    parser.add_argument("manifest", type=Path, help="CSV or JSON cohort manifest")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    report = validate_manifest(args.manifest)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
