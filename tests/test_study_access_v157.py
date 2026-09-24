from pathlib import Path

from skin_ai.store import ProductStore
from skin_ai.study_access_v157 import (
    VERSION,
    _participant_detail,
    _save_participant,
    _study_summary,
    _upsert_legacy_participants,
    access_hash,
    clean_tester_id,
    is_study_scan,
    sign_session,
    tester_id_from_name as study_tester_id_from_name,
    verify_session,
)

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
TESTER_JS = ROOT / "web" / "tester_study_v157.js"
RESEARCHER_HTML = ROOT / "web" / "researcher.html"
RESEARCHER_JS = ROOT / "web" / "researcher_v157.js"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"
ACCESS = ROOT / "src" / "skin_ai" / "study_access_v157.py"


def test_v157_version_and_signed_sessions_reject_tampering():
    assert VERSION == "1.5.7"
    secret = "researcher-key-for-tests"
    token = sign_session("study", "subject-1", secret, "marker", ttl=120)
    assert verify_session(token, "study", secret) == ("subject-1", "marker")
    assert verify_session(token + "x", "study", secret) is None
    assert verify_session(token, "researcher", secret) is None


def test_v157_hashes_tester_access_codes():
    raw = "Private-Code-123"
    hashed = access_hash(raw)
    assert raw not in hashed
    assert len(hashed) == 64
    assert hashed == access_hash(raw)


def test_v157_study_identity_and_summary(tmp_path):
    store = ProductStore(tmp_path / "study.db")
    subject = store.create_subject(subject_id="study-subject", display_name="STUDY-P001", created_at="2026-09-23T00:00:00+00:00")
    _upsert_legacy_participants(store)
    _save_participant(store, "P001", subject["id"], access_hash("Access-Code-001"))
    metrics = {
        "tracking_subject_id": subject["id"], "tracking_subject_name": "STUDY-P001",
        "tracking_region_code": "full_face", "tracking_region_label": "Full face",
        "tracking_series_key": "series-p001", "scan_session_id": "session-001",
        "rgb_engine_version": "1.5.2", "capture_protocol_version": "1.4",
        "capture_quality": "good", "capture_quality_score": 91.0,
        "longitudinal_eligible": True, "redness_area_fraction": 0.031,
        "pigmentation_area_fraction": 0.018, "texture_index_proxy": 0.012,
        "anatomical_skin_support_fraction": 0.94,
    }
    store.add_scan(scan_id="scan-001", created_at="2026-09-23T01:00:00+00:00", modality="rgb", source_name="capture.jpg", metrics=metrics, media_dir="/data/scans/scan-001")
    scan = store.get_scan("scan-001")
    assert study_tester_id_from_name("STUDY-P001") == "P001"
    assert is_study_scan(scan) is True
    summary = _study_summary(store)
    assert summary["participant_count"] == 1
    assert summary["session_count"] == 1
    assert summary["capture_count"] == 1
    assert summary["eligible_capture_count"] == 1
    detail = _participant_detail(store, "P001")
    assert detail["tester_id"] == "P001"
    assert detail["scans"][0]["rgb_engine_version"] == "1.5.2"


def test_v157_tester_id_rejects_personal_style_values():
    assert clean_tester_id("P001") == "P001"
    for value in ("a@b.com", "Jane Doe", "+84901234567", ""):
        try:
            clean_tester_id(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected {value!r} to be rejected")


def test_v157_public_filtering_and_researcher_routes_exist():
    source = ACCESS.read_text(encoding="utf-8")
    assert 'if path == "/v1/subjects" and method == "GET"' in source
    assert 'if path == "/v1/scans" and method == "GET"' in source
    assert 'if path == "/v1/sessions" and method == "GET"' in source
    assert 'if path == "/v1/trends" and method == "GET"' in source
    assert 'path.startswith("/v1/researcher/")' in source
    assert 'RESEARCHER_COOKIE' in source
    assert 'httponly=True' in source
    assert 'samesite="strict"' in source


def test_v157_tester_ui_requires_assigned_access_code():
    js = TESTER_JS.read_text(encoding="utf-8")
    assert "STUDY_MODE_VERSION='1.5.7'" in js
    assert "Access code" in js
    assert "/v1/study/login" in js
    assert "/v1/study/scans" in js
    assert "ensureStudySubject" not in js
    assert "provided by the study organizer" in js.lower()


def test_v157_researcher_dashboard_does_not_store_researcher_key():
    html = RESEARCHER_HTML.read_text(encoding="utf-8")
    js = RESEARCHER_JS.read_text(encoding="utf-8")
    assert "Researcher Dashboard" in html
    assert "/v1/researcher/login" in js
    assert "/v1/researcher/study/summary" in js
    assert "/v1/researcher/study/manifest" in js
    assert "localStorage" not in js
    assert "access_code" in js


def test_v157_assets_are_loaded_and_remain_cached_in_later_releases():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "/app/tester_study_v157.css?v=157" in html
    assert "/app/tester_study_v157.js?v=157" in html
    assert "tester_study_v156.js" not in html
    assert "const CACHE='skin-ai-beta-v" in sw
    assert "/researcher.html" in sw
    assert "/app/researcher_v157.js?v=157" in sw


def test_v157_keeps_measurement_and_capture_protocol_frozen():
    entry = ENTRY.read_text(encoding="utf-8")
    access = ACCESS.read_text(encoding="utf-8")
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
    assert "rgb_engine_v153" not in access
    assert "redness_threshold" not in access
    assert "pigmentation_threshold" not in access
