from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UX = ROOT / "web" / "ux_polish_v1581.js"
I18N = ROOT / "web" / "i18n_v1601.js"


def test_v1604_ux_polish_uses_active_i18n_for_capture_labels():
    js = UX.read_text(encoding="utf-8")
    assert "window.skinI18n?.t" in js
    assert "setText(title,'Tester access')" in js
    assert "setText(toggle,'Use study code')" in js
    assert "setText(camera,'Open camera')" in js
    assert "setText(uploadTitle,'Or upload a front-facing photo')" in js
    assert "setText(title,'Advanced details')" in js


def test_v1604_ux_polish_reacts_to_locale_switches():
    js = UX.read_text(encoding="utf-8")
    assert "window.addEventListener('skin-ai:locale-change',schedule)" in js
    assert "Hide advanced settings" in js
    assert "Advanced scan settings" in js


def test_v1604_capture_labels_exist_in_dictionary():
    js = I18N.read_text(encoding="utf-8")
    expected = {
        "'Tester access':'Truy cập thử nghiệm'",
        "'Use study code':'Dùng mã thử nghiệm'",
        "'Open camera':'Mở camera'",
        "'Or upload a front-facing photo':'Hoặc tải ảnh chụp chính diện'",
        "'Advanced details':'Chi tiết nâng cao'",
        "'Measurement and scan-quality details':'Chi tiết chỉ số và chất lượng lần quét'",
    }
    for item in expected:
        assert item in js


def test_v1604_is_presentation_only():
    js = UX.read_text(encoding="utf-8")
    assert "No measurement or access-control changes" in js
    assert "redness_threshold" not in js
    assert "pigmentation_threshold" not in js
