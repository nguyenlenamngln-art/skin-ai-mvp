from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
SW = ROOT / "web" / "sw.js"
MOBILE_NAV = ROOT / "web" / "mobile_navigation_v1583.js"
PATCH = ROOT / "web" / "localization_runtime_patch_v1602.js"


def test_v1602_mobile_navigation_respects_active_locale():
    js = MOBILE_NAV.read_text(encoding="utf-8")
    assert "window.skinI18n?.t" in js
    assert "ui('Take a skin scan')" in js
    assert "window.addEventListener('skin-ai:locale-change',schedule)" in js


def test_v1602_compound_status_terms_are_bilingual():
    js = PATCH.read_text(encoding="utf-8")
    assert "'↑ Higher':'↑ Cao hơn'" in js
    assert "'↓ Lower':'↓ Thấp hơn'" in js
    assert "'→ Stable':'→ Ổn định'" in js
    assert "VI_TO_EN" in js
    assert "skin-ai:locale-change" in js


def test_v1602_runtime_patch_is_loaded_last_and_cached():
    html = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    asset = "/app/localization_runtime_patch_v1602.js?v=1602"
    assert asset in html
    assert asset in sw
    assert html.index("i18n_v1601.js?v=1601") < html.index("localization_runtime_patch_v1602.js?v=1602")
    # Later localization releases may advance the global PWA cache version.
    assert "const CACHE='skin-ai-beta-v" in sw


def test_v1602_does_not_touch_measurement_engine():
    js = PATCH.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
