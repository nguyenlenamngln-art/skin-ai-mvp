from pathlib import Path

from skin_ai.store import ProductStore
from skin_ai.uv_longitudinal import (
    UV_ANALYSIS_VERSION,
    build_comparison_key,
    build_series_id,
    stamp_uv_longitudinal_metadata,
    uv_scans_comparable,
)


def _stamp(subject="beta-01", site="left cheek"):
    m = {"porphyrin_component_count_proxy": 2}
    out = stamp_uv_longitudinal_metadata(
        m,
        subject_label=subject,
        anatomical_site=site,
        model_signature="model123",
        validator_version="1.0",
        validator_profile="uvfd-closeup-v1",
    )
    if subject and site:
        out["tracking_series_key"] = f"{subject.strip()}/{site.strip()}"
    return out


def test_missing_series_identity_is_analysis_only():
    m = _stamp(subject=None, site="left cheek")
    assert m["uv_longitudinal_eligible"] is False
    assert m["uv_comparison_series_id"] is None
    assert m["uv_comparison_key"] is None


def test_same_subject_site_and_pipeline_are_comparable():
    a = _stamp("beta-01", "left cheek")
    b = _stamp(" beta-01 ", "left   cheek")
    assert a["uv_analysis_version"] == UV_ANALYSIS_VERSION
    assert a["uv_comparison_key"] == b["uv_comparison_key"]
    assert uv_scans_comparable(a, b) is True


def test_different_anatomical_site_is_not_comparable():
    a = _stamp("beta-01", "left cheek")
    b = _stamp("beta-01", "right cheek")
    assert a["uv_comparison_key"] != b["uv_comparison_key"]
    assert uv_scans_comparable(a, b) is False


def test_pipeline_change_breaks_comparison_key():
    series_id = build_series_id("beta-01", "left cheek")
    a = build_comparison_key(
        series_id=series_id,
        analysis_version=UV_ANALYSIS_VERSION,
        model_signature="model123",
        validator_version="1.0",
        validator_profile="uvfd-closeup-v1",
    )
    b = build_comparison_key(
        series_id=series_id,
        analysis_version=UV_ANALYSIS_VERSION,
        model_signature="model456",
        validator_version="1.0",
        validator_profile="uvfd-closeup-v1",
    )
    assert a != b


def test_uv_trends_exclude_legacy_and_unlabeled_scans(tmp_path: Path):
    store = ProductStore(tmp_path / "skin.db")
    legacy = {
        "porphyrin_component_count_proxy": 85,
        "porphyrin_area_fraction_valid": 0.04,
        "porphyrin_red_intensity_proxy": 0.45,
        "artifact_area_fraction": 0.1,
    }
    unlabeled = _stamp(subject=None, site=None)
    unlabeled.update({
        "porphyrin_area_fraction_valid": 0.01,
        "porphyrin_red_intensity_proxy": 0.2,
        "artifact_area_fraction": 0.02,
    })
    eligible = _stamp()
    eligible.update({
        "porphyrin_area_fraction_valid": 0.02,
        "porphyrin_red_intensity_proxy": 0.3,
        "artifact_area_fraction": 0.03,
    })
    store.add_scan(scan_id="legacy", created_at="2026-01-01T00:00:00+00:00", modality="uv", source_name="old.png", metrics=legacy, media_dir=None)
    store.add_scan(scan_id="unlabeled", created_at="2026-01-02T00:00:00+00:00", modality="uv", source_name="sample.png", metrics=unlabeled, media_dir=None)
    store.add_scan(scan_id="eligible", created_at="2026-01-03T00:00:00+00:00", modality="uv", source_name="repeat.png", metrics=eligible, media_dir=None)

    rows = store.trends(modality="uv")
    assert [r["scan_id"] for r in rows] == ["eligible"]
    assert rows[0]["uv_comparison_key"] == eligible["uv_comparison_key"]
    assert rows[0]["uv_longitudinal_eligible"] is True
