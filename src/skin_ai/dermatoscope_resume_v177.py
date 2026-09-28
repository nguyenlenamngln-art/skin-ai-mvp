from __future__ import annotations

from fastapi import HTTPException

VERSION = "1.7.7"
DEFAULT_SUBJECT_KEY = "my_profile"
RESUMABLE_STATUSES = {"active", "incomplete"}


def _next_unresolved(session_payload: dict):
    for key, item in session_payload.get("positions", {}).items():
        if item.get("status") in {"incomplete", "rejected"}:
            return {
                "position_key": key,
                "region": item.get("region"),
                "subregion": item.get("subregion"),
                "attempts": int(item.get("attempts") or 0),
                "status": item.get("status"),
            }
    return None


def install_dermatoscope_resume_v177(product_api) -> None:
    from skin_ai.dermatoscope_session_v176 import _payload

    @product_api.app.get("/v1/dermatoscope/sessions/resumable/latest")
    def latest_resumable_dermatoscope_session(
        subject_key: str = DEFAULT_SUBJECT_KEY,
        simulator: bool = True,
    ):
        with product_api.store.connect() as con:
            row = con.execute(
                """
                SELECT * FROM dermatoscope_sessions
                WHERE subject_key=? AND simulator=? AND status IN ('active','incomplete')
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (subject_key, 1 if simulator else 0),
            ).fetchone()
        if not row:
            return {"session": None, "next_unresolved": None, "version": VERSION}
        session = _payload(row)
        next_unresolved = _next_unresolved(session)
        if not next_unresolved:
            return {"session": None, "next_unresolved": None, "version": VERSION}
        return {
            "session": session,
            "next_unresolved": next_unresolved,
            "version": VERSION,
        }

    @product_api.app.post("/v1/dermatoscope/sessions/{session_id}/resume")
    def resume_dermatoscope_session(session_id: str):
        with product_api.store.connect() as con:
            row = con.execute("SELECT * FROM dermatoscope_sessions WHERE id=?", (session_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Dermatoscope session not found")
            if row["status"] not in RESUMABLE_STATUSES:
                raise HTTPException(status_code=409, detail="Dermatoscope session is not resumable")
            session = _payload(row)
            next_unresolved = _next_unresolved(session)
            if not next_unresolved:
                raise HTTPException(status_code=409, detail="Dermatoscope session has no unresolved position")
            con.execute(
                "UPDATE dermatoscope_sessions SET status='active', completed_at=NULL WHERE id=?",
                (session_id,),
            )
            row = con.execute("SELECT * FROM dermatoscope_sessions WHERE id=?", (session_id,)).fetchone()
        return {
            "session": _payload(row),
            "next_unresolved": next_unresolved,
            "version": VERSION,
        }
