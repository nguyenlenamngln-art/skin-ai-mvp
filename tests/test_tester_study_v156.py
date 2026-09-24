from pathlib import Path

from skin_ai.study_mode_v156 import (
    STUDY_MODE_VERSION,
    build_study_manifest,
    clean_study_id,
    study_manifest_record,
    study_profile_name,
)

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
SCRIPT = ROOT / "web" / "tester_study_v156.js"
STYLE = ROOT / "web" / "tester_study_v156.css"
SW = ROOT / "web" / "sw.js"


def _scan(scan_id: str, tester: str, session_id: str, created_at: str):
    return {
        "id": scan_id,
        "created_at": created_at,
        "modality": "rgb",
        "media_dir": f"/tmp/{scan_id}",
        "metrics": {
            "tracking_subject_name": study_profile_name(tester),
            "tracking_series_key": f"series-{tester}",
            "scan_session_id": session_id,
            "rgb_engine_version": "1.5.2",
            "capture_protocol_version": "1.4",
            "capture_quality": "good",
            "longitudinal_eligible": True,
        },
    }


def test_v156_study_id_is_pseudonymous_and_strict():
    assert STUDY_MODE_VERSION == "1.5.6"
    assert clean_study_id("P001") == "P001"
    assert study_profile_name("P001") == "STUDY-P001"
    for bad in ("", "A", "first last", "person@example.com", "P/001"):
        try:
            clean_study_id(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid study id: {bad!r}")


def test_v156_manifest_reuses_tracking_subject_and_guided_session_ids():
    scan = _scan("cap01", "P001", "sess01", "2026-09-23T00:00:00+00:00")
    row = study_manifest_record(scan)
    assert row is not None
    assert row["participant_id"] == "P001"
    assert row["session_id"] == "sess01"
    assert row["capture_id"] == "cap01"
    assert row["path"].endswith("cap01/original.jpg")
    assert row["rgb_engine_version"] == "1.5.2"


def test_v156_manifest_counts_participants_sessions_and_captures():
    scans = [
        _scan("a", "P001", "S01", "2026-09-23T00:00:00+00:00"),
        _scan("b", "P001", "S02", "2026-09-24T00:00:00+00:00"),
        _scan("c", "P002", "S03", "2026-09-24T01:00:00+00:00"),
    ]
    report = build_study_manifest(scans)
    assert report["capture_count"] == 3
    assert report["participant_count"] == 2
    assert report["session_count"] == 3
    assert [x["capture_id"] for x in report["captures"]] == ["a", "b", "c"]


def test_v156_ui_historical_asset_still_contains_notice_and_guided_session_logic():
    js = SCRIPT.read_text(encoding="utf-8")
    for text in (
        "TESTER STUDY MODE",
        "Study notice",
        "not a medical or diagnostic assessment",
        "full_face",
        "startGuidedSession",
        "scanMode='rgb'",
    ):
        assert text in js
    assert "name, email address, phone number" in js
    assert "formal research consent" in js


def test_v156_assets_remain_available_while_later_releases_supersede_live_ui():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "/app/tester_study_v156.css?v=156" in html
    assert "/app/tester_study_v157.js?v=157" in html
    assert "/app/tester_study_v156.js?v=156" not in html
    assert "const CACHE='skin-ai-beta-v" in sw
    assert "/app/tester_study_v156.css?v=156" in sw
    assert "/app/tester_study_v157.js?v=157" in sw


def test_v156_historical_ui_keeps_engine_and_capture_protocol_frozen():
    js = SCRIPT.read_text(encoding="utf-8")
    assert "Measurement remains RGB engine V1.5.2 / Capture Protocol V1.4" in js


def test_v156_has_mobile_layout():
    css = STYLE.read_text(encoding="utf-8")
    assert ".studyModeV156" in css
    assert ".studyNotice" in css
    assert "@media(max-width:650px)" in css
