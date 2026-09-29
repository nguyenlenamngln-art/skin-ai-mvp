from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "web" / "localization_runtime_patch_v1602.js"


def test_localization_patch_has_reentry_guard_and_no_scan_poll_loop():
    text = JS.read_text(encoding="utf-8")
    assert "const VERSION='1.6.0.6'" in text
    assert "let applying=false" in text
    assert "if(applying)return" in text
    assert "if(scheduled||applying)return" in text
    assert "setInterval(()=>{if(document.querySelector('#scan.view.active'))schedule()},750)" not in text


def test_scan_label_mutations_are_change_guarded():
    text = JS.read_text(encoding="utf-8")
    assert "function setText(el,value){if(el&&el.textContent!==value)el.textContent=value}" in text
    assert "function setAttr(el,name,value){if(el&&el.getAttribute(name)!==value)el.setAttribute(name,value)}" in text
    assert "for(const [selector,en] of pairs)setText(document.querySelector(selector),t(en))" in text
