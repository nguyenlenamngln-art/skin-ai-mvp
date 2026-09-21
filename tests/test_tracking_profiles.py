from skin_ai.store import ProductStore
from skin_ai.tracking import get_region, stamp_tracking_metadata, tracking_series_key


def test_structured_regions_are_modality_aware():
    assert get_region("left_cheek", "rgb")["label"] == "Left cheek"
    assert get_region("left_cheek", "uv")["label"] == "Left cheek"
    assert get_region("full_face", "rgb")["label"] == "Full face"
    assert get_region("full_face", "uv") is None


def test_tracking_series_key_changes_by_subject_or_region():
    a = tracking_series_key("subject-a", "left_cheek")
    b = tracking_series_key("subject-b", "left_cheek")
    c = tracking_series_key("subject-a", "right_cheek")
    assert a
    assert len({a, b, c}) == 3


def test_stamp_tracking_metadata_uses_structured_identity():
    metrics = {}
    stamp_tracking_metadata(
        metrics,
        subject={"id": "s1", "display_name": "Test User"},
        region={"code": "left_cheek", "label": "Left cheek"},
    )
    assert metrics["tracking_subject_id"] == "s1"
    assert metrics["tracking_subject_name"] == "Test User"
    assert metrics["tracking_region_code"] == "left_cheek"
    assert metrics["tracking_region_label"] == "Left cheek"
    assert metrics["tracking_series_key"]


def test_subject_profiles_are_persistent_and_duplicate_safe(tmp_path):
    store = ProductStore(tmp_path / "skin.db")
    first = store.create_subject(subject_id="s1", display_name="Test User", created_at="2026-09-21T00:00:00+00:00")
    again = store.create_subject(subject_id="s2", display_name="test user", created_at="2026-09-21T00:01:00+00:00")
    assert first["id"] == "s1"
    assert again["id"] == "s1"
    assert len(store.list_subjects()) == 1


def test_trends_exclude_unassigned_rgb_and_keep_structured_series(tmp_path):
    store = ProductStore(tmp_path / "skin.db")
    base = {
        "rgb_engine_version": "1.1",
        "capture_quality": "good",
        "longitudinal_eligible": True,
        "redness_area_fraction": 0.01,
        "pigmentation_area_fraction": 0.02,
    }
    store.add_scan(
        scan_id="legacy",
        created_at="2026-09-21T00:00:00+00:00",
        modality="rgb",
        source_name="legacy.jpg",
        metrics=dict(base),
        media_dir=None,
    )
    structured = dict(base)
    structured.update(
        {
            "tracking_subject_id": "s1",
            "tracking_subject_name": "Test User",
            "tracking_region_code": "full_face",
            "tracking_region_label": "Full face",
            "tracking_series_key": tracking_series_key("s1", "full_face"),
        }
    )
    store.add_scan(
        scan_id="structured",
        created_at="2026-09-21T00:01:00+00:00",
        modality="rgb",
        source_name="structured.jpg",
        metrics=structured,
        media_dir=None,
    )
    rows = store.trends(modality="rgb")
    assert [x["scan_id"] for x in rows] == ["structured"]
    assert rows[0]["tracking_subject_id"] == "s1"
    assert rows[0]["tracking_region_code"] == "full_face"
