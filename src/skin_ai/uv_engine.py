from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    def __init__(self, a: int, b: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(a, b, 3, padding=1, bias=False),
            nn.BatchNorm2d(b),
            nn.SiLU(inplace=True),
            nn.Conv2d(b, b, 3, padding=1, bias=False),
            nn.BatchNorm2d(b),
            nn.SiLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class ArtifactUNet(nn.Module):
    """Architecture compatible with the UVFD V2 checkpoint."""

    def __init__(self, base: int = 16):
        super().__init__()
        self.e1 = ConvBlock(3, base)
        self.e2 = ConvBlock(base, base * 2)
        self.e3 = ConvBlock(base * 2, base * 4)
        self.p = nn.MaxPool2d(2)
        self.b = ConvBlock(base * 4, base * 8)
        self.u3 = nn.ConvTranspose2d(base * 8, base * 4, 2, 2)
        self.d3 = ConvBlock(base * 8, base * 4)
        self.u2 = nn.ConvTranspose2d(base * 4, base * 2, 2, 2)
        self.d2 = ConvBlock(base * 4, base * 2)
        self.u1 = nn.ConvTranspose2d(base * 2, base, 2, 2)
        self.d1 = ConvBlock(base * 2, base)
        self.out = nn.Conv2d(base, 2, 1)

    def forward(self, x):
        e1 = self.e1(x)
        e2 = self.e2(self.p(e1))
        e3 = self.e3(self.p(e2))
        b = self.b(self.p(e3))
        d3 = self.d3(torch.cat([self.u3(b), e3], 1))
        d2 = self.d2(torch.cat([self.u2(d3), e2], 1))
        d1 = self.d1(torch.cat([self.u1(d2), e1], 1))
        return self.out(d1)


@dataclass
class UVAnalysisResult:
    metrics: dict[str, Any]
    dark_mask: np.ndarray
    light_mask: np.ndarray
    artifact_mask: np.ndarray
    porphyrin_mask: np.ndarray
    overlay_rgb: np.ndarray


class UVAnalysisEngine:
    """Artifact-aware UV/UVA fluorescence analysis.

    The artifact model excludes suspected hair/ruler/reflective pixels. It does
    not inpaint them. Porphyrin metrics are then calculated only from observed,
    non-excluded pixels. Outputs are research/development proxies, not a
    diagnostic measurement.
    """

    def __init__(self, checkpoint: str | Path, device: str | None = None):
        self.checkpoint_path = Path(checkpoint)
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        ckpt = torch.load(self.checkpoint_path, map_location=self.device)
        cfg = ckpt.get("config", {})
        self.size = int(cfg.get("size", 256))
        self.thresholds = [float(x) for x in ckpt.get("thresholds", [0.5, 0.5])]
        self.model = ArtifactUNet(base=int(cfg.get("base", 16))).to(self.device)
        self.model.load_state_dict(ckpt["model_state"])
        self.model.eval()
        self.model_meta = {
            "classes": ckpt.get("classes", ["dark_hair_ruler", "light_hair_uv_particles"]),
            "thresholds": self.thresholds,
            "input_size": self.size,
            "best_validation_macro_dice": float(ckpt.get("best_val_macro_dice", float("nan"))),
        }

    @torch.no_grad()
    def artifact_masks(self, image_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        h, w = image_rgb.shape[:2]
        resized = cv2.resize(image_rgb, (self.size, self.size), interpolation=cv2.INTER_LINEAR)
        x = torch.from_numpy(resized.astype(np.float32).transpose(2, 0, 1) / 255.0)[None].to(self.device)
        probs = torch.sigmoid(self.model(x))[0].cpu().numpy()
        dark = (probs[0] >= self.thresholds[0]).astype(np.uint8) * 255
        light = (probs[1] >= self.thresholds[1]).astype(np.uint8) * 255
        dark = cv2.resize(dark, (w, h), interpolation=cv2.INTER_NEAREST)
        light = cv2.resize(light, (w, h), interpolation=cv2.INTER_NEAREST)
        return dark, light, np.maximum(dark, light)

    @staticmethod
    def porphyrin_mask(image_rgb: np.ndarray, artifact_mask: np.ndarray) -> np.ndarray:
        rgb = image_rgb.astype(np.float32)
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        excess = r - (g + b) / 2.0
        lum = (r + g + b) / 3.0
        valid = (lum < 220) & (artifact_mask == 0)
        vals = excess[valid]
        if vals.size < 100:
            return np.zeros(valid.shape, dtype=np.uint8)
        med = np.median(vals)
        mad = np.median(np.abs(vals - med)) + 1.0
        z = (excess - med) / mad
        mask = ((z > 3.0) & valid & (r > 80)).astype(np.uint8) * 255
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    @staticmethod
    def _metrics(image_rgb: np.ndarray, artifact_mask: np.ndarray, porphyrin_mask: np.ndarray) -> dict[str, Any]:
        valid = artifact_mask == 0
        positive = porphyrin_mask > 0
        n, _, stats, centroids = cv2.connectedComponentsWithStats(positive.astype(np.uint8), 8)
        components = []
        for i in range(1, n):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if 3 <= area <= 5000:
                components.append({
                    "x": float(centroids[i, 0]),
                    "y": float(centroids[i, 1]),
                    "area_px": area,
                })
        red = image_rgb[..., 0].astype(np.float32) / 255.0
        return {
            "porphyrin_component_count_proxy": len(components),
            "porphyrin_area_fraction_valid": float(positive.sum() / max(1, valid.sum())),
            "porphyrin_red_intensity_proxy": float(red[positive].mean()) if positive.any() else 0.0,
            "artifact_area_fraction": float((artifact_mask > 0).mean()),
            "valid_area_fraction": float(valid.mean()),
            "components": components,
        }

    def analyze_rgb(self, image_rgb: np.ndarray) -> UVAnalysisResult:
        dark, light, artifact = self.artifact_masks(image_rgb)
        porphyrin = self.porphyrin_mask(image_rgb, artifact)
        metrics = self._metrics(image_rgb, artifact, porphyrin)
        metrics["dark_artifact_area_fraction"] = float((dark > 0).mean())
        metrics["light_artifact_area_fraction"] = float((light > 0).mean())
        metrics["model"] = self.model_meta
        metrics["interpretation"] = {
            "porphyrin_metrics_are_proxies": True,
            "artifact_pixels_are_excluded_not_inpainted": True,
            "diagnostic_use": False,
        }

        overlay = image_rgb.copy()
        overlay[dark > 0] = (255, 40, 40)
        overlay[light > 0] = (40, 255, 40)
        overlay[porphyrin > 0] = (255, 190, 0)
        return UVAnalysisResult(metrics, dark, light, artifact, porphyrin, overlay)

    def analyze_file(self, path: str | Path) -> UVAnalysisResult:
        return self.analyze_rgb(np.asarray(Image.open(path).convert("RGB")))

    @staticmethod
    def save_result(result: UVAnalysisResult, out_dir: str | Path) -> None:
        import json
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(result.dark_mask).save(out / "dark_artifact_mask.png")
        Image.fromarray(result.light_mask).save(out / "light_artifact_mask.png")
        Image.fromarray(result.artifact_mask).save(out / "artifact_mask.png")
        Image.fromarray(result.porphyrin_mask).save(out / "porphyrin_mask.png")
        Image.fromarray(result.overlay_rgb).save(out / "overlay.png")
        (out / "metrics.json").write_text(json.dumps(result.metrics, indent=2))
