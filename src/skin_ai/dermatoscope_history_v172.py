from __future__ import annotations

import json
from typing import Any

VERSION = "1.7.2"


def _row_payload(row) -> dict[str, Any]:
    return {
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
    }


def install_dermatoscope_history_v172(product_api) -> None:
    with product_api.store.connect() as con:
        cols = {r[1] for r in con.execute("PRAGMA table_info(dermatoscope_captures)").fetchall()}
        if "subject_key" not in cols:
            con.execute("ALTER TABLE dermatoscope_captures ADD COLUMN subject_key TEXT NOT NULL DEFAULT 'default'")
        if "is_baseline" not in cols:
            con.execute("ALTER TABLE dermatoscope_captures ADD COLUMN is_baseline INTEGER NOT NULL DEFAULT 0")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_derm_subject_position_created ON dermatoscope_captures(subject_key, region, subregion, illumination_mode, brightness_level, created_at DESC)"
        )

    @product_api.app.get("/v1/dermatoscope/history")
    def dermatoscope_history(subject_key: str, region: str | None = None, subregion: str | None = None, limit: int = 100):
        limit = min(max(limit, 1), 500)
        where = ["subject_key = ?"]
        args: list[Any] = [subject_key]
        if region:
            where.append("region = ?")
            args.append(region)
        if subregion:
            where.append("subregion = ?")
            args.append(subregion)
        args.append(limit)
        with product_api.store.connect() as con:
            rows = con.execute(
                f"SELECT * FROM dermatoscope_captures WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ?",
                tuple(args),
            ).fetchall()
        return [{**_row_payload(r), "is_baseline": bool(r["is_baseline"])} for r in rows]

    @product_api.app.get("/v1/dermatoscope/baseline")
    def dermatoscope_baseline(subject_key: str, region: str, subregion: str, illumination_mode: str = "polarized", brightness_level: int = 2):
        with product_api.store.connect() as con:
            row = con.execute(
                """
                SELECT * FROM dermatoscope_captures
                WHERE subject_key=? AND region=? AND subregion=?
                  AND illumination_mode=? AND brightness_level=?
                ORDER BY is_baseline DESC, created_at ASC
                LIMIT 1
                """,
                (subject_key, region, subregion, illumination_mode, brightness_level),
            ).fetchone()
        if not row:
            return {"baseline": None, "position_key": f"{region}/{subregion}"}
        return {"baseline": {**_row_payload(row), "is_baseline": bool(row["is_baseline"])}, "position_key": f"{region}/{subregion}"}

    @product_api.app.get("/v1/dermatoscope/position-summary")
    def dermatoscope_position_summary(subject_key: str):
        with product_api.store.connect() as con:
            rows = con.execute(
                """
                SELECT region, subregion, illumination_mode, brightness_level,
                       COUNT(*) AS capture_count,
                       MIN(created_at) AS first_capture_at,
                       MAX(created_at) AS latest_capture_at,
                       MAX(is_baseline) AS has_baseline
                FROM dermatoscope_captures
                WHERE subject_key=?
                GROUP BY region, subregion, illumination_mode, brightness_level
                ORDER BY latest_capture_at DESC
                """,
                (subject_key,),
            ).fetchall()
        return [
            {
                "region": r["region"],
                "subregion": r["subregion"],
                "illumination_mode": r["illumination_mode"],
                "brightness_level": r["brightness_level"],
                "capture_count": r["capture_count"],
                "first_capture_at": r["first_capture_at"],
                "latest_capture_at": r["latest_capture_at"],
                "has_baseline": bool(r["has_baseline"]),
                "position_key": f"{r['region']}/{r['subregion']}",
            }
            for r in rows
        ]
