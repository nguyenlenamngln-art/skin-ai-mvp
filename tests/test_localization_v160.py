from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "web" / "index.html"
JS = ROOT / "web" / "i18n_v160.js"
CSS = ROOT / "web" / "i18n_v160.css"
SW = ROOT / "web" / "sw.js"
MANIFEST = ROOT / "web" / "manifest.webmanifest"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"


def test_v160_assets_are_loaded_last_and_vietnamese_is_default():
    html = INDEX.read_text(encoding="utf-8")
    assert '<html lang="vi">' in html
    assert '/app/i18n_v160.css?v=160' in html
    assert '/app/i18n_v160.js?v=160' in html
    assert html.index('mobile_comparison_registration_v1593.js') < html.index('i18n_v160.js')


def test_v160_has_persistent_vi_en_switch_and_translation_api():
    js = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "skin_ai_locale_v160" in js
    assert "const SUPPORTED=['vi','en']" in js
    assert "data-locale=\"vi\"" in js
    assert "data-locale=\"en\"" in js
    assert "window.skinI18n" in js
    assert ".languageSwitchV160" in css


def test_v160_localizes_core_tester_navigation_and_product_copy():
    js = JS.read_text(encoding="utf-8")
    for vietnamese in (
        "Hôm nay",
        "Tiến trình",
        "Quét da",
        "Chu trình",
        "Hành trình",
        "Làn da hôm nay",
        "Tổng quan hôm nay",
        "Độ phù hợp để so sánh",
        "Trước & Sau" if False else "TRƯỚC & SAU",
        "Mở camera",
        "Nhật ký da" if False else "NHẬT KÝ DA",
    ):
        assert vietnamese in js


def test_v160_localizes_dynamic_dates_and_comparison_messages():
    js = JS.read_text(encoding="utf-8")
    assert "MONTHS" in js
    assert "WEEKDAYS" in js
    assert "So với mốc ban đầu ngày" in js
    assert "lần quét có thể so sánh" in js
    assert "Rất phù hợp" in js
    assert "Có thể dùng" in js
    assert "Cần xem lại" in js


def test_v160_pwa_is_vietnamese_first_and_cached_offline():
    sw = SW.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "skin-ai-beta-v160" in sw
    assert "/app/i18n_v160.css?v=160" in sw
    assert "/app/i18n_v160.js?v=160" in sw
    assert '"lang": "vi"' in manifest
    assert "Theo dõi da cá nhân" in manifest


def test_v160_does_not_modify_measurement_engine_or_capture_protocol():
    js = JS.read_text(encoding="utf-8")
    entry = ENTRY.read_text(encoding="utf-8")
    assert "Presentation only" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
