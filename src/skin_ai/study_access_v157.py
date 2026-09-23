from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import statistics
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

VERSION = "1.5.7"
RESEARCHER_COOKIE = "skin_ai_researcher_v157"
STUDY_COOKIE = "skin_ai_study_v157"
STUDY_PREFIX = "STUDY-"
COOKIE_TTL_SECONDS = 60 * 60 * 24 * 30
TESTER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$")

_current_researcher: ContextVar[bool] = ContextVar("study_researcher", default=False)
_current_study_subject: ContextVar[str | None] = ContextVar("study_subject", default=None)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_tester_id(value: str | None) -> str:
    text = str(value or "").strip()
    if not TESTER_ID_RE.fullmatch(text):
        raise ValueError("Tester ID must be 2–32 characters using letters, numbers, '-' or '_'.")
    return text


def access_hash(code: str) -> str:
    text = str(code or "").strip()
    if len(text) < 8:
        raise ValueError("Access code must be at least 8 characters.")
    return hashlib.sha256(f"skin-ai-study-v157|{text}".encode("utf-8")).hexdigest()


def new_access_code() -> str:
    return secrets.token_urlsafe(9)


def _b64e(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")


def _b64d(text: str) -> str:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("ascii")).decode("utf-8")


def sign_session(role: str, subject_id: str, secret: str, marker: str = "", ttl: int = COOKIE_TTL_SECONDS) -> str:
    exp = int(time.time()) + int(ttl)
    payload = f"{role}|{subject_id}|{marker}|{exp}"
    sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{_b64e(payload)}.{sig}"


def verify_session(token: str | None, role: str, secret: str) -> tuple[str, str] | None:
    if not token or "." not in token or not secret:
        return None
    body, sig = token.rsplit(".", 1)
    try:
        payload = _b64d(body)
        expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        got_role, subject_id, marker, exp_text = payload.split("|", 3)
        if got_role != role or int(exp_text) < int(time.time()):
            return None
        return subject_id, marker
    except Exception:
        return None


def is_study_name(name: str | None) -> bool:
    return str(name or "").startswith(STUDY_PREFIX)


def tester_id_from_name(name: str | None) -> str | None:
    text = str(name or "")
    if not text.startswith(STUDY_PREFIX):
        return None
    try:
        return clean_tester_id(text[len(STUDY_PREFIX):])
    except ValueError:
        return None


def is_study_scan(scan: dict[str, Any] | None) -> bool:
    if not scan:
        return False
    metrics = scan.get("metrics") or {}
    return bool(tester_id_from_name(metrics.get("tracking_subject_name")))


def _study_subject_id_from_scan(scan: dict[str, Any] | None) -> str | None:
    if not is_study_scan(scan):
        return None
    return str((scan.get("metrics") or {}).get("tracking_subject_id") or "") or None


def _init_table(store) -> None:
    with store.connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS study_participants (
                tester_id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL UNIQUE,
                access_hash TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_study_participant_subject ON study_participants(subject_id)")


def _participant_row(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "tester_id": row["tester_id"],
        "subject_id": row["subject_id"],
        "has_access_code": bool(row["access_hash"]),
        "active": bool(row["active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "_access_hash": row["access_hash"],
    }


def _get_participant(store, tester_id: str) -> dict[str, Any] | None:
    with store.connect() as con:
        row = con.execute("SELECT * FROM study_participants WHERE tester_id=?", (tester_id,)).fetchone()
    return _participant_row(row)


def _get_participant_by_subject(store, subject_id: str | None) -> dict[str, Any] | None:
    if not subject_id:
        return None
    with store.connect() as con:
        row = con.execute("SELECT * FROM study_participants WHERE subject_id=?", (subject_id,)).fetchone()
    return _participant_row(row)


def _list_participants(store) -> list[dict[str, Any]]:
    with store.connect() as con:
        rows = con.execute("SELECT * FROM study_participants ORDER BY tester_id").fetchall()
    return [_participant_row(row) for row in rows]


def _upsert_legacy_participants(store) -> None:
    _init_table(store)
    for subject in store.list_subjects():
        tester_id = tester_id_from_name(subject.get("display_name"))
        if not tester_id:
            continue
        now = _now_iso()
        with store.connect() as con:
            con.execute(
                """
                INSERT INTO study_participants(tester_id,subject_id,access_hash,active,created_at,updated_at)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(tester_id) DO NOTHING
                """,
                (tester_id, subject["id"], None, 1, subject.get("created_at") or now, now),
            )


def _save_participant(store, tester_id: str, subject_id: str, hashed: str | None, *, active: bool = True) -> dict[str, Any]:
    now = _now_iso()
    with store.connect() as con:
        con.execute(
            """
            INSERT INTO study_participants(tester_id,subject_id,access_hash,active,created_at,updated_at)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(tester_id) DO UPDATE SET
              subject_id=excluded.subject_id,
              access_hash=excluded.access_hash,
              active=excluded.active,
              updated_at=excluded.updated_at
            """,
            (tester_id, subject_id, hashed, int(active), now, now),
        )
    return _get_participant(store, tester_id)


def _next_tester_id(store) -> str:
    used = {row["tester_id"] for row in _list_participants(store)}
    n = 1
    while True:
        candidate = f"P{n:03d}"
        if candidate not in used:
            return candidate
        n += 1


def _subject_is_study(store, subject: dict[str, Any] | None) -> bool:
    if not subject:
        return False
    return bool(_get_participant_by_subject(store, subject.get("id")) or is_study_name(subject.get("display_name")))


def _researcher_secret() -> str:
    return os.environ.get("SKIN_AI_RESEARCHER_KEY", "").strip()


def _secure_cookie() -> bool:
    value = os.environ.get("SKIN_AI_COOKIE_SECURE", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _researcher_authorized(request: Request) -> bool:
    secret = _researcher_secret()
    if not secret:
        return False
    header = request.headers.get("x-researcher-key")
    if header and hmac.compare_digest(header, secret):
        return True
    token = request.cookies.get(RESEARCHER_COOKIE)
    return verify_session(token, "researcher", secret) is not None


def _study_subject_from_request(request: Request, store) -> str | None:
    secret = _researcher_secret()
    if not secret:
        return None
    parsed = verify_session(request.cookies.get(STUDY_COOKIE), "study", secret)
    if not parsed:
        return None
    subject_id, marker = parsed
    participant = _get_participant_by_subject(store, subject_id)
    if not participant or not participant["active"] or not participant["_access_hash"]:
        return None
    if marker != participant["_access_hash"][:16]:
        return None
    return subject_id


def _authorize_subject(subject_id: str | None) -> bool:
    if _current_researcher.get():
        return True
    return bool(subject_id and _current_study_subject.get() == subject_id)


def _json_error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": {"code": code, "message": message}})


def _public_media(scan: dict[str, Any]) -> dict[str, str]:
    sid = scan["id"]
    if scan.get("modality") == "rgb":
        return {
            "original": f"/media/{sid}/original.jpg",
            "skin_region": f"/media/{sid}/skin_region.png",
            "overlay": f"/media/{sid}/rgb_overlay.png",
            "redness_map": f"/media/{sid}/redness_map.png",
            "pigmentation_map": f"/media/{sid}/pigmentation_map.png",
        }
    return {"original": f"/media/{sid}/original.jpg", "overlay": f"/media/{sid}/overlay.png"}


def _study_scans(store, tester_id: str | None = None) -> list[dict[str, Any]]:
    rows = []
    for scan in store.list_scans(limit=100000, modality="rgb"):
        metrics = scan.get("metrics") or {}
        tid = tester_id_from_name(metrics.get("tracking_subject_name"))
        if not tid:
            continue
        if tester_id and tid != tester_id:
            continue
        rows.append(scan)
    return rows


def _safe_cv(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = statistics.fmean(values)
    if abs(mean) < 1e-12:
        return None
    return statistics.pstdev(values) / abs(mean)


def _participant_summary(store, participant: dict[str, Any]) -> dict[str, Any]:
    tester_id = participant["tester_id"]
    scans = _study_scans(store, tester_id)
    session_ids = {str((s.get("metrics") or {}).get("scan_session_id")) for s in scans if (s.get("metrics") or {}).get("scan_session_id")}
    eligible = [s for s in scans if (s.get("metrics") or {}).get("longitudinal_eligible") is True]
    quality_scores = [float((s.get("metrics") or {}).get("capture_quality_score")) for s in scans if isinstance((s.get("metrics") or {}).get("capture_quality_score"), (int, float))]
    redness = [float((s.get("metrics") or {}).get("redness_area_fraction")) for s in eligible if isinstance((s.get("metrics") or {}).get("redness_area_fraction"), (int, float))]
    pigmentation = [float((s.get("metrics") or {}).get("pigmentation_area_fraction")) for s in eligible if isinstance((s.get("metrics") or {}).get("pigmentation_area_fraction"), (int, float))]
    latest = scans[0] if scans else None
    lm = (latest or {}).get("metrics") or {}
    redness_cv = _safe_cv(redness)
    pigmentation_cv = _safe_cv(pigmentation)
    return {
        "tester_id": tester_id,
        "subject_id": participant["subject_id"],
        "active": participant["active"],
        "has_access_code": participant["has_access_code"],
        "capture_count": len(scans),
        "session_count": len(session_ids),
        "eligible_capture_count": len(eligible),
        "latest_at": latest.get("created_at") if latest else None,
        "mean_capture_quality_score": round(statistics.fmean(quality_scores), 1) if quality_scores else None,
        "redness_cv": round(redness_cv, 4) if redness_cv is not None else None,
        "pigmentation_cv": round(pigmentation_cv, 4) if pigmentation_cv is not None else None,
        "latest_redness_area_fraction": lm.get("redness_area_fraction"),
        "latest_pigmentation_area_fraction": lm.get("pigmentation_area_fraction"),
        "latest_capture_quality": lm.get("capture_quality"),
    }


def _study_summary(store) -> dict[str, Any]:
    participants = [_participant_summary(store, p) for p in _list_participants(store)]
    all_scans = _study_scans(store)
    sessions = {(tester_id_from_name((s.get("metrics") or {}).get("tracking_subject_name")), (s.get("metrics") or {}).get("scan_session_id")) for s in all_scans if (s.get("metrics") or {}).get("scan_session_id")}
    eligible = sum((s.get("metrics") or {}).get("longitudinal_eligible") is True for s in all_scans)
    return {"version": VERSION, "participant_count": len(participants), "session_count": len(sessions), "capture_count": len(all_scans), "eligible_capture_count": eligible, "participants": participants}


def _participant_detail(store, tester_id: str) -> dict[str, Any] | None:
    participant = _get_participant(store, tester_id)
    if not participant:
        return None
    summary = _participant_summary(store, participant)
    scans_out = []
    for scan in _study_scans(store, tester_id):
        m = scan.get("metrics") or {}
        scans_out.append({
            "scan_id": scan["id"],
            "created_at": scan.get("created_at"),
            "session_id": m.get("scan_session_id"),
            "capture_quality": m.get("capture_quality"),
            "capture_quality_score": m.get("capture_quality_score"),
            "longitudinal_eligible": m.get("longitudinal_eligible"),
            "redness_area_fraction": m.get("redness_area_fraction"),
            "pigmentation_area_fraction": m.get("pigmentation_area_fraction"),
            "texture_index_proxy": m.get("texture_index_proxy"),
            "measurement_confidence_score": m.get("measurement_confidence_score"),
            "anatomical_outer_boundary_score": m.get("anatomical_outer_boundary_score"),
            "anatomical_skin_support_fraction": m.get("anatomical_skin_support_fraction"),
            "rgb_engine_version": m.get("rgb_engine_version"),
            "capture_protocol_version": m.get("capture_protocol_version"),
            "media": _public_media(scan),
        })
    return {**summary, "scans": scans_out}


def _manifest(store) -> dict[str, Any]:
    from skin_ai.study_mode_v156 import build_study_manifest
    return build_study_manifest(_study_scans(store))


def _researcher_login_response(key: str) -> JSONResponse:
    secret = _researcher_secret()
    if not secret:
        return _json_error(503, "researcher_access_not_configured", "Researcher access is not configured on this deployment.")
    if not hmac.compare_digest(str(key or ""), secret):
        return _json_error(401, "researcher_auth_failed", "Researcher key is incorrect.")
    token = sign_session("researcher", "admin", secret)
    response = JSONResponse({"ok": True, "version": VERSION})
    response.set_cookie(RESEARCHER_COOKIE, token, max_age=COOKIE_TTL_SECONDS, httponly=True, secure=_secure_cookie(), samesite="strict", path="/")
    return response


def _study_login_response(store, tester_id: str, code: str) -> JSONResponse:
    try:
        tid = clean_tester_id(tester_id)
        hashed = access_hash(code)
    except ValueError as exc:
        return _json_error(422, "study_access_invalid", str(exc))
    participant = _get_participant(store, tid)
    if not participant or not participant["active"] or not participant["_access_hash"]:
        return _json_error(401, "study_access_failed", "Tester code or access code is incorrect.")
    if not hmac.compare_digest(hashed, participant["_access_hash"]):
        return _json_error(401, "study_access_failed", "Tester code or access code is incorrect.")
    secret = _researcher_secret()
    if not secret:
        return _json_error(503, "researcher_access_not_configured", "Study access is not configured on this deployment.")
    token = sign_session("study", participant["subject_id"], secret, participant["_access_hash"][:16])
    subject = store.get_subject(participant["subject_id"])
    response = JSONResponse({"ok": True, "version": VERSION, "tester_id": tid, "subject": subject})
    response.set_cookie(STUDY_COOKIE, token, max_age=COOKIE_TTL_SECONDS, httponly=True, secure=_secure_cookie(), samesite="strict", path="/")
    return response


def install_v157(product_api) -> None:
    store = product_api.store
    app = product_api.app
    _upsert_legacy_participants(store)

    original_resolve_tracking = product_api.resolve_tracking

    def resolve_tracking_v157(subject_id, region_code, modality):
        subject, region = original_resolve_tracking(subject_id, region_code, modality)
        if _subject_is_study(store, subject) and not _authorize_subject(subject.get("id")):
            raise product_api.HTTPException(status_code=401, detail={"code": "study_access_required", "message": "This study profile requires tester or researcher access."})
        return subject, region

    product_api.resolve_tracking = resolve_tracking_v157

    @app.middleware("http")
    async def study_access_middleware(request: Request, call_next):
        researcher = _researcher_authorized(request)
        study_subject = _study_subject_from_request(request, store)
        researcher_token = _current_researcher.set(researcher)
        study_token = _current_study_subject.set(study_subject)
        try:
            path = request.url.path
            method = request.method.upper()

            if path == "/v1/researcher/login" and method == "POST":
                payload = await request.json()
                return _researcher_login_response(payload.get("key", ""))
            if path == "/v1/researcher/logout" and method == "POST":
                response = JSONResponse({"ok": True})
                response.delete_cookie(RESEARCHER_COOKIE, path="/")
                return response
            if path.startswith("/v1/researcher/"):
                if not researcher:
                    return _json_error(401, "researcher_access_required", "Researcher access is required.")
                if path == "/v1/researcher/study/summary" and method == "GET":
                    return JSONResponse(_study_summary(store))
                if path == "/v1/researcher/study/manifest" and method == "GET":
                    return JSONResponse(_manifest(store))
                if path == "/v1/researcher/study/participants" and method == "GET":
                    return JSONResponse([_participant_summary(store, p) for p in _list_participants(store)])
                if path == "/v1/researcher/study/participants" and method == "POST":
                    payload = await request.json()
                    raw_id = str(payload.get("tester_id") or "").strip()
                    try:
                        tid = clean_tester_id(raw_id) if raw_id else _next_tester_id(store)
                    except ValueError as exc:
                        return _json_error(422, "tester_id_invalid", str(exc))
                    if _get_participant(store, tid):
                        return _json_error(409, "tester_exists", "That tester ID already exists.")
                    subject = store.create_subject(subject_id=uuid.uuid4().hex[:12], display_name=f"{STUDY_PREFIX}{tid}", created_at=_now_iso())
                    code = new_access_code()
                    participant = _save_participant(store, tid, subject["id"], access_hash(code))
                    return JSONResponse(status_code=201, content={"tester_id": tid, "subject_id": participant["subject_id"], "access_code": code, "message": "Share the tester ID and access code privately. The access code is shown only in this response."})
                match = re.fullmatch(r"/v1/researcher/study/participants/([^/]+)/rotate-access", path)
                if match and method == "POST":
                    try:
                        tid = clean_tester_id(match.group(1))
                    except ValueError as exc:
                        return _json_error(422, "tester_id_invalid", str(exc))
                    participant = _get_participant(store, tid)
                    if not participant:
                        return _json_error(404, "tester_not_found", "Tester was not found.")
                    code = new_access_code()
                    _save_participant(store, tid, participant["subject_id"], access_hash(code), active=participant["active"])
                    return JSONResponse({"tester_id": tid, "access_code": code, "message": "Previous tester sessions are revoked when their cookie is checked again."})
                match = re.fullmatch(r"/v1/researcher/study/participants/([^/]+)", path)
                if match and method == "GET":
                    try:
                        tid = clean_tester_id(match.group(1))
                    except ValueError as exc:
                        return _json_error(422, "tester_id_invalid", str(exc))
                    detail = _participant_detail(store, tid)
                    if not detail:
                        return _json_error(404, "tester_not_found", "Tester was not found.")
                    return JSONResponse(detail)
                return _json_error(404, "researcher_route_not_found", "Researcher route not found.")

            if path == "/v1/study/login" and method == "POST":
                payload = await request.json()
                return _study_login_response(store, payload.get("tester_id", ""), payload.get("access_code", ""))
            if path == "/v1/study/logout" and method == "POST":
                response = JSONResponse({"ok": True})
                response.delete_cookie(STUDY_COOKIE, path="/")
                return response
            if path == "/v1/study/status" and method == "GET":
                if not study_subject:
                    return JSONResponse({"authenticated": False, "version": VERSION})
                participant = _get_participant_by_subject(store, study_subject)
                return JSONResponse({"authenticated": True, "version": VERSION, "tester_id": participant["tester_id"] if participant else None, "subject": store.get_subject(study_subject)})

            if path == "/v1/subjects" and method == "GET":
                return JSONResponse([s for s in store.list_subjects() if not _subject_is_study(store, s)])
            if path == "/v1/scans" and method == "GET":
                try:
                    limit = min(max(int(request.query_params.get("limit", "30")), 1), 100)
                except ValueError:
                    limit = 30
                modality = request.query_params.get("modality")
                rows = [s for s in store.list_scans(limit=1000, modality=modality) if not is_study_scan(s)]
                return JSONResponse([product_api.public_scan(s) for s in rows[:limit]])
            if path == "/v1/sessions" and method == "GET":
                try:
                    limit = min(max(int(request.query_params.get("limit", "30")), 1), 100)
                except ValueError:
                    limit = 30
                rows = []
                for session in store.list_sessions(limit=1000):
                    subject = store.get_subject(session.get("subject_id"))
                    if _subject_is_study(store, subject):
                        continue
                    rows.append(product_api.public_session(session))
                    if len(rows) >= limit:
                        break
                return JSONResponse(rows)
            if path == "/v1/trends" and method == "GET":
                try:
                    limit = min(max(int(request.query_params.get("limit", "90")), 1), 365)
                except ValueError:
                    limit = 90
                modality = request.query_params.get("modality")
                rows = [row for row in store.trends(limit=1000, modality=modality) if not is_study_name(row.get("tracking_subject_name"))]
                return JSONResponse(rows[-limit:])

            scan_match = re.fullmatch(r"/v1/scans/([A-Za-z0-9_-]+)", path)
            if scan_match and method == "GET":
                scan = store.get_scan(scan_match.group(1))
                subject_id = _study_subject_id_from_scan(scan)
                if subject_id and not (researcher or subject_id == study_subject):
                    return _json_error(404, "scan_not_found", "Scan not found.")
            session_match = re.fullmatch(r"/v1/sessions/([A-Za-z0-9_-]+)", path)
            if session_match and method == "GET":
                session = store.get_session(session_match.group(1))
                subject = store.get_subject(session.get("subject_id")) if session else None
                if _subject_is_study(store, subject) and not (researcher or subject.get("id") == study_subject):
                    return _json_error(404, "session_not_found", "Session not found.")
            media_match = re.fullmatch(r"/media/([A-Za-z0-9_-]+)/[^/]+", path)
            if media_match and method == "GET":
                scan = store.get_scan(media_match.group(1))
                subject_id = _study_subject_id_from_scan(scan)
                if subject_id and not (researcher or subject_id == study_subject):
                    return _json_error(404, "media_not_found", "Media not found.")

            if path == "/v1/sessions" and method == "POST":
                try:
                    payload = await request.json()
                except Exception:
                    payload = {}
                subject = store.get_subject(payload.get("subject_id")) if payload.get("subject_id") else None
                if _subject_is_study(store, subject) and not (researcher or subject.get("id") == study_subject):
                    return _json_error(401, "study_access_required", "Tester access is required for this study profile.")

            return await call_next(request)
        finally:
            _current_researcher.reset(researcher_token)
            _current_study_subject.reset(study_token)
