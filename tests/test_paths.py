"""Tests for path resolution."""
import os
import platform
from pathlib import Path
from unittest.mock import patch

from voice_bridge.paths import get_data_dir, get_state_file, get_env_file, get_models_dir


def test_get_data_dir_returns_path():
    result = get_data_dir()
    assert isinstance(result, Path)
    assert result.exists()


def test_env_override():
    with patch.dict(os.environ, {"VOICE_BRIDGE_HOME": "/tmp/vb-test-data"}):
        result = get_data_dir()
        assert result == Path("/tmp/vb-test-data")


def test_state_file_in_data_dir():
    state = get_state_file()
    data = get_data_dir()
    assert state.parent == data
    assert state.name == ".state"


def test_env_file_in_data_dir():
    env = get_env_file()
    data = get_data_dir()
    assert env.parent == data
    assert env.name == ".env"


def test_models_dir_in_data_dir():
    models = get_models_dir()
    data = get_data_dir()
    assert models.parent == data
    assert models.name == "models"


def test_macos_default():
    if platform.system() != "Darwin":
        return
    with patch.dict(os.environ, {}, clear=True):
        # Remove override if present
        os.environ.pop("VOICE_BRIDGE_HOME", None)
        result = get_data_dir()
        assert ".voice-bridge" in str(result)
