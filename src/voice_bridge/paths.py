"""Centralized path resolution for Voice Bridge data directory.

Priority:
1. VOICE_BRIDGE_HOME env var (explicit override)
2. ~/.voice-bridge/ on macOS (conventional)
3. $XDG_DATA_HOME/voice-bridge/ on Linux (XDG spec)
4. ~/.voice-bridge/ fallback everywhere else
"""

import os
import platform
from pathlib import Path


def get_data_dir() -> Path:
    """Return the Voice Bridge data directory, creating it if needed."""
    # Explicit override
    env = os.environ.get("VOICE_BRIDGE_HOME")
    if env:
        p = Path(env)
        p.mkdir(parents=True, exist_ok=True)
        return p

    system = platform.system()

    if system == "Darwin":
        # macOS: use ~/.voice-bridge (conventional for CLI tools)
        p = Path.home() / ".voice-bridge"
    elif system == "Linux":
        # Linux: respect XDG_DATA_HOME
        xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        p = Path(xdg) / "voice-bridge"
    elif system == "Windows":
        # Windows: use %APPDATA%
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        p = Path(appdata) / "voice-bridge"
    else:
        p = Path.home() / ".voice-bridge"

    p.mkdir(parents=True, exist_ok=True)
    return p


def get_state_file() -> Path:
    """Return path to the .state file."""
    return get_data_dir() / ".state"


def get_env_file() -> Path:
    """Return path to the .env file."""
    return get_data_dir() / ".env"


def get_models_dir() -> Path:
    """Return path to the models directory (for Kokoro ONNX files)."""
    return get_data_dir() / "models"
