from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def robust_porhyrin_mask(
    image_bgr: np.ndarray,
    exclude_mask: np.ndarray | None = None,
    z_threshold: float = 3.0,
    min_red: int = 80,
) -> np.ndarray:
    """Detect warm red/orange fluorescence while excluding known artifact pixels.

    This is a measurement baseline, not a clinical detector. Artifact pixels are
    excluded from both background estimation and positive detections.
    """
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    excess = r - (g + b) / 2.0
    lum = (r + g + b) / 3.0

    valid = lum < 220
    if exclude_mask is not None:
        exc = exclude_mask > 0
        if exc.shape != valid.shape:
            exc = cv2.resize(exc.astype(np.uint8), (valid.shape[1], valid.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        valid &= ~exc

    vals = excess[valid]
    if vals.size < 100:
        raise ValueError("too few valid pixels after artifact exclusion")
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med))) + 1.0
    z = (excess - med) / mad
    mask = ((z > z_threshold) & valid & (r > min_red)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return mask


def analyze_cleaned(
    image_bgr: np.ndarray,
    artifact_mask: np.ndarray | None = None,
    min_component_area: int = 3,
    max_component_area: int = 5000,
) -> dict:
    por = robust_porhyrin_mask(image_bgr, artifact_mask)

    valid = np.ones(por.shape, dtype=bool)
    if artifact_mask is not None:
        exc = artifact_mask > 0
        if exc.shape != valid.shape:
            exc = cv2.resize(exc.astype(np.uint8), (valid.shape[1], valid.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        valid &= ~exc

    n, labels, stats, cent = cv2.connectedComponentsWithStats((por > 0).astype(np.uint8), 8)
    comps = []
    for i in range(1, n):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if min_component_area <= area <= max_component_area:
            comps.append({"x": float(cent[i, 0]), "y": float(cent[i, 1]), "area_px": area})

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    positive = por > 0
    denom = max(1, int(valid.sum()))
    return {
        "porphyrin_component_count_proxy": len(comps),
        "porphyrin_area_fraction_valid": float(positive.sum() / denom),
        "porphyrin_red_intensity_proxy": float(rgb[..., 0][positive].mean()) if positive.any() else 0.0,
        "artifact_area_fraction": float((~valid).mean()),
        "valid_area_fraction": float(valid.mean()),
        "components": comps,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--artifact-mask")
    ap.add_argument("--mask-out")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    img = cv2.imread(args.image, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"cannot read image: {args.image}")
    artifact = cv2.imread(args.artifact_mask, cv2.IMREAD_GRAYSCALE) if args.artifact_mask else None
    result = analyze_cleaned(img, artifact)
    print(json.dumps(result, indent=2))

    if args.mask_out:
        cv2.imwrite(args.mask_out, robust_porhyrin_mask(img, artifact))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
