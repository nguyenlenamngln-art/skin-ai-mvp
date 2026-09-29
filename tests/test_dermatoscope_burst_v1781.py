from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BURST = ROOT / "web" / "dermatoscope_burst_v1781.js"
TRANSITION = ROOT / "web" / "dermatoscope_transition_v1700.js"
API = ROOT / "src" / "skin_ai" / "dermatoscope_capture_v171.py"


def test_v1781_burst_captures_three_frames_and_selects_best():
    js = BURST.read_text(encoding="utf-8")
    assert "const VERSION='1.7.8.1'" in js
    assert "const FRAME_COUNT=3" in js
    assert "const GAP_MS=170" in js
    assert "highest_quality_score" in js
    assert "selected_frame" in js
    assert "alignment_status" in js
    assert "fusion_used:false" in js
    assert "deferred_until_physical_device_validation" in js


def test_v1781_burst_preserves_stable_scan_architecture():
    js = BURST.read_text(encoding="utf-8")
    assert "MutationObserver" not in js
    assert "setInterval" not in js
    assert "window.fetch=async function" in js
    assert "'/v1/dermatoscope/captures'" in js
    assert "falling back to single frame" in js


def test_v1781_burst_is_loaded_after_guided_capture():
    transition = TRANSITION.read_text(encoding="utf-8")
    assert "/app/dermatoscope_burst_v1781.js?v=1781" in transition
    guided = transition.index("/app/dermatoscope_guided_capture_v171.js?v=1711")
    burst = transition.index("/app/dermatoscope_burst_v1781.js?v=1781")
    assert guided < burst


def test_v1781_backend_accepts_and_preserves_raw_frames():
    api = API.read_text(encoding="utf-8")
    assert 'VERSION = "1.7.8.1"' in api
    for name in ("burst_frame_1", "burst_frame_2", "burst_frame_3", "burst_metadata"):
        assert name in api
    assert 'out_dir / f"burst_{index}.jpg"' in api
    assert '"raw_frames_preserved"' in api
    assert '"validated_for_de500"] = False' in api
    assert '"burst": burst_media' in api


def test_v1781_canonical_image_remains_selected_frame_for_existing_analysis():
    api = API.read_text(encoding="utf-8")
    assert 'media_path = out_dir / "original.jpg"' in api
    assert 'rgb.save(media_path, quality=94)' in api
    assert '"original": f"/media/dermatoscope/{capture_id}/original.jpg"' in api
