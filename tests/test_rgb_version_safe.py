from skin_ai.store import ProductStore


def test_rgb_trends_preserve_engine_version(tmp_path):
    store = ProductStore(tmp_path / "skin_ai.db")
    store.add_scan(
        scan_id="legacy",
        created_at="2026-09-21T00:00:00+00:00",
        modality="rgb",
        source_name="legacy.jpg",
        metrics={
            "redness_area_fraction": 0.01,
            "pigmentation_area_fraction": 0.02,
            "texture_index_proxy": 0.01,
            "red_spot_count_proxy": 4,
            "pigmented_spot_count_proxy": 10,
            "capture_quality": "good",
            "tracking_series_key": "subject-1/full-face",
        },
        media_dir="unused",
    )
    store.add_scan(
        scan_id="v11",
        created_at="2026-09-21T01:00:00+00:00",
        modality="rgb",
        source_name="v11.jpg",
        metrics={
            "rgb_engine_version": "1.1",
            "redness_area_fraction": 0.005,
            "pigmentation_area_fraction": 0.015,
            "texture_index_proxy": 0.011,
            "red_spot_count_proxy": 3,
            "pigmented_spot_count_proxy": 8,
            "capture_quality": "good",
            "tracking_series_key": "subject-1/full-face",
        },
        media_dir="unused",
    )

    rows = store.trends(modality="rgb")

    assert rows[0]["scan_id"] == "legacy"
    assert rows[0]["rgb_engine_version"] is None
    assert rows[1]["scan_id"] == "v11"
    assert rows[1]["rgb_engine_version"] == "1.1"
