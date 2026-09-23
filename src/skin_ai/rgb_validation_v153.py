from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np

from skin_ai.rgb_engine_v152 import RGBAnalysisEngineV152


VALIDATION_VERSION = "1.5.3"
ENGINE_UNDER_TEST = "1.5.2"
PHOTOMETRIC_VARIANTS = ("baseline", "exposure_down", "exposure_up", "contrast_down", "contrast_up")


def _variant(image_rgb: np.ndarray, name: str) -> np.ndarray:
    x = image_rgb.astype(np.float32)
    if name == "baseline":
        out = x
    elif name == "exposure_down":
        out = x * 0.92
    elif name == "exposure_up":
        out = x * 1.08
    elif name == "contrast_down":
        out = (x - 127.5) * 0.95 + 127.5
    elif name == "contrast_up":
        out = (x - 127.5) * 1.05 + 127.5
    else:
        raise ValueError(f"Unknown validation variant: {name}")
    return np.clip(out, 0, 255).astype(np.uint8)


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    intersection = int(np.logical_and(a, b).sum())
    union = int(np.logical_or(a, b).sum())
    return float(intersection / max(1, union))


def _mask_snapshot(engine: RGBAnalysisEngineV152, image_rgb: np.ndarray) -> tuple[np.ndarray | None, dict[str, Any]]:
    face = engine._detect_largest_face(engine.face_detector, image_rgb)
    if face is None:
        return None, {"face_detected": False}

    base, excluded = engine._face_geometry(image_rgb.shape[:2], face)
    skin_mask, segmentation = engine._adaptive_skin_mask(image_rgb, face, base, excluded)
    anatomy = engine._anatomical_regularity(skin_mask, face)
    envelope = engine._outer_boundary_mask(skin_mask, face)

    return skin_mask, {
        "face_detected": True,
        "face_box": [int(v) for v in face],
        "skin_pixels": int(skin_mask.sum()),
        "outer_envelope_pixels": int(envelope.sum()),
        "anatomical_mask_fallback": bool(segmentation.get("anatomical_mask_fallback", False)),
        "anatomical_mask_retention_fraction": float(segmentation.get("anatomical_mask_retention_fraction", 1.0)),
        "anatomical_mask_added_fraction": float(segmentation.get("anatomical_mask_added_fraction", 0.0)),
        "anatomical_mask_changed_fraction": float(segmentation.get("anatomical_mask_changed_fraction", 0.0)),
        "anatomical_skin_support_fraction": float(anatomy.get("anatomical_skin_support_fraction", 0.0)),
        "anatomical_outer_boundary_score": float(anatomy.get("anatomical_outer_boundary_score", 0.0)),
        "skin_mask_component_count": int(anatomy.get("skin_mask_component_count", 0)),
        "skin_mask_hole_count": int(anatomy.get("skin_mask_hole_count", 0)),
        "skin_mask_perimeter_ratio": float(anatomy.get("skin_mask_perimeter_ratio", 0.0)),
    }


def validate_rgb_image(image_rgb: np.ndarray, *, source_name: str = "image") -> dict[str, Any]:
    """Validate V1.5.2 anatomical-mask repeatability on one real RGB image.

    V1.5.3 is a validation harness only. It does not alter redness,
    pigmentation, regional trend gates, or Capture Protocol V1.4.
    """
    engine = RGBAnalysisEngineV152()
    snapshots: dict[str, dict[str, Any]] = {}
    masks: dict[str, np.ndarray] = {}

    for name in PHOTOMETRIC_VARIANTS:
        mask, metrics = _mask_snapshot(engine, _variant(image_rgb, name))
        snapshots[name] = metrics
        if mask is not None:
            masks[name] = mask

    baseline = snapshots["baseline"]
    if not baseline.get("face_detected"):
        return {
            "validation_version": VALIDATION_VERSION,
            "engine_under_test": ENGINE_UNDER_TEST,
            "source_name": source_name,
            "face_detected": False,
            "validation_pass": False,
            "failure_reasons": ["baseline_face_not_detected"],
            "variants": snapshots,
        }

    base_mask = masks["baseline"]
    base_area = max(1, int(base_mask.sum()))
    detected = [name for name in PHOTOMETRIC_VARIANTS if snapshots[name].get("face_detected")]
    ious = {name: _iou(base_mask, masks[name]) for name in detected if name != "baseline"}
    area_changes = {
        name: abs(int(masks[name].sum()) - base_area) / base_area
        for name in detected
        if name != "baseline"
    }
    fallback_rate = float(
        sum(bool(snapshots[name].get("anatomical_mask_fallback")) for name in detected) / max(1, len(detected))
    )
    supports = [
        float(snapshots[name].get("anatomical_skin_support_fraction", 0.0))
        for name in detected
    ]

    min_iou = min(ious.values()) if ious else 0.0
    max_area_change = max(area_changes.values()) if area_changes else 1.0
    min_support = min(supports) if supports else 0.0

    reasons: list[str] = []
    if len(detected) != len(PHOTOMETRIC_VARIANTS):
        reasons.append("face_detection_not_stable")
    if min_iou < 0.85:
        reasons.append("mask_iou_below_0_85")
    if max_area_change > 0.12:
        reasons.append("mask_area_drift_above_12pct")
    if fallback_rate > 0.20:
        reasons.append("fallback_rate_above_20pct")
    if min_support < 0.70:
        reasons.append("anatomical_support_below_70pct")

    return {
        "validation_version": VALIDATION_VERSION,
        "engine_under_test": ENGINE_UNDER_TEST,
        "source_name": source_name,
        "face_detected": True,
        "validation_pass": not reasons,
        "failure_reasons": reasons,
        "summary": {
            "variants_detected": len(detected),
            "variants_total": len(PHOTOMETRIC_VARIANTS),
            "min_mask_iou_vs_baseline": round(float(min_iou), 4),
            "max_mask_area_change_fraction": round(float(max_area_change), 4),
            "fallback_rate": round(float(fallback_rate), 4),
            "min_anatomical_skin_support_fraction": round(float(min_support), 4),
        },
        "variants": snapshots,
    }


def validate_paths(paths: Iterable[Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if bgr is None:
            rows.append({
                "validation_version": VALIDATION_VERSION,
                "engine_under_test": ENGINE_UNDER_TEST,
                "source_name": path.name,
                "face_detected": False,
                "validation_pass": False,
                "failure_reasons": ["image_decode_failed"],
            })
            continue
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        rows.append(validate_rgb_image(rgb, source_name=path.name))

    passed = sum(bool(row.get("validation_pass")) for row in rows)
    return {
        "validation_version": VALIDATION_VERSION,
        "engine_under_test": ENGINE_UNDER_TEST,
        "image_count": len(rows),
        "passed_count": passed,
        "failed_count": len(rows) - passed,
        "all_passed": bool(rows) and passed == len(rows),
        "images": rows,
    }


def _expand_inputs(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        p = Path(value)
        if p.is_dir():
            for suffix in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"):
                paths.extend(p.glob(suffix))
        elif p.is_file():
            paths.append(p)
    return sorted(set(paths))


def main() -> None:
    parser = argparse.ArgumentParser(description="RGB V1.5.3 real-image anatomical mask validation")
    parser.add_argument("inputs", nargs="+", help="Image files or directories")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    report = validate_paths(_expand_inputs(args.inputs))
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
