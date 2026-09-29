from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSITION = ROOT / "web" / "dermatoscope_transition_v1700.js"
POLISH = ROOT / "web" / "dermatoscope_ui_polish_v1711.js"
SW = ROOT / "web" / "sw.js"


def test_consumer_scan_detaches_unused_legacy_scan_grid():
    js = TRANSITION.read_text(encoding="utf-8")
    assert "function isolateConsumerScan" in js
    assert "legacy.remove()" in js
    assert "dermatoscopeLegacyScanDetached" in js
    assert "if(researchMode)return" in js


def test_polish_no_longer_observes_entire_scan_subtree():
    js = POLISH.read_text(encoding="utf-8")
    assert "new MutationObserver" not in js
    assert "skin-ai:locale-change" in js
    assert "[data-derm-region]" in js


def test_scan_isolation_assets_are_cache_busted():
    transition = TRANSITION.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "dermatoscope_ui_polish_v1711.js?v=17114" in transition
    assert "dermatoscope_ui_polish_v1711.js?v=17114" in sw
    assert "const CACHE='skin-ai-beta-v1784'" in sw
