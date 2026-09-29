from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "web" / "dermatoscope_session_v176.js"
POLISH = ROOT / "web" / "dermatoscope_ui_polish_v1711.js"
SW = ROOT / "web" / "sw.js"


def test_session_render_writes_are_guarded():
    js = SESSION.read_text(encoding="utf-8")
    assert "function setText" in js
    assert "if(el&&el.textContent!==value)" in js
    assert "setText(panel.querySelector('#dermAttemptCount')" in js
    assert "setText(hint" in js


def test_session_observer_does_not_watch_entire_scan_childlist():
    js = SESSION.read_text(encoding="utf-8")
    assert "observer.observe(scan,{subtree:true,childList:true" not in js
    assert "#dermCounter" in js
    assert "#dermComplete" in js


def test_session_asset_is_cache_busted():
    polish = POLISH.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "dermatoscope_session_v176.js?v=1761" in polish
    assert "dermatoscope_session_v176.js?v=1761" in sw
    assert "const CACHE='skin-ai-beta-v1783'" in sw
