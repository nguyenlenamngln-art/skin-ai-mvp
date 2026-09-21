from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DEFAULT_ROUTINE = {"morning": ["Cleanser", "Moisturizer", "SPF"], "evening": ["Cleanser", "Moisturizer"]}


class ProductStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init_db(self) -> None:
        with self.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS scans (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    modality TEXT NOT NULL,
                    source_name TEXT,
                    metrics_json TEXT NOT NULL,
                    media_dir TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC);
                CREATE TABLE IF NOT EXISTS subjects (
                    id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_subjects_created_at ON subjects(created_at DESC);
                CREATE TABLE IF NOT EXISTS scan_sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    subject_id TEXT NOT NULL,
                    modality TEXT NOT NULL,
                    status TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    session_version TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_scan_sessions_created_at ON scan_sessions(created_at DESC);
                CREATE TABLE IF NOT EXISTS scan_session_items (
                    session_id TEXT NOT NULL,
                    region_code TEXT NOT NULL,
                    scan_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(session_id, region_code),
                    UNIQUE(scan_id)
                );
                CREATE INDEX IF NOT EXISTS idx_scan_session_items_session ON scan_session_items(session_id, position);
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL
                );
            """)
            if con.execute("SELECT 1 FROM settings WHERE key='routine'").fetchone() is None:
                con.execute("INSERT INTO settings(key, value_json) VALUES(?, ?)", ("routine", json.dumps(DEFAULT_ROUTINE)))

    def add_scan(self, *, scan_id: str, created_at: str, modality: str, source_name: str | None, metrics: dict[str, Any], media_dir: str | None) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO scans(id, created_at, modality, source_name, metrics_json, media_dir) VALUES(?,?,?,?,?,?)",
                (scan_id, created_at, modality, source_name, json.dumps(metrics), media_dir),
            )

    def list_scans(self, limit: int = 30, modality: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as con:
            if modality:
                rows = con.execute("SELECT * FROM scans WHERE modality=? ORDER BY created_at DESC LIMIT ?", (modality, limit)).fetchall()
            else:
                rows = con.execute("SELECT * FROM scans ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._scan_row(r) for r in rows]

    def get_scan(self, scan_id: str) -> dict[str, Any] | None:
        with self.connect() as con:
            row = con.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
        return self._scan_row(row) if row else None

    def create_subject(self, *, subject_id: str, display_name: str, created_at: str) -> dict[str, Any]:
        clean = " ".join(display_name.strip().split())[:80]
        if not clean:
            raise ValueError("Subject name is required")
        with self.connect() as con:
            duplicate = con.execute("SELECT * FROM subjects WHERE lower(display_name)=lower(?)", (clean,)).fetchone()
            if duplicate:
                return self._subject_row(duplicate)
            con.execute("INSERT INTO subjects(id, display_name, created_at) VALUES(?,?,?)", (subject_id, clean, created_at))
            row = con.execute("SELECT * FROM subjects WHERE id=?", (subject_id,)).fetchone()
        return self._subject_row(row)

    def list_subjects(self) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM subjects ORDER BY created_at ASC").fetchall()
        return [self._subject_row(r) for r in rows]

    def get_subject(self, subject_id: str) -> dict[str, Any] | None:
        with self.connect() as con:
            row = con.execute("SELECT * FROM subjects WHERE id=?", (subject_id,)).fetchone()
        return self._subject_row(row) if row else None

    def create_session(self, *, session_id: str, created_at: str, subject_id: str, modality: str, plan: list[str], session_version: str) -> dict[str, Any]:
        with self.connect() as con:
            con.execute(
                "INSERT INTO scan_sessions(id, created_at, completed_at, subject_id, modality, status, plan_json, session_version) VALUES(?,?,?,?,?,?,?,?)",
                (session_id, created_at, None, subject_id, modality, "in_progress", json.dumps(plan), session_version),
            )
        return self.get_session(session_id)

    def list_sessions(self, limit: int = 30) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM scan_sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._session_row(r, self._session_items(r["id"])) for r in rows]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as con:
            row = con.execute("SELECT * FROM scan_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            return None
        return self._session_row(row, self._session_items(session_id))

    def add_session_scan(self, *, session_id: str, region_code: str, scan_id: str, position: int, created_at: str) -> dict[str, Any]:
        with self.connect() as con:
            session = con.execute("SELECT * FROM scan_sessions WHERE id=?", (session_id,)).fetchone()
            if not session:
                raise ValueError("Session not found")
            if session["status"] != "in_progress":
                raise ValueError("Session is not in progress")
            con.execute(
                "INSERT INTO scan_session_items(session_id, region_code, scan_id, position, created_at) VALUES(?,?,?,?,?)",
                (session_id, region_code, scan_id, position, created_at),
            )
            count = con.execute("SELECT COUNT(*) FROM scan_session_items WHERE session_id=?", (session_id,)).fetchone()[0]
            plan = json.loads(session["plan_json"])
            if count >= len(plan):
                con.execute("UPDATE scan_sessions SET status='complete', completed_at=? WHERE id=?", (created_at, session_id))
        return self.get_session(session_id)

    def _session_items(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT i.session_id, i.region_code, i.scan_id, i.position, i.created_at, s.metrics_json, s.source_name FROM scan_session_items i JOIN scans s ON s.id=i.scan_id WHERE i.session_id=? ORDER BY i.position ASC",
                (session_id,),
            ).fetchall()
        out = []
        for r in rows:
            out.append({
                "session_id": r["session_id"],
                "region_code": r["region_code"],
                "scan_id": r["scan_id"],
                "position": r["position"],
                "created_at": r["created_at"],
                "source_name": r["source_name"],
                "metrics": json.loads(r["metrics_json"]),
            })
        return out

    def trends(self, limit: int = 90, modality: str | None = None) -> list[dict[str, Any]]:
        rows = list(reversed(self.list_scans(limit=limit, modality=modality)))
        out = []
        for row in rows:
            m = row["metrics"]
            tracking_key = m.get("tracking_series_key")
            if row["modality"] == "rgb":
                eligible = m.get("longitudinal_eligible")
                if eligible is False or (eligible is None and m.get("capture_quality") not in (None, "good")):
                    continue
                if not tracking_key:
                    continue
            elif row["modality"] == "uv":
                if m.get("uv_longitudinal_eligible") is not True or not m.get("uv_comparison_key") or not tracking_key:
                    continue
            base = {
                "scan_id": row["id"],
                "created_at": row["created_at"],
                "modality": row["modality"],
                "tracking_subject_id": m.get("tracking_subject_id"),
                "tracking_subject_name": m.get("tracking_subject_name"),
                "tracking_region_code": m.get("tracking_region_code"),
                "tracking_region_label": m.get("tracking_region_label"),
                "tracking_series_key": tracking_key,
                "scan_session_id": m.get("scan_session_id"),
            }
            if row["modality"] == "uv":
                base.update({
                    "uv_analysis_version": m.get("uv_analysis_version"),
                    "uv_model_signature": m.get("uv_model_signature"),
                    "uv_input_validation_version": m.get("uv_input_validation_version"),
                    "uv_input_validation_profile": m.get("uv_input_validation_profile"),
                    "uv_comparison_series_id": m.get("uv_comparison_series_id"),
                    "uv_comparison_key": m.get("uv_comparison_key"),
                    "uv_subject_label": m.get("uv_subject_label"),
                    "uv_anatomical_site": m.get("uv_anatomical_site"),
                    "uv_longitudinal_eligible": True,
                    "porphyrin_component_count_proxy": m.get("porphyrin_component_count_proxy"),
                    "porphyrin_area_fraction_valid": m.get("porphyrin_area_fraction_valid"),
                    "porphyrin_red_intensity_proxy": m.get("porphyrin_red_intensity_proxy"),
                    "artifact_area_fraction": m.get("artifact_area_fraction"),
                })
            elif row["modality"] == "rgb":
                base.update({
                    "rgb_engine_version": m.get("rgb_engine_version"),
                    "capture_protocol_version": m.get("capture_protocol_version"),
                    "capture_quality_score": m.get("capture_quality_score"),
                    "longitudinal_eligible": m.get("longitudinal_eligible", m.get("capture_quality") == "good"),
                    "redness_index_proxy": m.get("redness_index_proxy"),
                    "redness_area_fraction": m.get("redness_area_fraction"),
                    "pigmentation_area_fraction": m.get("pigmentation_area_fraction"),
                    "texture_index_proxy": m.get("texture_index_proxy"),
                    "red_spot_count_proxy": m.get("red_spot_count_proxy"),
                    "pigmented_spot_count_proxy": m.get("pigmented_spot_count_proxy"),
                    "capture_quality": m.get("capture_quality"),
                })
            out.append(base)
        return out

    def get_routine(self) -> dict[str, list[str]]:
        with self.connect() as con:
            row = con.execute("SELECT value_json FROM settings WHERE key='routine'").fetchone()
        return json.loads(row[0]) if row else DEFAULT_ROUTINE.copy()

    def set_routine(self, routine: dict[str, list[str]]) -> dict[str, list[str]]:
        with self.connect() as con:
            con.execute(
                "INSERT INTO settings(key,value_json) VALUES('routine',?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json",
                (json.dumps(routine),),
            )
        return routine

    @staticmethod
    def _scan_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "modality": row["modality"],
            "source_name": row["source_name"],
            "metrics": json.loads(row["metrics_json"]),
            "media_dir": row["media_dir"],
        }

    @staticmethod
    def _subject_row(row: sqlite3.Row) -> dict[str, Any]:
        return {"id": row["id"], "display_name": row["display_name"], "created_at": row["created_at"]}

    @staticmethod
    def _session_row(row: sqlite3.Row, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
            "subject_id": row["subject_id"],
            "modality": row["modality"],
            "status": row["status"],
            "plan": json.loads(row["plan_json"]),
            "session_version": row["session_version"],
            "items": items,
        }
