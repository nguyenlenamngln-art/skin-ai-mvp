from pathlib import Path

from skin_ai.session_plan import SESSION_VERSION, next_region, session_plan, session_progress
from skin_ai.store import ProductStore


def test_uv_session_plan_is_ordered_five_region_workflow():
    assert session_plan("uv") == ["forehead", "left_cheek", "right_cheek", "nose", "chin"]
    assert next_region(session_plan("uv"), ["forehead", "left_cheek"]) == "right_cheek"
    progress = session_progress(session_plan("uv"), ["forehead", "left_cheek"])
    assert progress["completed_count"] == 2
    assert progress["total_count"] == 5
    assert progress["complete"] is False


def test_rgb_session_is_one_full_face_capture():
    assert session_plan("rgb") == ["full_face"]
    assert session_progress(session_plan("rgb"), ["full_face"])["complete"] is True


def test_store_session_advances_and_completes(tmp_path: Path):
    store = ProductStore(tmp_path / "product.db")
    subject = store.create_subject(subject_id="subject1", display_name="Test user", created_at="2026-09-21T00:00:00+00:00")
    session = store.create_session(
        session_id="session1",
        created_at="2026-09-21T00:00:00+00:00",
        subject_id=subject["id"],
        modality="rgb",
        plan=session_plan("rgb"),
        session_version=SESSION_VERSION,
    )
    assert session["status"] == "in_progress"
    store.add_scan(
        scan_id="scan1",
        created_at="2026-09-21T00:01:00+00:00",
        modality="rgb",
        source_name="face.jpg",
        metrics={"tracking_region_code": "full_face", "scan_session_id": "session1"},
        media_dir="unused",
    )
    session = store.add_session_scan(
        session_id="session1",
        region_code="full_face",
        scan_id="scan1",
        position=0,
        created_at="2026-09-21T00:01:00+00:00",
    )
    assert session["status"] == "complete"
    assert session["completed_at"] is not None
    assert len(session["items"]) == 1
    assert session["items"][0]["scan_id"] == "scan1"
