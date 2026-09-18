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

    def list_scans(self, limit: int = 30) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM scans ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._scan_row(r) for r in rows]

    def get_scan(self, scan_id: str) -> dict[str, Any] | None:
        with self.connect() as con:
            row = con.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
        return self._scan_row(row) if row else None

    def trends(self, limit: int = 90) -> list[dict[str, Any]]:
        rows = list(reversed(self.list_scans(limit=limit)))
        return [{
            "scan_id": row["id"],
            "created_at": row["created_at"],
            "porphyrin_component_count_proxy": row["metrics"].get("porphyrin_component_count_proxy"),
            "porphyrin_area_fraction_valid": row["metrics"].get("porphyrin_area_fraction_valid"),
            "porphyrin_red_intensity_proxy": row["metrics"].get("porphyrin_red_intensity_proxy"),
            "artifact_area_fraction": row["metrics"].get("artifact_area_fraction"),
        } for row in rows]

    def get_routine(self) -> dict[str, list[str]]:
        with self.connect() as con:
            row = con.execute("SELECT value_json FROM settings WHERE key='routine'").fetchone()
        return json.loads(row[0]) if row else DEFAULT_ROUTINE.copy()

    def set_routine(self, routine: dict[str, list[str]]) -> dict[str, list[str]]:
        with self.connect() as con:
            con.execute("INSERT INTO settings(key,value_json) VALUES('routine',?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json", (json.dumps(routine),))
        return routine

    @staticmethod
    def _scan_row(row: sqlite3.Row) -> dict[str, Any]:
        return {"id": row["id"], "created_at": row["created_at"], "modality": row["modality"], "source_name": row["source_name"], "metrics": json.loads(row["metrics_json"]), "media_dir": row["media_dir"]}
