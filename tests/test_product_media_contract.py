from skin_ai.product_api import public_scan


def test_public_scan_exposes_all_uv_analysis_media():
    scan = {
        "id": "abc123",
        "created_at": "2026-09-18T00:00:00+00:00",
        "modality": "uv",
        "source_name": "sample.png",
        "metrics": {},
        "media_dir": "unused",
    }

    out = public_scan(scan)

    assert out["media"] == {
        "original": "/media/abc123/original.jpg",
        "overlay": "/media/abc123/overlay.png",
        "artifact_mask": "/media/abc123/artifact_mask.png",
        "porphyrin_mask": "/media/abc123/porphyrin_mask.png",
        "dark_mask": "/media/abc123/dark_artifact_mask.png",
        "light_mask": "/media/abc123/light_artifact_mask.png",
    }


def test_public_scan_exposes_rgb_v11_skin_region_media():
    scan = {
        "id": "rgb123",
        "created_at": "2026-09-21T00:00:00+00:00",
        "modality": "rgb",
        "source_name": "face.jpg",
        "metrics": {},
        "media_dir": "unused",
    }

    out = public_scan(scan)

    assert out["media"] == {
        "original": "/media/rgb123/original.jpg",
        "skin_region": "/media/rgb123/skin_region.png",
        "overlay": "/media/rgb123/rgb_overlay.png",
        "redness_map": "/media/rgb123/redness_map.png",
        "pigmentation_map": "/media/rgb123/pigmentation_map.png",
    }
