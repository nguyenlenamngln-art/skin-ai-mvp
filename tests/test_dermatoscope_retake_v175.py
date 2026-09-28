from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "src" / "skin_ai" / "dermatoscope_retake_v175.py"
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"
HISTORY = ROOT / "src" / "skin_ai" / "dermatoscope_history_v172.py"
REGISTRATION = ROOT / "src" / "skin_ai" / "dermatoscope_registration_v173.py"
JS = ROOT / "web" / "dermatoscope_postcapture_v175.js"
CSS = ROOT / "web" / "dermatoscope_postcapture_v175.css"
POLISH = ROOT / "web" / "dermatoscope_ui_polish_v1711.js"
SW = ROOT / "web" / "sw.js"


def test_v175_backend_marks_weak_position_capture_for_retake():
    api = API.read_text(encoding="utf-8")
    assert 'VERSION = "1.7.5"' in api
    assert 'REJECTED_STATUS = "rejected_position"' in api
    assert '/v1/dermatoscope/captures/{capture_id}/validate-position' in api
    assert 'result["status"] in {"comparable", "borderline"}' in api
    assert '"retake_required": not accepted' in api
    assert '"thresholds_provisional": True' in api
    assert '"validated_for_de500": False' in api


def test_v175_first_capture_remains_valid_baseline():
    api = API.read_text(encoding="utf-8")
    assert '"status": "baseline"' in api
    assert '"accepted": True' in api
    assert '"retake_required": False' in api


def test_v175_rejected_images_do_not_enter_longitudinal_history_or_baseline():
    history = HISTORY.read_text(encoding="utf-8")
    registration = REGISTRATION.read_text(encoding="utf-8")
    assert "longitudinal_status = 'accepted'" in history
    assert "longitudinal_status='accepted'" in history
    assert "longitudinal_status='accepted'" in registration
    assert 'baseline_rule": "first_accepted_capture"' in history


def test_v175_is_installed_after_registration_without_touching_rgb_engine():
    entry = ENTRY.read_text(encoding="utf-8")
    assert "install_dermatoscope_registration_v173(product_api)" in entry
    assert "install_dermatoscope_retake_v175(product_api)" in entry
    assert entry.index("install_dermatoscope_registration_v173(product_api)") < entry.index("install_dermatoscope_retake_v175(product_api)")
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry


def test_v175_frontend_rearms_same_subregion_with_bilingual_retake_feedback():
    js = JS.read_text(encoding="utf-8")
    assert "validate-position" in js
    assert "retake_required" in js
    assert "skin-ai:dermatoscope-retake-required" in js
    assert "Retake this position" in js
    assert "Chụp lại vị trí này" in js
    assert "Cần chụp lại" in js
    assert "window.skinDermatoscopeLiveGuidance?.reset?.()" in js
    assert CSS.exists()


def test_v175_assets_are_loaded_and_cached():
    polish = POLISH.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    for asset in (
        "/app/dermatoscope_postcapture_v175.css?v=175",
        "/app/dermatoscope_postcapture_v175.js?v=175",
    ):
        assert asset in polish
        assert asset in sw
    assert "skin-ai-beta-v175" in sw
