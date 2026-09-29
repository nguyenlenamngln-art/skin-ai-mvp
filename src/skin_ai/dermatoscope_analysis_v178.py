from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import HTTPException
from PIL import Image

VERSION = "1.7.8"
DEFAULT_SUBJECT_KEY = "my_profile"


def _largest_component(mask: np.ndarray) -> np.ndarray:
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if n <= 1:
        return mask.astype(bool)
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return labels == idx


def _optical_field(rgb: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # Bright-content component works for circular/vignetted scope images, while
    # the ellipse fallback keeps simulator/ordinary camera images usable.
    candidate = _largest_component(gray > 12)
    coverage = float(candidate.mean())
    if 0.45 <= coverage <= 0.98:
        mask = candidate.astype(np.uint8)
        kernel = np.ones((9, 9), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1).astype(bool)
        method = "largest_nonblack_component"
    else:
        mask = np.zeros((h, w), np.uint8)
        cv2.ellipse(mask, (w // 2, h // 2), (max(1, int(w * .46)), max(1, int(h * .46))), 0, 0, 360, 1, -1)
        mask = mask.astype(bool)
        method = "central_ellipse_fallback"
    return mask, {"method": method, "coverage_fraction": round(float(mask.mean()), 4)}


def _glare_mask(rgb: np.ndarray, field: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    bright = hsv[..., 2] >= 245
    low_sat = hsv[..., 1] <= 70
    mask = bright & low_sat & field
    mask = cv2.dilate(mask.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=1)
    return mask.astype(bool)


def _hair_mask(rgb: np.ndarray, field: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # Dark thin structures are highlighted by a black-hat transform. This is a
    # provisional artifact detector, not an ML hair segmentation model.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    mask = (blackhat >= 18) & field
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)
    return mask.astype(bool)


def _ruler_mask(rgb: np.ndarray, field: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    lower = np.zeros((h, w), bool)
    lower[int(h * .55):] = True
    dark = (gray < 75) & field & lower
    # Connect repeated tick marks/text into a band. Require a plausible wide,
    # shallow component before calling it a ruler.
    connected = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 17), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(connected, 8)
    best = None
    for i in range(1, n):
        x, y, ww, hh, area = stats[i]
        if ww >= int(w * .28) and hh <= int(h * .18) and area >= max(20, int(w * h * .0008)):
            score = ww / max(hh, 1)
            if best is None or score > best[0]:
                best = (score, i, x, y, ww, hh)
    mask = np.zeros((h, w), np.uint8)
    if best is None:
        return mask.astype(bool), {"detected": False, "pixels_per_mm": None, "confidence": 0.0, "provisional": True}
    _, idx, x, y, ww, hh = best
    component = labels == idx
    mask[component] = 1
    mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=1)

    # Estimate spacing between vertical dark tick clusters by projection. The
    # value is explicitly provisional until DE-500 scale geometry is validated.
    roi = dark[y:y + hh, x:x + ww]
    projection = roi.sum(axis=0).astype(np.float32)
    threshold = max(2.0, float(np.percentile(projection, 82)))
    xs = np.flatnonzero(projection >= threshold)
    centers: list[float] = []
    if xs.size:
        groups = np.split(xs, np.where(np.diff(xs) > 2)[0] + 1)
        centers = [float(g.mean()) for g in groups if len(g) >= 1]
    spacings = np.diff(centers) if len(centers) >= 3 else np.array([])
    plausible = spacings[(spacings >= 3) & (spacings <= max(4, ww * .2))]
    px_per_mm = float(np.median(plausible)) if plausible.size >= 2 else None
    confidence = min(.85, .35 + .08 * len(centers)) if px_per_mm else .35
    return mask.astype(bool), {
        "detected": True,
        "bbox": [int(x), int(y), int(ww), int(hh)],
        "pixels_per_mm": round(px_per_mm, 3) if px_per_mm else None,
        "confidence": round(float(confidence), 3),
        "provisional": True,
    }


def _metrics(rgb: np.ndarray, valid: np.ndarray) -> dict[str, Any]:
    count = int(valid.sum())
    if count < 500:
        raise ValueError("insufficient valid skin pixels")
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    # OpenCV Lab uses 0..255 encoding. Center a* around 128 for an interpretable
    # relative redness index; do not treat this as calibrated erythema.
    a = lab[..., 1] - 128.0
    l = lab[..., 0] * (100.0 / 255.0)
    redness_values = a[valid]
    lightness_values = l[valid]
    pigment_index = 100.0 - lightness_values
    lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    gradient = np.sqrt(gx * gx + gy * gy)
    return {
        "redness": {
            "median_relative_a": round(float(np.median(redness_values)), 3),
            "p90_relative_a": round(float(np.percentile(redness_values, 90)), 3),
        },
        "pigmentation": {
            "median_inverse_lightness": round(float(np.median(pigment_index)), 3),
            "p90_inverse_lightness": round(float(np.percentile(pigment_index, 90)), 3),
        },
        "texture": {
            "laplacian_abs_mean": round(float(np.mean(np.abs(lap[valid]))), 3),
            "gradient_mean": round(float(np.mean(gradient[valid])), 3),
        },
        "valid_skin_pixels": count,
        "measurement_status": "provisional_relative_only",
    }


def _write_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def analyze_image(path: Path, artifact_dir: Path | None = None) -> dict[str, Any]:
    rgb = np.asarray(Image.open(path).convert("RGB"))
    field, field_info = _optical_field(rgb)
    glare = _glare_mask(rgb, field)
    hair = _hair_mask(rgb, field)
    ruler, ruler_info = _ruler_mask(rgb, field)
    valid = field & ~glare & ~hair & ~ruler
    metrics = _metrics(rgb, valid)
    masks = {
        "optical_field_fraction": round(float(field.mean()), 4),
        "valid_skin_fraction": round(float(valid.mean()), 4),
        "glare_fraction": round(float(glare.mean()), 4),
        "hair_fraction": round(float(hair.mean()), 4),
        "ruler_fraction": round(float(ruler.mean()), 4),
    }
    artifacts: dict[str, str] = {}
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        for name, mask in (("valid_skin", valid), ("glare", glare), ("hair", hair), ("ruler", ruler), ("optical_field", field)):
            out = artifact_dir / f"analysis_{name}.png"
            _write_mask(out, mask)
            artifacts[name] = out.name
    return {
        "analysis_version": VERSION,
        "analysis_type": "classical_interpretable_foundation",
        "validated_for_de500": False,
        "clinically_calibrated": False,
        "field": field_info,
        "ruler": ruler_info,
        "masks": masks,
        "metrics": metrics,
        "artifacts": artifacts,
    }


def _numeric_delta(current: dict, baseline: dict) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for family in ("redness", "pigmentation", "texture"):
        out[family] = {}
        for key, value in current[family].items():
            base = baseline.get(family, {}).get(key)
            if isinstance(value, (int, float)) and isinstance(base, (int, float)):
                out[family][key] = {
                    "baseline": base,
                    "current": value,
                    "absolute_delta": round(float(value - base), 3),
                    "relative_delta_pct": round(float((value - base) / abs(base) * 100.0), 2) if abs(base) > 1e-8 else None,
                }
    return out


def install_dermatoscope_analysis_v178(product_api) -> None:
    with product_api.store.connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS dermatoscope_analyses (
                capture_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                analysis_version TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )

    @product_api.app.post("/v1/dermatoscope/captures/{capture_id}/analyze")
    def analyze_dermatoscope_capture(capture_id: str, subject_key: str = DEFAULT_SUBJECT_KEY):
        with product_api.store.connect() as con:
            row = con.execute(
                "SELECT * FROM dermatoscope_captures WHERE id=? AND subject_key=?",
                (capture_id, subject_key),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Dermatoscope capture not found")
        if "longitudinal_status" in row.keys() and row["longitudinal_status"] != "accepted":
            raise HTTPException(status_code=409, detail="Only accepted captures can enter longitudinal analysis")
        media_path = Path(row["media_path"])
        try:
            result = analyze_image(media_path, media_path.parent)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Image analysis failed: {exc}") from exc

        # Compare only with the first earlier accepted capture from an identical
        # acquisition series. Simulator and real-device data never mix.
        with product_api.store.connect() as con:
            baseline = con.execute(
                """
                SELECT * FROM dermatoscope_captures
                WHERE subject_key=? AND region=? AND subregion=?
                  AND illumination_mode=? AND brightness_level=? AND simulator=?
                  AND longitudinal_status='accepted' AND id<>? AND created_at<?
                ORDER BY created_at ASC LIMIT 1
                """,
                (subject_key, row["region"], row["subregion"], row["illumination_mode"], row["brightness_level"], row["simulator"], row["id"], row["created_at"]),
            ).fetchone()
            baseline_analysis = None
            if baseline:
                ar = con.execute("SELECT result_json FROM dermatoscope_analyses WHERE capture_id=?", (baseline["id"],)).fetchone()
                if ar:
                    baseline_analysis = json.loads(ar["result_json"])
        result["baseline_id"] = baseline["id"] if baseline else capture_id
        result["is_baseline"] = baseline is None
        result["position_key"] = f"{row['region']}/{row['subregion']}"
        if baseline_analysis:
            result["delta"] = _numeric_delta(result["metrics"], baseline_analysis["metrics"])
            result["delta_status"] = "provisional_relative_only"
        else:
            result["delta"] = None
            result["delta_status"] = "baseline_or_baseline_analysis_missing"
        result["artifact_urls"] = {name: f"/media/dermatoscope/{capture_id}/{filename}" for name, filename in result["artifacts"].items()}
        with product_api.store.connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO dermatoscope_analyses(capture_id, analysis_version, result_json) VALUES(?,?,?)",
                (capture_id, VERSION, json.dumps(result)),
            )
        return result

    @product_api.app.get("/v1/dermatoscope/captures/{capture_id}/analysis")
    def get_dermatoscope_analysis(capture_id: str):
        with product_api.store.connect() as con:
            row = con.execute("SELECT result_json FROM dermatoscope_analyses WHERE capture_id=?", (capture_id,)).fetchone()
        if not row:
            return {"capture_id": capture_id, "analysis": None, "analysis_version": VERSION}
        return json.loads(row["result_json"])
