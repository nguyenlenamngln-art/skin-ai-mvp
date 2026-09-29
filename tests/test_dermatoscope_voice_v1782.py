from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOICE = ROOT / "web" / "dermatoscope_guided_capture_v1712.js"
TRANSITION = ROOT / "web" / "dermatoscope_transition_v1700.js"


def test_vietnamese_voice_is_selected_explicitly():
    js = VOICE.read_text(encoding="utf-8")
    assert "preferredVoice" in js
    assert "speechVoices" in js
    assert "vi-VN" in js
    assert "u.voice=voice" in js
    assert "voiceschanged" in js


def test_vietnamese_guidance_uses_slower_rate_and_natural_short_copy():
    js = VOICE.read_text(encoding="utf-8")
    assert "u.rate=isVi?.88:.95" in js
    assert "Giữ yên nhé." in js
    assert "Đã chụp xong." in js
    assert "Đã quét xong vùng" in js


def test_transition_loads_new_voice_capture_without_global_observer():
    transition = TRANSITION.read_text(encoding="utf-8")
    assert "/app/dermatoscope_guided_capture_v1712.js?v=1712" in transition
    assert "MutationObserver" not in VOICE.read_text(encoding="utf-8")
