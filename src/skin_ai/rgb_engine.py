from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


@dataclass
class RGBAnalysisResult:
    metrics: dict[str, Any]
    original_rgb: np.ndarray
    skin_region_rgb: np.ndarray
    redness_map_rgb: np.ndarray
    pigmentation_map_rgb: np.ndarray
    overlay_rgb: np.ndarray


class RGBAnalysisEngine:
    """Transparent phone-RGB skin tracking baseline.

    V1.1 keeps the measurement pipeline stable. Product milestone V1.2 adds
    a capture-quality protocol that scores whether a photo is suitable for
    longitudinal comparison without changing the RGB measurement version.
    """

    VERSION = "1.1"
    SEGMENTATION_METHOD = "adaptive_lab_chroma_v1_1"
    CAPTURE_PROTOCOL_VERSION = "1.0"

    def __init__(self) -> None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.face_detector = cv2.CascadeClassifier(str(cascade_path))
        if self.face_detector.empty():
            raise RuntimeError(f"Unable to load OpenCV face detector: {cascade_path}")

    @staticmethod
    def _detect_largest_face(detector: cv2.CascadeClassifier, image_rgb: np.ndarray) -> tuple[int, int, int, int] | None:
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.equalizeHist(gray)
        h, w = gray.shape
        min_side = max(48, int(min(h, w) * 0.12))
        faces = detector.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(min_side, min_side))
        if len(faces) == 0:
            return None
        x, y, fw, fh = max(faces, key=lambda r: int(r[2]) * int(r[3]))
        return int(x), int(y), int(fw), int(fh)

    @staticmethod
    def _face_geometry(shape: tuple[int, int], face: tuple[int, int, int, int]) -> tuple[np.ndarray, np.ndarray]:
        h, w = shape
        x, y, fw, fh = face
        base = np.zeros((h, w), np.uint8)
        center = (x + fw // 2, y + int(fh * 0.52))
        axes = (max(1, int(fw * 0.40)), max(1, int(fh * 0.50)))
        cv2.ellipse(base, center, axes, 0, 0, 360, 255, -1)

        excluded = np.zeros((h, w), np.uint8)
        features = [(0.32, 0.38, 0.15, 0.085),(0.68, 0.38, 0.15, 0.085),(0.50, 0.76, 0.20, 0.08)]
        for cx, cy, ax, ay in features:
            cv2.ellipse(excluded,(int(x + fw * cx), int(y + fh * cy)),(max(1, int(fw * ax)), max(1, int(fh * ay))),0, 0, 360, 255, -1)
        excluded &= base
        return base, excluded

    @staticmethod
    def _seed_mask(shape: tuple[int, int], face: tuple[int, int, int, int], candidate: np.ndarray) -> np.ndarray:
        h, w = shape
        x, y, fw, fh = face
        seed = np.zeros((h, w), dtype=bool)
        def add(rx0: float, ry0: float, rx1: float, ry1: float) -> None:
            x0 = max(0, int(x + fw * rx0)); x1 = min(w, int(x + fw * rx1))
            y0 = max(0, int(y + fh * ry0)); y1 = min(h, int(y + fh * ry1))
            if x1 > x0 and y1 > y0: seed[y0:y1, x0:x1] = True
        add(0.18, 0.49, 0.38, 0.67); add(0.62, 0.49, 0.82, 0.67); add(0.38, 0.20, 0.62, 0.31)
        return seed & candidate

    @staticmethod
    def _adaptive_skin_mask(image_rgb: np.ndarray, face: tuple[int, int, int, int], base: np.ndarray, excluded: np.ndarray) -> tuple[np.ndarray, dict[str, float | str]]:
        candidate = (base > 0) & (excluded == 0)
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
        seed = RGBAnalysisEngine._seed_mask(image_rgb.shape[:2], face, candidate)
        seed &= (L > 45) & (L < 245) & (hsv[..., 1] < 220)
        if int(seed.sum()) < 250:
            valid = candidate & (L > 35) & (L < 248) & (hsv[..., 1] < 220)
            method = "geometry_exposure_fallback_v1_1"; chroma_distance_threshold = -1.0
        else:
            av = a[seed]; bv = b[seed]
            a_med = float(np.median(av)); b_med = float(np.median(bv))
            a_scale = max(2.5, float(1.4826 * np.median(np.abs(av - a_med)))); b_scale = max(2.5, float(1.4826 * np.median(np.abs(bv - b_med))))
            distance = np.sqrt(((a - a_med) / a_scale) ** 2 + ((b - b_med) / b_scale) ** 2)
            chroma_distance_threshold = 4.5
            valid = candidate & (L > 35) & (L < 248) & (hsv[..., 1] < 220) & (distance < chroma_distance_threshold)
            method = RGBAnalysisEngine.SEGMENTATION_METHOD
        mask = valid.astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); valid = mask > 0
        base_n = max(1, int((base > 0).sum())); candidate_n = max(1, int(candidate.sum()))
        return valid, {"segmentation_method": method,"skin_region_fraction_of_face": float(valid.sum() / base_n),"skin_region_fraction_of_candidate": float(valid.sum() / candidate_n),"excluded_feature_fraction_of_face": float((excluded > 0).sum() / base_n),"chroma_distance_threshold": float(chroma_distance_threshold)}

    @staticmethod
    def _ramp_score(value: float, fail_low: float, good_low: float, good_high: float, fail_high: float) -> float:
        if good_low <= value <= good_high: return 100.0
        if value < good_low:
            if value <= fail_low: return 0.0
            return 100.0 * (value - fail_low) / max(1e-9, good_low - fail_low)
        if value >= fail_high: return 0.0
        return 100.0 * (fail_high - value) / max(1e-9, fail_high - good_high)

    @staticmethod
    def _one_sided_score(value: float, good_max: float, fail_max: float) -> float:
        if value <= good_max: return 100.0
        if value >= fail_max: return 0.0
        return 100.0 * (fail_max - value) / max(1e-9, fail_max - good_max)

    @staticmethod
    def _quality(image_rgb: np.ndarray, face: tuple[int, int, int, int], skin_mask: np.ndarray) -> dict[str, Any]:
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY); hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        valid = skin_mask > 0; h, w = image_rgb.shape[:2]; x, y, fw, fh = face
        face_area_fraction = float((fw * fh) / (h * w)); face_center_x = (x + fw / 2) / w; face_center_y = (y + fh / 2) / h
        center_offset = float(np.sqrt((face_center_x - 0.5) ** 2 + (face_center_y - 0.46) ** 2))
        brightness = float(hsv[..., 2][valid].mean()) if valid.any() else 0.0
        blur_var = float(cv2.Laplacian(gray[y:y+fh, x:x+fw], cv2.CV_64F).var())
        clipped_dark = float((hsv[..., 2][valid] < 25).mean()) if valid.any() else 1.0; clipped_bright = float((hsv[..., 2][valid] > 245).mean()) if valid.any() else 1.0
        mid = x + fw // 2; yy, xx = np.indices(valid.shape); left = valid & (xx < mid); right = valid & (xx >= mid)
        if left.any() and right.any():
            left_luma = float(gray[left].mean()); right_luma = float(gray[right].mean()); luma_mean = max(20.0, (left_luma + right_luma) / 2.0); left_right_asymmetry = float(abs(left_luma - right_luma) / luma_mean)
        else: left_right_asymmetry = 1.0
        subscores = {"lighting": RGBAnalysisEngine._ramp_score(brightness, 45, 85, 205, 235),"sharpness": float(np.clip((blur_var - 25.0) / 75.0 * 100.0, 0.0, 100.0)),"framing": RGBAnalysisEngine._ramp_score(face_area_fraction, 0.07, 0.18, 0.60, 0.82),"centering": RGBAnalysisEngine._one_sided_score(center_offset, 0.08, 0.30),"clipping": RGBAnalysisEngine._one_sided_score(clipped_dark + clipped_bright, 0.03, 0.20),"symmetry": RGBAnalysisEngine._one_sided_score(left_right_asymmetry, 0.12, 0.40)}
        weights = {"lighting": 0.25, "sharpness": 0.20, "framing": 0.20, "centering": 0.15, "clipping": 0.10, "symmetry": 0.10}; score = float(sum(subscores[k] * weights[k] for k in weights))
        flags: list[str] = []
        if brightness < 70: flags.append("too_dark")
        if brightness > 220: flags.append("too_bright")
        if blur_var < 50: flags.append("blurry")
        if face_area_fraction < 0.15: flags.append("face_too_small")
        if face_area_fraction > 0.68: flags.append("face_too_close")
        if center_offset > 0.18: flags.append("face_off_center")
        if clipped_dark > 0.10: flags.append("shadow_clipping")
        if clipped_bright > 0.10: flags.append("highlight_clipping")
        if left_right_asymmetry > 0.30: flags.append("uneven_light_or_pose")
        severe = {"too_dark", "too_bright", "blurry", "face_too_small", "face_too_close"}
        if score >= 85 and not flags: quality = "good"
        elif score >= 65 and len(severe.intersection(flags)) <= 1: quality = "usable"
        else: quality = "poor"
        guidance_map = {"too_dark":"Move to brighter, soft frontal light.","too_bright":"Reduce direct light or move away from strong highlights.","blurry":"Hold the phone steady and refocus before capture.","face_too_small":"Move closer so the face fills about 20–60% of the frame.","face_too_close":"Move the phone farther away so the full face is visible.","face_off_center":"Center the face and keep the camera level.","shadow_clipping":"Use more even frontal light to reduce deep shadows.","highlight_clipping":"Avoid direct glare and strong overhead light.","uneven_light_or_pose":"Face the camera more directly and use even light on both sides."}
        guidance = [guidance_map[f] for f in flags if f in guidance_map] or ["Capture conditions are suitable. Reuse similar lighting, distance and angle for repeat scans."]
        return {"capture_protocol_version": RGBAnalysisEngine.CAPTURE_PROTOCOL_VERSION,"capture_quality": quality,"capture_quality_score": round(score, 1),"longitudinal_eligible": bool(quality == "good"),"quality_flags": flags,"quality_guidance": guidance,"quality_subscores": {k: round(v, 1) for k, v in subscores.items()},"brightness_mean_0_255": brightness,"sharpness_laplacian_var": blur_var,"face_area_fraction": face_area_fraction,"face_center_offset_fraction": center_offset,"left_right_luminance_asymmetry": left_right_asymmetry,"dark_clipped_fraction": clipped_dark,"bright_clipped_fraction": clipped_bright}

    @staticmethod
    def _connected_count(binary: np.ndarray,min_area: int,max_area: int,*,max_aspect: float = 3.2,min_extent: float = 0.12) -> tuple[int, list[dict[str, float]]]:
        n, _, stats, centroids = cv2.connectedComponentsWithStats(binary.astype(np.uint8), 8); comps: list[dict[str, float]] = []
        for i in range(1, n):
            area = int(stats[i, cv2.CC_STAT_AREA]); width = int(stats[i, cv2.CC_STAT_WIDTH]); height = int(stats[i, cv2.CC_STAT_HEIGHT])
            if not (min_area <= area <= max_area): continue
            aspect = max(width / max(1, height), height / max(1, width)); extent = area / max(1, width * height)
            if aspect > max_aspect or extent < min_extent: continue
            comps.append({"x": float(centroids[i, 0]),"y": float(centroids[i, 1]),"area_px": float(area),"aspect": float(aspect),"extent": float(extent)})
        return len(comps), comps

    @staticmethod
    def _draw_skin_boundary(image_rgb: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
        out = image_rgb.copy(); contours, _ = cv2.findContours(skin_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(out, contours, -1, (70, 210, 140), 2, cv2.LINE_AA); return out

    def analyze_rgb(self, image_rgb: np.ndarray) -> RGBAnalysisResult:
        if image_rgb.ndim != 3 or image_rgb.shape[2] != 3: raise ValueError("Expected an RGB image with shape HxWx3")
        if min(image_rgb.shape[:2]) < 160: raise ValueError("Image is too small; use at least 160 px on the shortest side")
        face = self._detect_largest_face(self.face_detector, image_rgb)
        if face is None: raise ValueError("No frontal face detected. Use a well-lit, front-facing photo with one face visible.")
        base, excluded = self._face_geometry(image_rgb.shape[:2], face); valid, segmentation = self._adaptive_skin_mask(image_rgb, face, base, excluded)
        if int(valid.sum()) < 2500: raise ValueError("Not enough usable facial skin pixels. Try a closer, evenly lit front-facing photo.")
        analysis_valid = cv2.erode(valid.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1) > 0
        if int(analysis_valid.sum()) < 2000: analysis_valid = valid
        quality = self._quality(image_rgb, face, valid)
        rgb = image_rgb.astype(np.float32); lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB).astype(np.float32); L, a = lab[..., 0], lab[..., 1]
        denom = rgb.sum(axis=2) + 1.0; red_chroma = rgb[..., 0] / denom; redness_index = float(red_chroma[analysis_valid].mean())
        a_blur = cv2.GaussianBlur(a, (0, 0), 5.0); red_resid = a - a_blur; rv = red_resid[analysis_valid]; r_med = float(np.median(rv)); r_mad = float(np.median(np.abs(rv - r_med))) + 1.0; red_thr = max(4.5, r_med + 2.5 * r_mad)
        redness_mask = analysis_valid & (red_resid > red_thr); redness_mask = cv2.morphologyEx(redness_mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0; red_spot_count, red_components = self._connected_count(redness_mask, 6, 900)
        L_blur = cv2.GaussianBlur(L, (0, 0), 7.0); dark_resid = L_blur - L; dv = dark_resid[analysis_valid]; d_med = float(np.median(dv)); d_mad = float(np.median(np.abs(dv - d_med))) + 1.0; dark_thr = max(8.0, d_med + 2.6 * d_mad)
        pigmentation_mask = analysis_valid & (dark_resid > dark_thr); pigmentation_mask = cv2.morphologyEx(pigmentation_mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0; pigmentation_count, pigmentation_components = self._connected_count(pigmentation_mask, 6, 1200)
        local_texture = np.abs(L - cv2.GaussianBlur(L, (0, 0), 1.6)); texture_index = float(local_texture[analysis_valid].mean() / 255.0); valid_n = max(1, int(analysis_valid.sum())); x, y, fw, fh = face
        metrics: dict[str, Any] = {"rgb_engine_version": self.VERSION,"redness_index_proxy": redness_index,"redness_area_fraction": float(redness_mask.sum() / valid_n),"red_spot_count_proxy": red_spot_count,"pigmentation_area_fraction": float(pigmentation_mask.sum() / valid_n),"pigmented_spot_count_proxy": pigmentation_count,"texture_index_proxy": texture_index,"face_bbox": {"x": x, "y": y, "w": fw, "h": fh},"valid_skin_area_fraction_of_image": float(analysis_valid.mean()),"red_components": red_components,"pigmentation_components": pigmentation_components,**segmentation,**quality,"interpretation": {"measurement_type": "relative_phone_rgb_proxies","best_use": "longitudinal_tracking_under_similar_capture_conditions","diagnostic_use": False,"segmentation_note": "adaptive color/geometry mask; not anatomical landmark segmentation","capture_quality_note": "capture score is a repeatability gate, not a clinical quality score","not_equivalent_to": ["dermatologist assessment", "polarized imaging", "UV fluorescence imaging"]}}
        skin_region = image_rgb.copy(); skin_region[~valid] = (skin_region[~valid] * 0.22).astype(np.uint8); skin_region[valid] = (0.85 * skin_region[valid] + 0.15 * np.array([70, 220, 140])).astype(np.uint8); skin_region = self._draw_skin_boundary(skin_region, valid)
        redness_map = image_rgb.copy(); pigmentation_map = image_rgb.copy(); overlay = image_rgb.copy(); redness_map[~valid] = (redness_map[~valid] * 0.50).astype(np.uint8); pigmentation_map[~valid] = (pigmentation_map[~valid] * 0.50).astype(np.uint8)
        redness_map[redness_mask] = (0.45 * redness_map[redness_mask] + 0.55 * np.array([255, 55, 70])).astype(np.uint8); pigmentation_map[pigmentation_mask] = (0.45 * pigmentation_map[pigmentation_mask] + 0.55 * np.array([90, 70, 210])).astype(np.uint8); overlay[redness_mask] = (0.50 * overlay[redness_mask] + 0.50 * np.array([255, 55, 70])).astype(np.uint8); overlay[pigmentation_mask] = (0.50 * overlay[pigmentation_mask] + 0.50 * np.array([90, 70, 210])).astype(np.uint8); overlay = self._draw_skin_boundary(overlay, valid)
        return RGBAnalysisResult(metrics, image_rgb, skin_region, redness_map, pigmentation_map, overlay)

    def analyze_file(self, path: str | Path) -> RGBAnalysisResult:
        return self.analyze_rgb(np.asarray(Image.open(path).convert("RGB")))

    @staticmethod
    def save_result(result: RGBAnalysisResult, out_dir: str | Path) -> None:
        import json
        out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(result.original_rgb).save(out / "original.jpg", quality=92); Image.fromarray(result.skin_region_rgb).save(out / "skin_region.png"); Image.fromarray(result.redness_map_rgb).save(out / "redness_map.png"); Image.fromarray(result.pigmentation_map_rgb).save(out / "pigmentation_map.png"); Image.fromarray(result.overlay_rgb).save(out / "rgb_overlay.png"); (out / "metrics.json").write_text(json.dumps(result.metrics, indent=2))
