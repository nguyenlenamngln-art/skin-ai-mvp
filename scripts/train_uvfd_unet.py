from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset


def source_group(key: str) -> str:
    m = re.match(r"^crop_\d+_(.+)$", key, re.I)
    if m:
        return m.group(1)
    m = re.match(r"^(image\d+)_crop_\d+$", key, re.I)
    if m:
        return m.group(1)
    return re.sub(r"_crop_\d+$", "", key, flags=re.I)


def classify(path: Path) -> str:
    q = "/" + path.as_posix().lower().strip("/") + "/"
    if "/black_masks/" in q:
        return "black_mask"
    if "/white_masks/" in q:
        return "white_mask"
    if "/images/" in q:
        return "image"
    return "other"


def pair_key(path: Path) -> str:
    parts = list(path.parts)
    low = [x.lower() for x in parts]
    for folder in ("images", "black_masks", "white_masks"):
        if folder in low:
            i = low.index(folder)
            rel = Path(*parts[i + 1 :]).with_suffix("")
            return rel.as_posix()
    return path.stem


def build_pairs(root: Path):
    by_key: dict[str, dict[str, Path]] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() != ".png":
            continue
        k = classify(path.relative_to(root))
        if k not in {"image", "black_mask", "white_mask"}:
            continue
        key = pair_key(path.relative_to(root))
        by_key.setdefault(key, {})[k] = path
    rows = []
    for key, d in sorted(by_key.items()):
        if "image" not in d or ("black_mask" not in d and "white_mask" not in d):
            continue
        rows.append(
            {
                "key": key,
                "source_group": source_group(key),
                "image": str(d["image"]),
                "black_mask": str(d["black_mask"]) if "black_mask" in d else "",
                "white_mask": str(d["white_mask"]) if "white_mask" in d else "",
            }
        )
    return rows


def assign_splits(rows, seed=42):
    groups = sorted({r["source_group"] for r in rows})
    rng = random.Random(seed)
    rng.shuffle(groups)
    n = len(groups)
    n_train = int(round(n * 0.70))
    n_val = int(round(n * 0.15))
    train_g = set(groups[:n_train])
    val_g = set(groups[n_train : n_train + n_val])
    test_g = set(groups[n_train + n_val :])
    for r in rows:
        g = r["source_group"]
        r["split"] = "train" if g in train_g else "val" if g in val_g else "test"
    return rows


class UVFDDataset(Dataset):
    def __init__(self, rows, size=128, augment=False, seed=42):
        self.rows = rows
        self.size = size
        self.augment = augment
        self.seed = seed

    def __len__(self):
        return len(self.rows)

    def _mask(self, p: str):
        if not p:
            return Image.new("L", (512, 512), 0)
        return Image.open(p).convert("L")

    def __getitem__(self, idx):
        r = self.rows[idx]
        image = Image.open(r["image"]).convert("RGB")
        black = self._mask(r["black_mask"])
        white = self._mask(r["white_mask"])

        if self.augment:
            rng = random.Random((self.seed + 1000003 * idx + random.randint(0, 2**20)))
            if rng.random() < 0.5:
                image = ImageOps.mirror(image)
                black = ImageOps.mirror(black)
                white = ImageOps.mirror(white)
            if rng.random() < 0.5:
                image = ImageOps.flip(image)
                black = ImageOps.flip(black)
                white = ImageOps.flip(white)
            k = rng.randrange(4)
            if k:
                angle = 90 * k
                image = image.rotate(angle)
                black = black.rotate(angle)
                white = white.rotate(angle)

        image = image.resize((self.size, self.size), Image.Resampling.BILINEAR)
        black = black.resize((self.size, self.size), Image.Resampling.NEAREST)
        white = white.resize((self.size, self.size), Image.Resampling.NEAREST)

        x = np.asarray(image, dtype=np.float32) / 255.0
        b = (np.asarray(black, dtype=np.uint8) > 127).astype(np.float32)
        w = (np.asarray(white, dtype=np.uint8) > 127).astype(np.float32)

        x = torch.from_numpy(x.transpose(2, 0, 1))
        y = torch.from_numpy(np.stack([b, w], axis=0))
        return x, y, r["key"]


class ConvBlock(nn.Module):
    def __init__(self, a, b):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(a, b, 3, padding=1, bias=False),
            nn.BatchNorm2d(b),
            nn.ReLU(inplace=True),
            nn.Conv2d(b, b, 3, padding=1, bias=False),
            nn.BatchNorm2d(b),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class TinyUNet(nn.Module):
    def __init__(self, base=16):
        super().__init__()
        self.e1 = ConvBlock(3, base)
        self.e2 = ConvBlock(base, base * 2)
        self.e3 = ConvBlock(base * 2, base * 4)
        self.pool = nn.MaxPool2d(2)
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
        e2 = self.e2(self.pool(e1))
        e3 = self.e3(self.pool(e2))
        b = self.b(self.pool(e3))
        d3 = self.d3(torch.cat([self.u3(b), e3], 1))
        d2 = self.d2(torch.cat([self.u2(d3), e2], 1))
        d1 = self.d1(torch.cat([self.u1(d2), e1], 1))
        return self.out(d1)


def dice_loss(logits, target, eps=1.0):
    prob = torch.sigmoid(logits)
    dims = (0, 2, 3)
    inter = (prob * target).sum(dims)
    den = prob.sum(dims) + target.sum(dims)
    dice = (2 * inter + eps) / (den + eps)
    return 1 - dice.mean()


def balanced_bce(logits, target):
    dims = (0, 2, 3)
    pos = target.sum(dims)
    total = torch.tensor(
        target.shape[0] * target.shape[2] * target.shape[3],
        device=target.device,
        dtype=target.dtype,
    )
    neg = total - pos
    pos_weight = torch.sqrt((neg + 1) / (pos + 1)).clamp(1.0, 20.0)
    return F.binary_cross_entropy_with_logits(
        logits, target, pos_weight=pos_weight.view(1, -1, 1, 1)
    )


def loss_fn(logits, target):
    return 0.5 * balanced_bce(logits, target) + 0.5 * dice_loss(logits, target)


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    tp = np.zeros(2, dtype=np.float64)
    fp = np.zeros(2, dtype=np.float64)
    fn = np.zeros(2, dtype=np.float64)
    losses = []
    for x, y, _ in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        losses.append(float(loss_fn(logits, y).item()))
        pred = torch.sigmoid(logits) >= 0.5
        true = y >= 0.5
        for c in range(2):
            p = pred[:, c]
            t = true[:, c]
            tp[c] += (p & t).sum().item()
            fp[c] += (p & ~t).sum().item()
            fn[c] += (~p & t).sum().item()
    dice = (2 * tp + 1) / (2 * tp + fp + fn + 1)
    iou = (tp + 1) / (tp + fp + fn + 1)
    precision = (tp + 1) / (tp + fp + 1)
    recall = (tp + 1) / (tp + fn + 1)
    return {
        "loss": float(np.mean(losses)) if losses else None,
        "dark_dice": float(dice[0]),
        "light_dice": float(dice[1]),
        "macro_dice": float(dice.mean()),
        "dark_iou": float(iou[0]),
        "light_iou": float(iou[1]),
        "macro_iou": float(iou.mean()),
        "dark_precision": float(precision[0]),
        "light_precision": float(precision[1]),
        "dark_recall": float(recall[0]),
        "light_recall": float(recall[1]),
    }


def save_samples(model, loader, device, out_dir: Path, limit=12):
    model.eval()
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    with torch.no_grad():
        for x, y, keys in loader:
            prob = torch.sigmoid(model(x.to(device))).cpu().numpy()
            xn = (x.numpy() * 255).clip(0, 255).astype(np.uint8)
            yn = y.numpy()
            for i in range(len(keys)):
                image = xn[i].transpose(1, 2, 0)
                panel = Image.fromarray(image)
                canv = Image.new("RGB", (image.shape[1] * 3, image.shape[0]))
                canv.paste(panel, (0, 0))
                gt = np.zeros_like(image)
                gt[..., 0] = (yn[i, 0] * 255).astype(np.uint8)
                gt[..., 1] = (yn[i, 1] * 255).astype(np.uint8)
                pred = np.zeros_like(image)
                pred[..., 0] = (prob[i, 0] >= 0.5).astype(np.uint8) * 255
                pred[..., 1] = (prob[i, 1] >= 0.5).astype(np.uint8) * 255
                canv.paste(Image.fromarray(gt), (image.shape[1], 0))
                canv.paste(Image.fromarray(pred), (image.shape[1] * 2, 0))
                safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", keys[i])[-100:]
                canv.save(out_dir / f"{saved:03d}_{safe}.png")
                saved += 1
                if saved >= limit:
                    return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="artifacts/uvfd_train_v1")
    ap.add_argument("--size", type=int, default=128)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--base", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = assign_splits(build_pairs(Path(args.root)), seed=args.seed)
    with (out / "manifest.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    counts = {}
    for split in ("train", "val", "test"):
        subset = [r for r in rows if r["split"] == split]
        counts[split] = {
            "samples": len(subset),
            "source_groups": len({r["source_group"] for r in subset}),
        }

    train_rows = [r for r in rows if r["split"] == "train"]
    val_rows = [r for r in rows if r["split"] == "val"]
    test_rows = [r for r in rows if r["split"] == "test"]

    train_ds = UVFDDataset(train_rows, args.size, augment=True, seed=args.seed)
    val_ds = UVFDDataset(val_rows, args.size, augment=False, seed=args.seed)
    test_ds = UVFDDataset(test_rows, args.size, augment=False, seed=args.seed)

    train_dl = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=2)
    val_dl = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=2)
    test_dl = DataLoader(test_ds, batch_size=args.batch, shuffle=False, num_workers=2)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TinyUNet(args.base).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)

    history = []
    best = -1.0
    best_path = out / "uvfd_tiny_unet_best.pt"

    for epoch in range(1, args.epochs + 1):
        model.train()
        tr_losses = []
        for x, y, _ in train_dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            logits = model(x)
            loss = loss_fn(logits, y)
            loss.backward()
            opt.step()
            tr_losses.append(float(loss.item()))
        val = evaluate(model, val_dl, device)
        rec = {"epoch": epoch, "train_loss": float(np.mean(tr_losses)), **{f"val_{k}": v for k, v in val.items()}}
        history.append(rec)
        print(json.dumps(rec))
        if val["macro_dice"] > best:
            best = val["macro_dice"]
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "config": vars(args),
                    "classes": ["dark_hair_ruler", "light_hair_uv_particles"],
                    "best_val_macro_dice": best,
                },
                best_path,
            )

    ckpt = torch.load(best_path, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    val_best = evaluate(model, val_dl, device)
    test = evaluate(model, test_dl, device)
    save_samples(model, test_dl, device, out / "sample_predictions", limit=12)

    metrics = {
        "device": str(device),
        "dataset_counts": counts,
        "image_size": args.size,
        "epochs": args.epochs,
        "best_validation": val_best,
        "test": test,
        "history": history,
        "scientific_note": "Development baseline only. Test split is held out by inferred original UVFD source-image group, not independent patients/devices.",
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
