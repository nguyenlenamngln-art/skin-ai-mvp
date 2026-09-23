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

    @app.middleware("http")
    async def study_scoped_view_middleware(request: Request, call_next):
        path = request.url.path
        if not path.startswith("/v1/study/") or path in {"/v1/study/login", "/v1/study/logout", "/v1/study/status"}:
            return await call_next(request)

        subject_id = _study_subject_from_request(request, store)
        if not subject_id:
            return unauthorized()

        if path == "/v1/study/subjects" and request.method == "GET":
            subject = store.get_subject(subject_id)
            return JSONResponse([subject] if subject else [])

        if path == "/v1/study/scans" and request.method == "GET":
            try:
                limit = min(max(int(request.query_params.get("limit", "100")), 1), 100)
            except ValueError:
                limit = 100
            modality = request.query_params.get("modality")
            rows = []
            for scan in store.list_scans(limit=1000, modality=modality):
                metrics = scan.get("metrics") or {}
                if not is_study_scan(scan) or metrics.get("tracking_subject_id") != subject_id:
                    continue
                rows.append(product_api.public_scan(scan))
                if len(rows) >= limit:
                    break
            return JSONResponse(rows)

        if path == "/v1/study/trends" and request.method == "GET":
            try:
                limit = min(max(int(request.query_params.get("limit", "180")), 1), 365)
            except ValueError:
                limit = 180
            modality = request.query_params.get("modality")
            rows = [
                row
                for row in store.trends(limit=1000, modality=modality)
                if row.get("tracking_subject_id") == subject_id
            ]
            return JSONResponse(rows[-limit:])

        if path == "/v1/study/sessions" and request.method == "GET":
            try:
                limit = min(max(int(request.query_params.get("limit", "100")), 1), 100)
            except ValueError:
                limit = 100
            rows = []
            for session in store.list_sessions(limit=1000):
                if session.get("subject_id") != subject_id:
                    continue
                rows.append(product_api.public_session(session))
                if len(rows) >= limit:
                    break
            return JSONResponse(rows)

        if path == "/v1/study/profile" and request.method == "GET":
            participant = _get_participant_by_subject(store, subject_id)
            return JSONResponse({
                "version": VERSION,
                "tester_id": participant.get("tester_id") if participant else None,
                "subject": store.get_subject(subject_id),
            })

        return await call_next(request)
