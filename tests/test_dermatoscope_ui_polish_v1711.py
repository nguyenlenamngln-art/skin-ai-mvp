from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "dermatoscope_ui_polish_v1711.js"
CSS = ROOT / "web" / "dermatoscope_ui_polish_v1711.css"
TRANSITION = ROOT / "web" / "dermatoscope_transition_v1700.js"
SW = ROOT / "web" / "sw.js"


def test_v1711_customer_copy_uses_skin_ai_scope_and_vietnamese_product_terms():
    js = JS.read_text(encoding="utf-8")
    assert "Skin AI Scope" in js
    assert "QUÉT DA CẬN CẢNH" in js
    assert "Chọn vùng da cần kiểm tra" in js
    assert "CHUẨN BỊ MÁY SOI" in js
    assert "IBOOLO DE-500" not in js
    assert "QUÉT DERMATOSCOPE" not in js


def test_v1711_copy_remains_dual_language_and_describes_auto_capture():
    js = JS.read_text(encoding="utf-8")
    assert "CLOSE-UP SKIN SCAN" in js
    assert "Choose a skin area to examine" in js
    assert "PREPARE SKIN SCOPE" in js
    assert "Images are captured automatically" in js
    assert "tự động chụp" in js
    assert "skin-ai:locale-change" in js


def test_v1711_visual_polish_reuses_existing_design_tokens_and_mobile_layout():
    css = CSS.read_text(encoding="utf-8")
    for token in ("var(--line)", "var(--ink)", "var(--muted)", "var(--green)", "var(--sage)"):
        assert token in css
    assert "border-radius:20px" in css
    assert ".dermRegion.active" in css
    assert ".dermSetupFooter .primary" in css
    assert "@media(max-width:650px)" in css
    assert "grid-template-columns:1fr 1fr" in css


def test_v1711_polish_assets_are_loaded_and_cached():
    transition = TRANSITION.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    for asset in (
        "/app/dermatoscope_ui_polish_v1711.css?v=1711",
        "/app/dermatoscope_ui_polish_v1711.js?v=1711",
    ):
        assert asset in transition
        assert asset in sw
    assert "skin-ai-beta-v1711" in sw
