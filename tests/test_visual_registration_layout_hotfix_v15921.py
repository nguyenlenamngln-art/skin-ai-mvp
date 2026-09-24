from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "web" / "comparable_progress_v159.css"
SW = ROOT / "web" / "sw.js"


def test_v15921_desktop_comparison_is_forced_full_width_from_direct_stylesheet():
    css = CSS.read_text(encoding="utf-8")
    assert ".pjCompare{grid-template-columns:minmax(0,1fr)!important}" in css
    assert ".pjCompare>*{min-width:0}" in css
    assert "width:100%!important" in css
    assert "max-width:none!important" in css
    assert "aspect-ratio:auto!important" in css
    assert "justify-self:stretch!important" in css
    assert ".pjCompareSlider{width:100%!important;max-width:none!important}" in css


def test_v15921_cache_bump_for_layout_hotfix():
    sw = SW.read_text(encoding="utf-8")
    assert "skin-ai-beta-v15921" in sw
    assert "/app/comparable_progress_v159.css?v=159" in sw
