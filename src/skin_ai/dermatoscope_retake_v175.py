from __future__ import annotations

import json
from pathlib import Path

from skin_ai.dermatoscope_registration_v173 import _register

VERSION = "1.7.5"
DEFAULT_SUBJECT_KEY = "my_profile"
REJECTED_STATUS = "rejected_position"


def install_dermatoscope_retake_v175(product_api) -> None:
    with product_api.store.connect() as con:
        cols = {r[1] for r in con.execute("PRAGMA table_info(dermatoscope_captures)").fetchall()}
        if "longitudinal_status" not in cols:
            con.execute(
                "ALTER TABLE dermatoscope_captures ADD COLUMN longitudinal_status TEXT NOT NULL DEFAULT 'accepted'"
            )
        if "comparison_json" not in cols:
            con.execute("ALTER TABLE dermatoscope_captures ADD COLUMN comparison_json TEXT")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_derm_longitudinal_status ON dermatoscope_captures(longitudinal_status, region, subregion, created_at DESC)"
        )

    @product_api.app.post("/v1/dermatoscope/captures/{capture_id}/validate-position")
    def validate_dermatoscope_position(capture_id: str, subject_key: str = DEFAULT_SUBJECT_KEY):
        with product_api.store.connect() as con:
            current = con.execute(
                "SELECT * FROM dermatoscope_captures WHERE id=? AND subject_key=?",
                (capture_id, subject_key),
            ).fetchone()
            if not current:
                return {"capture_id": capture_id, "status": "missing", "version": VERSION}

            baseline = con.execute(
                """
                SELECT * FROM dermatoscope_captures
                WHERE subject_key=? AND region=? AND subregion=?
                  AND illumination_mode=? AND brightness_level=? AND simulator=?
                  AND id<>? AND longitudinal_status='accepted'
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (
                    subject_key,
                    current["region"],
                    current["subregion"],
                    current["illumination_mode"],
                    current["brightness_level"],
                    current["simulator"],
                    current["id"],
                ),
            ).fetchone()

            if not baseline:
                payload = {
                    "capture_id": capture_id,
                    "baseline_id": capture_id,
                    "position_key": f"{current['region']}/{current['subregion']}",
                    "status": "baseline",
                    "accepted": True,
                    "retake_required": False,
                    "thresholds_provisional": True,
                    "validated_for_de500": False,
                    "version": VERSION,
                }
                con.execute(
                    "UPDATE dermatoscope_captures SET longitudinal_status='accepted', comparison_json=? WHERE id=?",
                    (json.dumps(payload), capture_id),
                )
                return payload

        result = _register(str(Path(baseline["media_path"])), str(Path(current["media_path"])))
        accepted = result["status"] in {"comparable", "borderline"}
        longitudinal_status = "accepted" if accepted else REJECTED_STATUS
        payload = {
            "capture_id": capture_id,
            "baseline_id": baseline["id"],
            "position_key": f"{current['region']}/{current['subregion']}",
            "accepted": accepted,
            "retake_required": not accepted,
            "longitudinal_status": longitudinal_status,
            "simulator": bool(current["simulator"]),
            "version": VERSION,
            **result,
        }
        with product_api.store.connect() as con:
            con.execute(
                "UPDATE dermatoscope_captures SET longitudinal_status=?, comparison_json=? WHERE id=?",
                (longitudinal_status, json.dumps(payload), capture_id),
            )
        return payload

    @product_api.app.get("/v1/dermatoscope/captures/{capture_id}/validation")
    def get_dermatoscope_position_validation(capture_id: str, subject_key: str = DEFAULT_SUBJECT_KEY):
        with product_api.store.connect() as con:
            row = con.execute(
                "SELECT longitudinal_status, comparison_json FROM dermatoscope_captures WHERE id=? AND subject_key=?",
                (capture_id, subject_key),
            ).fetchone()
        if not row:
            return {"capture_id": capture_id, "status": "missing", "version": VERSION}
        return {
            "capture_id": capture_id,
            "longitudinal_status": row["longitudinal_status"],
            "comparison": json.loads(row["comparison_json"]) if row["comparison_json"] else None,
            "version": VERSION,
        }
