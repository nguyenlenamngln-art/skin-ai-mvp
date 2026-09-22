__version__ = "0.1.0"

# Import applies the mobile-camera capture-quality calibration at package load.
# RGB signal measurements remain unchanged; only the accept/reject quality gate
# is adjusted for moderately soft phone-camera captures.
from . import mobile_quality_patch as _mobile_quality_patch  # noqa: F401,E402
