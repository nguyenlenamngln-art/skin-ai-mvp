from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image

VERSION = "1.7.3"
DEFAULT_SUBJECT_KEY = "my_profile"


def _load_gray(path: str, size: int = 160) -> np.ndarray:
    image = Image.open(path).convert("L").resize((size, size), Image.Resampling.BILINEAR)
    arr = np.asarray(image, dtype=np.float32)
    arr = (arr - float(arr.mean())) / max(float(arr.std()), 1.0)
    return arr


def _crop_pair(a: np.ndarray, b: np.ndarray, dx: int, dy: int):
    h, w = a.shape
    x0a, x1a = max(0, dx), min(w, w + dx)
    y0a, y1a = max(0, dy), min(h, h + dy)
    x0b, x1b = max(0, -dx), min(w, w - dx)
    y0b, y1b = max(0, -dy), min(h, h - dy)
    if x1a - x0a < w * 0.75 or y1a - y0a < h * 0.75:
        return None, None
    return a[y0a:y1a, x0a:x1a], b[y0b:y1b, x0b:x1b]


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    aa = a - float(a.mean())
    bb = b - float(b.mean())
    denom = math.sqrt(float((aa * aa).sum()) * float((bb * bb).sum()))
    if denom <= 1e-8:
        return 0.0
    return float((aa * bb).sum() / denom)


def _register(reference_path: str, current_path: str) -> dict:
    ref = _load_gray(reference_path)
    cur = _load_gray(current_path)
    best = {"corr": -1.0, "dx": 0, "dy": 0}
    for dy in range(-16, 17, 2):
        for dx in range(-16, 17, 2):
            a, b = _crop_pair(ref, cur, dx, dy)
            if a is None:
                continue
            c = _corr(a, b)
            if c > best["corr"]:
                best = {"corr": c, "dx": dx, "dy": dy}

    shift_fraction = math.sqrt(best["dx"] ** 2 + best["dy"] ** 2) / 160.0
    similarity = max(0.0, min(1.0, (best["corr"] + 1.0) / 2.0))
    score = round(100.0 * (0.85 * similarity + 0.15 * max(0.0, 1.0 - shift_fraction / 0.14)), 1)
    if score >= 78.0 and shift_fraction <= 0.10:
        status = "comparable"
    elif score >= 62.0 and shift_fraction <= 0.15:
        status = "borderline"
    else:
        status = "not_comparable"
    return {
        "status": status,
        "score": score,
        "correlation": round(float(best["corr"]), 4),
        "shift_px": {"x": int(best["dx"]), "y": int(best["dy"])},
        "shift_fraction": round(shift_fraction, 4),
        "method": "normalized_grayscale_translation_v1",
        "thresholds_provisional": True,
        "validated_for_de500": False,
    }


def install_dermatoscope_registration_v173(product_api) -> None:
    @product_api.app.get("/v1/dermatoscope/comparability/{capture_id}")
    def dermatoscope_comparability(capture_id: str, subject_key: str = DEFAULT_SUBJECT_KEY):
        with product_api.store.connect() as con:
            current = con.execute(
                "SELECT * FROM dermatoscope_captures WHERE id=? AND subject_key=?",
                (capture_id, subject_key),
            ).fetchone()
            if not current:
                return {"capture_id": capture_id, "status": "missing", "version": VERSION}
            baseline = con.execute(
                """
                SELECT * FROM dermatoscope_captures
                WHERE subject_key=? AND region=? AND subregion=?
                  AND illumination_mode=? AND brightness_level=? AND simulator=?
                  AND longitudinal_status='accepted'
                ORDER BY created_at ASC LIMIT 1
                """,
                (
                    subject_key,
                    current["region"],
                    current["subregion"],
                    current["illumination_mode"],
                    current["brightness_level"],
                    current["simulator"],
                ),
            ).fetchone()
        if not baseline:
            return {
                "capture_id": capture_id,
                "status": "no_baseline",
                "position_key": f"{current['region']}/{current['subregion']}",
                "version": VERSION,
            }
        if baseline["id"] == current["id"]:
            return {
                "capture_id": capture_id,
                "baseline_id": baseline["id"],
                "status": "baseline",
                "score": 100.0,
                "position_key": f"{current['region']}/{current['subregion']}",
                "thresholds_provisional": True,
                "validated_for_de500": False,
                "version": VERSION,
            }
        result = _register(str(Path(baseline["media_path"])), str(Path(current["media_path"])))
        return {
            "capture_id": capture_id,
            "baseline_id": baseline["id"],
            "position_key": f"{current['region']}/{current['subregion']}",
            "simulator": bool(current["simulator"]),
            "version": VERSION,
            **result,
        }
