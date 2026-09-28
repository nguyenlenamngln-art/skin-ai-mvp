from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "dermatoscope_live_guidance_v174.js"
CSS = ROOT / "web" / "dermatoscope_live_guidance_v174.css"
POLISH = ROOT / "web" / "dermatoscope_ui_polish_v1711.js"
SW = ROOT / "web" / "sw.js"


def test_v174_loads_exact_compatible_baseline_before_live_guidance():
    js = JS.read_text(encoding="utf-8")
    assert "const VERSION='1.7.4'" in js
    assert "/v1/dermatoscope/baseline" in js
    for token in (
        "region,subregion",
        "subject_key:'my_profile'",
        "illumination_mode:'polarized'",
        "brightness_level:'2'",
        "simulator:'true'",
    ):
        assert token in js


def test_v174_provides_bilingual_directional_position_guidance():
    js = JS.read_text(encoding="utf-8")
    pairs = (
        ("Move slightly left.", "Di chuyển nhẹ sang trái."),
        ("Move slightly right.", "Di chuyển nhẹ sang phải."),
        ("Move slightly up.", "Di chuyển nhẹ lên trên."),
        ("Move slightly down.", "Di chuyển nhẹ xuống dưới."),
        ("Previous-position match", "Khớp vị trí trước"),
    )
    for en, vi in pairs:
        assert en in js
        assert vi in js
    assert "speechSynthesis" in js


def test_v174_match_is_provisional_advisory_and_has_safe_fallbacks():
    js = JS.read_text(encoding="utf-8")
    assert "const MATCH_READY_SCORE=62" in js
    assert "const MAX_SHIFT_FRACTION=.15" in js
    assert "New baseline" in js and "Tạo ảnh mốc mới" in js
    assert "Position guidance unavailable" in js
    assert "Capture can continue using the standard image-quality checks." in js
    assert "window.skinDermatoscopeLiveGuidance" in js
    assert "capture(m)" not in js


def test_v174_assets_follow_existing_design_tokens_and_are_loaded_cached():
    css = CSS.read_text(encoding="utf-8")
    polish = POLISH.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert ".dermPositionGuide" in css
    assert "var(--line)" in css
    assert "var(--green)" in css
    for asset in (
        "/app/dermatoscope_live_guidance_v174.css?v=174",
        "/app/dermatoscope_live_guidance_v174.js?v=174",
    ):
        assert asset in polish
        assert asset in sw
    match = re.search(r"skin-ai-beta-v(\d+)", sw)
    assert match and int(match.group(1)) >= 174
