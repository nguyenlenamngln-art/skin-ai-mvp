from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BURST = ROOT / "web" / "dermatoscope_burst_v1781.js"
TRANSITION = ROOT / "web" / "dermatoscope_transition_v1700.js"


def test_v1783_removes_spoken_guidance_and_keeps_audio_feedback():
    js = BURST.read_text(encoding="utf-8")
    assert "const VERSION='1.7.8.3'" in js
    assert "spokenGuidance:false" in js
    assert "speechSynthesis.cancel" in js
    assert "dermAudioOption" in js
    assert "frameCue" in js
    assert "positionCue" in js
    assert "completeCue" in js
    assert "audio_cues:true" in js


def test_v1783_uses_existing_quality_gate_as_contact_proxy():
    js = BURST.read_text(encoding="utf-8")
    assert "contact_inference:'image_quality_gate_proxy'" in js
    assert "Device contact detected" in js
    assert "Đã nhận diện tiếp xúc da" in js


def test_v1783_transition_cache_busts_nonverbal_burst_asset():
    transition = TRANSITION.read_text(encoding="utf-8")
    assert "/app/dermatoscope_burst_v1781.js?v=1783" in transition
    assert "V1.7.8.3 non-verbal capture cues" in transition
