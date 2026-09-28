from pathlib import Path

import numpy as np
from PIL import Image

from skin_ai.dermatoscope_registration_v173 import _register

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "src" / "skin_ai" / "product_api_mobile_v14.py"
MODULE = ROOT / "src" / "skin_ai" / "dermatoscope_registration_v173.py"


def _save(arr: np.ndarray, path: Path) -> None:
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="L").save(path)


def test_v173_nearby_same_patch_is_comparable(tmp_path):
    y, x = np.mgrid[0:180, 0:180]
    base = 115 + 45 * np.sin(x / 8.0) + 30 * np.cos(y / 11.0)
    base += 55 * np.exp(-((x - 62) ** 2 + (y - 87) ** 2) / 120.0)
    moved = np.roll(np.roll(base, 5, axis=1), -3, axis=0)
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    _save(base, a)
    _save(moved, b)
    result = _register(str(a), str(b))
    assert result["status"] in {"comparable", "borderline"}
    assert result["score"] >= 62
    assert result["thresholds_provisional"] is True
    assert result["validated_for_de500"] is False


def test_v173_different_patch_is_not_strongly_comparable(tmp_path):
    rng = np.random.default_rng(3)
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    _save(rng.normal(120, 35, (180, 180)), a)
    _save(rng.normal(120, 35, (180, 180)), b)
    result = _register(str(a), str(b))
    assert result["status"] != "comparable"


def test_v173_endpoint_is_same_position_and_same_configuration_only():
    module = MODULE.read_text(encoding="utf-8")
    for field in (
        'current["region"]',
        'current["subregion"]',
        'current["illumination_mode"]',
        'current["brightness_level"]',
        'current["simulator"]',
    ):
        assert field in module
    assert 'ORDER BY created_at ASC LIMIT 1' in module
    assert '"thresholds_provisional": True' in module
    assert '"validated_for_de500": False' in module


def test_v173_is_installed_without_touching_frozen_rgb_engine():
    entry = ENTRY.read_text(encoding="utf-8")
    assert "install_dermatoscope_registration_v173(product_api)" in entry
    assert "from skin_ai.rgb_engine_v152 import RGBAnalysisEngine" in entry
    assert '_CAPTURE_PROTOCOL_VERSION = "1.4"' in entry
