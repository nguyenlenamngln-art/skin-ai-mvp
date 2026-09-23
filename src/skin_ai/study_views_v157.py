from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from skin_ai.study_access_v157 import (
    VERSION,
    _get_participant_by_subject,
    _study_subject_from_request,
    is_study_scan,
)


def install_study_views_v157(product_api) -> None:
    app = product_api.app
    store = product_api.store

    def unauthorized():
        return JSONResponse(
            status_code=401,
            content={"detail": {"code": "study_access_required", "message": "Tester Study Mode access is required."}},
        )

    @app.get("/v1/study/subjects")
    def study_subjects(request: Request):
        subject_id = _study_subject_from_request(request, store)
        if not subject_id:
            return unauthorized()
        subject = store.get_subject(subject_id)
        return [subject] if subject else []

    @app.get("/v1/study/scans")
    def study_scans(request: Request, limit: int = 100, modality: str | None = None):
        subject_id = _study_subject_from_request(request, store)
        if not subject_id:
            return unauthorized()
        limit = min(max(limit, 1), 100)
        rows = []
        for scan in store.list_scans(limit=1000, modality=modality):
            metrics = scan.get("metrics") or {}
            if not is_study_scan(scan) or metrics.get("tracking_subject_id") != subject_id:
                continue
            rows.append(product_api.public_scan(scan))
            if len(rows) >= limit:
                break
        return rows

    @app.get("/v1/study/trends")
    def study_trends(request: Request, limit: int = 180, modality: str | None = None):
        subject_id = _study_subject_from_request(request, store)
        if not subject_id:
            return unauthorized()
        limit = min(max(limit, 1), 365)
        rows = [
            row
            for row in store.trends(limit=1000, modality=modality)
            if row.get("tracking_subject_id") == subject_id
        ]
        return rows[-limit:]

    @app.get("/v1/study/sessions")
    def study_sessions(request: Request, limit: int = 100):
        subject_id = _study_subject_from_request(request, store)
        if not subject_id:
            return unauthorized()
        limit = min(max(limit, 1), 100)
        rows = []
        for session in store.list_sessions(limit=1000):
            if session.get("subject_id") != subject_id:
                continue
            rows.append(product_api.public_session(session))
            if len(rows) >= limit:
                break
        return rows

    @app.get("/v1/study/profile")
    def study_profile(request: Request):
        subject_id = _study_subject_from_request(request, store)
        if not subject_id:
            return unauthorized()
        participant = _get_participant_by_subject(store, subject_id)
        return {
            "version": VERSION,
            "tester_id": participant.get("tester_id") if participant else None,
            "subject": store.get_subject(subject_id),
        }
