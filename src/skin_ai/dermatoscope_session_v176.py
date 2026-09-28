from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import Form, HTTPException

VERSION = "1.7.6"
DEFAULT_SUBJECT_KEY = "my_profile"
ALLOWED_POSITION_STATUS = {"accepted", "rejected", "skipped", "incomplete"}
ALLOWED_SESSION_STATUS = {"active", "complete", "incomplete", "cancelled"}
REGION_SUBREGIONS = {
    "forehead": ["left", "center", "right"],
    "left_cheek": ["upper", "middle", "lower"],
    "right_cheek": ["upper", "middle", "lower"],
    "nose": ["center"],
    "chin": ["upper", "lower"],
    "custom": ["custom"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _payload(row):
    positions = json.loads(row["positions_json"])
    counts = {key: 0 for key in ("accepted", "rejected", "skipped", "incomplete")}
    for item in positions.values():
        status = item.get("status", "incomplete")
        if status in counts:
            counts[status] += 1
    return {
        "id": row["id"],
        "subject_key": row["subject_key"],
        "region": row["region"],
        "simulator": bool(row["simulator"]),
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "completed_at": row["completed_at"],
        "positions": positions,
        "counts": counts,
        "version": VERSION,
    }


def install_dermatoscope_session_v176(product_api) -> None:
    with product_api.store.connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS dermatoscope_sessions (
                id TEXT PRIMARY KEY,
                subject_key TEXT NOT NULL,
                region TEXT NOT NULL,
                simulator INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                positions_json TEXT NOT NULL
            )
            """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_derm_sessions_subject_created ON dermatoscope_sessions(subject_key, created_at DESC)"
        )

    @product_api.app.post("/v1/dermatoscope/sessions")
    def create_dermatoscope_session(
        region: str = Form(...),
        simulator: bool = Form(True),
        subject_key: str = Form(DEFAULT_SUBJECT_KEY),
    ):
        region = region.strip().lower()
        if region not in REGION_SUBREGIONS:
            raise HTTPException(status_code=422, detail="Unsupported dermatoscope region")
        session_id = uuid.uuid4().hex[:16]
        created_at = _now()
        positions = {
            f"{region}/{sub}": {
                "region": region,
                "subregion": sub,
                "status": "incomplete",
                "attempts": 0,
                "capture_id": None,
                "updated_at": created_at,
            }
            for sub in REGION_SUBREGIONS[region]
        }
        with product_api.store.connect() as con:
            con.execute(
                """
                INSERT INTO dermatoscope_sessions(
                    id, subject_key, region, simulator, status,
                    created_at, updated_at, completed_at, positions_json
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    session_id,
                    subject_key,
                    region,
                    1 if simulator else 0,
                    "active",
                    created_at,
                    created_at,
                    None,
                    json.dumps(positions),
                ),
            )
            row = con.execute("SELECT * FROM dermatoscope_sessions WHERE id=?", (session_id,)).fetchone()
        return _payload(row)

    @product_api.app.post("/v1/dermatoscope/sessions/{session_id}/positions")
    def update_dermatoscope_session_position(
        session_id: str,
        region: str = Form(...),
        subregion: str = Form(...),
        status: str = Form(...),
        attempts: int = Form(0),
        capture_id: str | None = Form(None),
    ):
        status = status.strip().lower()
        if status not in ALLOWED_POSITION_STATUS:
            raise HTTPException(status_code=422, detail="Unsupported position status")
        if attempts < 0 or attempts > 20:
            raise HTTPException(status_code=422, detail="Invalid attempts")
        with product_api.store.connect() as con:
            row = con.execute("SELECT * FROM dermatoscope_sessions WHERE id=?", (session_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Dermatoscope session not found")
            positions = json.loads(row["positions_json"])
            key = f"{region}/{subregion}"
            if key not in positions:
                raise HTTPException(status_code=422, detail="Position is not part of this session")
            positions[key] = {
                **positions[key],
                "status": status,
                "attempts": attempts,
                "capture_id": capture_id,
                "updated_at": _now(),
            }
            updated_at = _now()
            con.execute(
                "UPDATE dermatoscope_sessions SET positions_json=?, updated_at=? WHERE id=?",
                (json.dumps(positions), updated_at, session_id),
            )
            row = con.execute("SELECT * FROM dermatoscope_sessions WHERE id=?", (session_id,)).fetchone()
        return _payload(row)

    @product_api.app.post("/v1/dermatoscope/sessions/{session_id}/finish")
    def finish_dermatoscope_session(session_id: str, status: str = Form(...)):
        status = status.strip().lower()
        if status not in {"complete", "incomplete", "cancelled"}:
            raise HTTPException(status_code=422, detail="Invalid final session status")
        with product_api.store.connect() as con:
            row = con.execute("SELECT * FROM dermatoscope_sessions WHERE id=?", (session_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Dermatoscope session not found")
            positions = json.loads(row["positions_json"])
            if status == "complete" and any(v.get("status") == "incomplete" for v in positions.values()):
                status = "incomplete"
            now = _now()
            con.execute(
                "UPDATE dermatoscope_sessions SET status=?, updated_at=?, completed_at=? WHERE id=?",
                (status, now, now, session_id),
            )
            row = con.execute("SELECT * FROM dermatoscope_sessions WHERE id=?", (session_id,)).fetchone()
        return _payload(row)

    @product_api.app.get("/v1/dermatoscope/sessions/{session_id}")
    def get_dermatoscope_session(session_id: str):
        with product_api.store.connect() as con:
            row = con.execute("SELECT * FROM dermatoscope_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Dermatoscope session not found")
        return _payload(row)
