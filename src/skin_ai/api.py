from __future__ import annotations

import io
import os
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

from skin_ai.uv_engine import UVAnalysisEngine

MODEL_PATH = Path(os.environ.get("UVFD_MODEL_PATH", "models/uvfd_unet_v2_best.pt"))
app = FastAPI(title="Skin AI UV Analysis API", version="0.1.0")
_engine: UVAnalysisEngine | None = None


def get_engine() -> UVAnalysisEngine:
    global _engine
    if _engine is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail=f"Model checkpoint not found: {MODEL_PATH}")
        _engine = UVAnalysisEngine(MODEL_PATH)
    return _engine


@app.get("/health")
def health():
    return {"status": "ok", "model_available": MODEL_PATH.exists()}


@app.post("/v1/uv/analyze")
async def analyze_uv(image: UploadFile = File(...)):
    raw = await image.read()
    try:
        arr = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image") from exc
    result = get_engine().analyze_rgb(arr)
    return result.metrics
