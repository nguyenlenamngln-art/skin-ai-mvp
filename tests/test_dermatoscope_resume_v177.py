from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "src" / "skin_ai" / "dermatoscope_resume_v177.py"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"
SESSION_JS = ROOT / "web" / "dermatoscope_session_v176.js"
RESUME_JS = ROOT / "web" / "dermatoscope_resume_v177.js"
RESUME_CSS = ROOT / "web" / "dermatoscope_resume_v177.css"
POLISH = ROOT / "web" / "dermatoscope_ui_polish_v1711.js"
SW = ROOT / "web" / "sw.js"


def test_v177_backend_exposes_latest_resumable_and_resume_routes():
    api = API.read_text(encoding="utf-8")
    assert 'VERSION = "1.7.7"' in api
    assert '/v1/dermatoscope/sessions/resumable/latest' in api
    assert '/v1/dermatoscope/sessions/{session_id}/resume' in api
    assert "status IN ('active','incomplete')" in api
    assert 'item.get("status") in {"incomplete", "rejected"}' in api


def test_v177_entry_installs_v176_before_v177_and_preserves_rgb():
    entry = ENTRY.read_text(encoding="utf-8")
    assert "install_dermatoscope_session_v176(product_api)" in entry
    assert "install_dermatoscope_resume_v177(product_api)" in entry
    assert entry.index("install_dermatoscope_session_v176(product_api)") < entry.index("install_dermatoscope_resume_v177(product_api)")
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v177_frontend_restores_unresolved_positions_without_recapturing_accepted():
    js = RESUME_JS.read_text(encoding="utf-8")
    session_js = SESSION_JS.read_text(encoding="utf-8")
    assert "Accepted positions will not be captured again." in js
    assert "Các vị trí đã đạt sẽ không được chụp lại." in js
    assert "s!=='accepted'&&s!=='skipped'" in js
    assert "skinDermatoscopeSession?.adoptSession" in js
    assert "dermatoscopeResumeAdopting" in js
    assert "activeShots(r)" in session_js
    assert "adoptSession" in session_js


def test_v177_resume_ui_is_bilingual_and_uses_existing_design_tokens():
    js = RESUME_JS.read_text(encoding="utf-8")
    css = RESUME_CSS.read_text(encoding="utf-8")
    assert "Continue where you left off" in js
    assert "Tiếp tục từ vị trí đang dở" in js
    assert "Resume scan" in js and "Tiếp tục quét" in js
    for token in ("var(--line)", "var(--sage)", "var(--ink)", "var(--muted)"):
        assert token in css


def test_v177_assets_are_loaded_and_cached():
    polish = POLISH.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    for asset in (
        "/app/dermatoscope_resume_v177.css?v=177",
        "/app/dermatoscope_resume_v177.js?v=177",
    ):
        assert asset in polish
        assert asset in sw
    assert "skin-ai-beta-v177" in sw
