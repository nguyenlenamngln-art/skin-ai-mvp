from __future__ import annotations

import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import File, Form, HTTPException, UploadFile
from PIL import Image

VERSION = "1.7.1"
DEVICE = "IBOOLO_DE500"
ALLOWED_REGIONS = {"forehead", "left_cheek", "right_cheek", "nose", "chin", "custom"}
ALLOWED_SUBREGIONS = {"upper", "middle", "lower", "center", "left", "right", "custom"}
ALLOWED_MODES = {"polarized", "non_polarized", "uv"}


def _clean(value: str | None, max_len: int = 80) -> str | None:
    if value is None:
        return None
    out = " ".join(value.strip().split())[:max_len]
    return out or None


def install_dermatoscope_capture_v171(product_api) -> None:
    scan_root: Path = product_api.SCAN_DIR / "dermatoscope"
    scan_root.mkdir(parents=True, exist_ok=True)

    with product_api.store.connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS dermatoscope_captures (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                device_model TEXT NOT NULL,
                region TEXT NOT NULL,
                subregion TEXT NOT NULL,
                sequence_index INTEGER NOT NULL,
                illumination_mode TEXT NOT NULL,
                brightness_level INTEGER NOT NULL,
                simulator INTEGER NOT NULL,
                source_name TEXT,
                media_path TEXT NOT NULL,
                quality_json TEXT NOT NULL,
                client_json TEXT NOT NULL
            )
            """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_dermatoscope_region_created ON dermatoscope_captures(region, subregion, created_at DESC)"
        )

    @product_api.app.post("/v1/dermatoscope/captures")
    async def create_dermatoscope_capture(
        image: UploadFile = File(...),
        region: str = Form(...),
        subregion: str = Form(...),
        sequence_index: int = Form(...),
        illumination_mode: str = Form("polarized"),
        brightness_level: int = Form(2),
        simulator: bool = Form(True),
        sharpness_score: float | None = Form(None),
        exposure_score: float | None = Form(None),
        motion_score: float | None = Form(None),
        glare_fraction: float | None = Form(None),
        client_device: str | None = Form(None),
        camera_label: str | None = Form(None),
    ):
        region = region.strip().lower()
        subregion = subregion.strip().lower()
        illumination_mode = illumination_mode.strip().lower()
        if region not in ALLOWED_REGIONS:
            raise HTTPException(status_code=422, detail="Unsupported dermatoscope region")
        if subregion not in ALLOWED_SUBREGIONS:
            raise HTTPException(status_code=422, detail="Unsupported dermatoscope subregion")
        if illumination_mode not in ALLOWED_MODES:
            raise HTTPException(status_code=422, detail="Unsupported dermatoscope illumination mode")
        if brightness_level not in (1, 2, 3):
            raise HTTPException(status_code=422, detail="brightness_level must be 1, 2, or 3")
        if sequence_index < 1 or sequence_index > 20:
            raise HTTPException(status_code=422, detail="Invalid sequence_index")

        raw = await image.read()
        if len(raw) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image exceeds 20 MB")
        try:
            rgb = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid image") from exc
        if min(rgb.size) < 160:
            raise HTTPException(status_code=422, detail="Dermatoscope image is too small")

        capture_id = uuid.uuid4().hex[:16]
        created_at = datetime.now(timezone.utc).isoformat()
        out_dir = scan_root / capture_id
        out_dir.mkdir(parents=True, exist_ok=True)
        media_path = out_dir / "original.jpg"
        rgb.save(media_path, quality=94)

        quality = {
            "sharpness_score": sharpness_score,
            "exposure_score": exposure_score,
            "motion_score": motion_score,
            "glare_fraction": glare_fraction,
            "thresholds_provisional": True,
            "validated_for_de500": False,
        }
        client = {
            "client_device": _clean(client_device),
            "camera_label": _clean(camera_label),
        }
        with product_api.store.connect() as con:
            con.execute(
                """
                INSERT INTO dermatoscope_captures(
                    id, created_at, device_model, region, subregion, sequence_index,
                    illumination_mode, brightness_level, simulator, source_name,
                    media_path, quality_json, client_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    capture_id,
                    created_at,
                    DEVICE,
                    region,
                    subregion,
                    sequence_index,
                    illumination_mode,
                    brightness_level,
                    1 if simulator else 0,
                    image.filename,
                    str(media_path),
                    json.dumps(quality),
                    json.dumps(client),
                ),
            )

        return {
            "id": capture_id,
            "created_at": created_at,
            "device_model": DEVICE,
            "region": region,
            "subregion": subregion,
            "sequence_index": sequence_index,
            "illumination_mode": illumination_mode,
            "brightness_level": brightness_level,
            "simulator": bool(simulator),
            "quality": quality,
            "client": client,
            "media": {"original": f"/media/dermatoscope/{capture_id}/original.jpg"},
            "analysis_status": "capture_only",
            "capture_protocol_version": VERSION,
        }

    @product_api.app.get("/v1/dermatoscope/captures")
    def list_dermatoscope_captures(limit: int = 100):
        limit = min(max(limit, 1), 500)
        with product_api.store.connect() as con:
            rows = con.execute(
                "SELECT * FROM dermatoscope_captures ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        out = []
        for row in rows:
            out.append(
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "device_model": row["device_model"],
                    "region": row["region"],
                    "subregion": row["subregion"],
                    "sequence_index": row["sequence_index"],
                    "illumination_mode": row["illumination_mode"],
                    "brightness_level": row["brightness_level"],
                    "simulator": bool(row["simulator"]),
                    "quality": json.loads(row["quality_json"]),
                    "client": json.loads(row["client_json"]),
                    "media": {"original": f"/media/dermatoscope/{row['id']}/original.jpg"},
                    "analysis_status": "capture_only",
                    "capture_protocol_version": VERSION,
                }
            )
        return out
