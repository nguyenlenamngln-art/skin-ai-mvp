from pathlib import Path

import numpy as np

from skin_ai.rgb_repeatability_v154 import (
    CaptureRecord,
    ENGINE_UNDER_TEST,
    MIN_PARTICIPANTS,
    VALIDATION_VERSION,
    _coefficient_of_variation,
    summarize_cohort,
)


def _square(offset: int = 0) -> np.ndarray:
    mask = np.zeros((64, 64), dtype=bool)
    mask[16 + offset:48 + offset, 16:48] = True
    return mask


def test_v154_version_contract():
    assert VALIDATION_VERSION == "1.5.4"
    assert ENGINE_UNDER_TEST == "1.5.2"
    assert MIN_PARTICIPANTS == 3


def test_v154_coefficient_of_variation_zero_for_constant_values():
    assert _coefficient_of_variation([0.5, 0.5, 0.5]) == 0.0


def test_v154_small_cohort_is_reported_but_not_overclaimed():
    rows = []
    masks = {}
    for i, session in enumerate(("s1", "s1", "s2"), start=1):
        capture_id = f"p1-{i}"
        rows.append({
            "capture_id": capture_id,
            "participant_id": "p1",
            "session_id": session,
            "device_id": "iphone",
            "per_image_validation_pass": True,
            "baseline": {
                "canonical_mask_available": True,
                "face_detected": True,
                "canonical_outer_area_fraction": 0.25,
                "anatomical_mask_fallback": False,
                "anatomical_skin_support_fraction": 0.9,
            },
        })
        masks[capture_id] = _square(i % 2)

    report = summarize_cohort(rows, masks)
    assert report["validation_version"] == "1.5.4"
    assert report["cohort_pass"] is False
    assert "insufficient_participants" in report["failure_reasons"]
    assert report["participants"][0]["participant_pass"] is True


def test_v154_complete_three_participant_cohort_can_pass():
    rows = []
    masks = {}
    for p in range(3):
        participant_id = f"p{p+1}"
        for i, session in enumerate(("s1", "s1", "s2"), start=1):
            capture_id = f"{participant_id}-{i}"
            rows.append({
                "capture_id": capture_id,
                "participant_id": participant_id,
                "session_id": session,
                "device_id": "device-a" if p < 2 else "device-b",
                "per_image_validation_pass": True,
                "baseline": {
                    "canonical_mask_available": True,
                    "face_detected": True,
                    "canonical_outer_area_fraction": 0.25 + (0.002 * i),
                    "anatomical_mask_fallback": False,
                    "anatomical_skin_support_fraction": 0.9,
                },
            })
            masks[capture_id] = _square((i + p) % 2)

    report = summarize_cohort(rows, masks)
    assert report["cohort_pass"] is True
    assert report["summary"]["participant_count"] == 3
    assert report["summary"]["complete_participant_count"] == 3
    assert report["summary"]["participant_pass_rate"] == 1.0


def test_capture_record_supports_pseudonymous_metadata():
    record = CaptureRecord(
        path=Path("capture.jpg"),
        participant_id="P-001",
        session_id="S-001",
        capture_id="C-001",
        device_id="phone-a",
    )
    assert record.participant_id == "P-001"
    assert record.device_id == "phone-a"
