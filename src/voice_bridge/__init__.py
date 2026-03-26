"""Voice Bridge -- multi-engine TTS for AI coding assistants."""

__version__ = "0.1.0"

import logging
from logging.handlers import RotatingFileHandler

from voice_bridge.paths import get_data_dir

_log_path = get_data_dir() / "voice-bridge.log"
try:
    _log_path.parent.mkdir(parents=True, exist_ok=True)
    _handler = RotatingFileHandler(str(_log_path), maxBytes=1_000_000, backupCount=2)
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    _logger = logging.getLogger("voice_bridge")
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
except (OSError, PermissionError):
    # Logging is non-critical -- don't crash if we can't write logs
    pass
