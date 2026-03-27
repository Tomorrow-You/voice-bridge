"""Voice Bridge -- multi-engine TTS for AI coding assistants."""

__version__ = "0.1.0"

__all__ = ["__version__"]

# Logging is set up lazily on first engine use, not at import time.
# This avoids creating directories or file handles just from `import voice_bridge`.

_logging_initialized = False


def _setup_logging():
    """Initialize file logging on first use. Called by load_config()."""
    global _logging_initialized
    if _logging_initialized:
        return
    _logging_initialized = True

    import logging
    from logging.handlers import RotatingFileHandler
    from voice_bridge.paths import get_data_dir

    try:
        log_path = get_data_dir() / "voice-bridge.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(str(log_path), maxBytes=1_000_000, backupCount=2)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
        logger = logging.getLogger("voice_bridge")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    except (OSError, PermissionError):
        pass
