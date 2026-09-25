from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "web" / "rejected_state_i18n_v1606.js"
INDEX = ROOT / "web" / "index.html"
SW = ROOT / "web" / "sw.js"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v1606_translates_rejected_state_shell():
    js = PATCH.read_text(encoding="utf-8")
    for en, vi in (
        ("Capture rejected — not saved.", "Ảnh chụp chưa đạt — chưa được lưu."),
        ("Status", "Trạng thái"),
        ("Rejected", "Không đạt"),
        ("Capture quality", "Chất lượng ảnh chụp"),
        ("Issues", "Vấn đề"),
        ("Retake guidance", "Hướng dẫn chụp lại"),
    ):
        assert en in js
        assert vi in js


def test_v1606_translates_quality_codes_seen_in_screenshots():
    js = PATCH.read_text(encoding="utf-8")
    assert "face_too_small:['Face too small in frame','Khuôn mặt quá nhỏ trong khung']" in js
    assert "lighting_not_comparable:['Lighting differs from baseline','Ánh sáng không tương đồng với mốc so sánh']" in js
    assert "flags.map(flagLabel).join(', ')" in js
    assert "cards[2].querySelector('strong').title=flags.join(', ')" in js


def test_v1606_translates_dynamic_ev_guidance():
    js = PATCH.read_text(encoding="utf-8")
    assert "Lighting differs from the comparable baseline by ([0-9.]+) EV" in js
    assert "Ánh sáng chênh so với mốc so sánh" in js
    assert "sáng hơn" in js
    assert "tối hơn" in js


def test_v1606_translates_known_backend_guidance_and_previous_scan_note():
    js = PATCH.read_text(encoding="utf-8")
    for text in (
        "Move closer so the full face is clearly visible and occupies more of the center of the frame.",
        "Move the phone farther away so the full face is visible.",
        "Hold the phone steady for a moment and tap the face to refocus before capture.",
        "The previous saved scan remains in History, but it is intentionally not shown here as the result of this rejected attempt.",
    ):
        assert text in js


def test_v1606_reacts_to_runtime_locale_change():
    js = PATCH.read_text(encoding="utf-8")
    assert "skin-ai:locale-change" in js
    assert "renderRejectedAttempt=function()" in js
    assert "showError=function(msg='')" in js
    assert "window.skinRejectedI18n" in js


def test_v1606_asset_is_loaded_last_and_cached():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "/app/rejected_state_i18n_v1606.js?v=" in html
    assert "/app/rejected_state_i18n_v1606.js?v=" in sw
    assert html.index("localization_runtime_patch_v1602.js?v=1602") < html.index("rejected_state_i18n_v1606.js?v=")
    assert "skin-ai-beta-v160" in sw


def test_v1606_is_presentation_only_and_engine_is_frozen():
    js = PATCH.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
