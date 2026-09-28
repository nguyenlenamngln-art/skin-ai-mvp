from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "src" / "skin_ai" / "dermatoscope_session_v176.py"
RETAKE = ROOT / "src" / "skin_ai" / "dermatoscope_retake_v175.py"
JS = ROOT / "web" / "dermatoscope_session_v176.js"
POST = ROOT / "web" / "dermatoscope_postcapture_v175.js"
CSS = ROOT / "web" / "dermatoscope_session_v176.css"
POLISH = ROOT / "web" / "dermatoscope_ui_polish_v1711.js"
SW = ROOT / "web" / "sw.js"


def test_v176_backend_tracks_explicit_session_and_position_states():
    api = API.read_text(encoding="utf-8")
    assert 'VERSION = "1.7.6"' in api
    assert '{"accepted", "rejected", "skipped", "incomplete"}' in api
    assert '/v1/dermatoscope/sessions' in api
    assert '/positions' in api
    assert '/finish' in api
    assert '"attempts": 0' in api
    assert '"status": "incomplete"' in api


def test_v176_session_backend_is_installed_through_existing_dermatoscope_stack():
    retake = RETAKE.read_text(encoding="utf-8")
    assert "from skin_ai.dermatoscope_session_v176 import install_dermatoscope_session_v176" in retake
    assert "install_dermatoscope_session_v176(product_api)" in retake


def test_v176_frontend_caps_retries_and_marks_unresolved_position_incomplete():
    js = JS.read_text(encoding="utf-8")
    post = POST.read_text(encoding="utf-8")
    assert "const MAX_ATTEMPTS=3" in js
    assert "registerRejected" in js
    assert "session_retry_allowed" in js
    assert "Retry limit reached" in js
    assert "Đã đạt giới hạn chụp lại" in js
    assert "window.skinDermatoscopeSession?.registerRejected?.(validation)" in post
    assert "if(retryAllowed!==false)throw new Error('dermatoscope_position_retake_required')" in post
    assert "marked incomplete" in post


def test_v176_session_completion_distinguishes_complete_incomplete_and_cancelled():
    api = API.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    for status in ("complete", "incomplete", "cancelled"):
        assert status in api
    assert "finishSession('cancelled')" in js
    assert "?'incomplete':'complete'" in js


def test_v176_assets_follow_existing_design_tokens_and_are_cached():
    css = CSS.read_text(encoding="utf-8")
    polish = POLISH.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    assert "var(--line)" in css
    assert "var(--muted)" in css
    for asset in (
        "/app/dermatoscope_session_v176.css?v=176",
        "/app/dermatoscope_session_v176.js?v=176",
    ):
        assert asset in polish
        assert asset in sw
    assert "skin-ai-beta-v176" in sw
