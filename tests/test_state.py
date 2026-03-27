"""Tests for shared state reader/writer."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from voice_bridge.state import read_state, write_state, read_state_value, read_env_key


def test_write_and_read_state(tmp_path):
    state_file = tmp_path / ".state"
    with patch("voice_bridge.state.get_state_file", return_value=state_file):
        write_state({"VOICE_BRIDGE_MODE": "always", "VOICE_BRIDGE_ENGINE": "edge-tts"})
        state = read_state()
        assert state["VOICE_BRIDGE_MODE"] == "always"
        assert state["VOICE_BRIDGE_ENGINE"] == "edge-tts"


def test_write_state_quotes_values(tmp_path):
    """State file values should be quoted for shell safety."""
    state_file = tmp_path / ".state"
    with patch("voice_bridge.state.get_state_file", return_value=state_file):
        write_state({"VOICE_BRIDGE_EDGE_RATE": "+20%"})
        content = state_file.read_text()
        assert 'VOICE_BRIDGE_EDGE_RATE="+20%"' in content


def test_read_state_handles_quoted_values(tmp_path):
    """Reader should strip surrounding quotes."""
    state_file = tmp_path / ".state"
    state_file.write_text('KEY="value with spaces"\n')
    with patch("voice_bridge.state.get_state_file", return_value=state_file):
        state = read_state()
        assert state["KEY"] == "value with spaces"


def test_read_state_handles_unquoted_values(tmp_path):
    state_file = tmp_path / ".state"
    state_file.write_text("KEY=simple\n")
    with patch("voice_bridge.state.get_state_file", return_value=state_file):
        state = read_state()
        assert state["KEY"] == "simple"


def test_read_state_skips_comments(tmp_path):
    state_file = tmp_path / ".state"
    state_file.write_text("# comment\nKEY=val\n")
    with patch("voice_bridge.state.get_state_file", return_value=state_file):
        state = read_state()
        assert "# comment" not in state
        assert state["KEY"] == "val"


def test_read_state_value(tmp_path):
    state_file = tmp_path / ".state"
    state_file.write_text('VOICE_BRIDGE_ENGINE="kokoro"\n')
    with patch("voice_bridge.state.get_state_file", return_value=state_file):
        assert read_state_value("VOICE_BRIDGE_ENGINE") == "kokoro"
        assert read_state_value("MISSING", "default") == "default"


def test_read_env_key_handles_quotes(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('ELEVENLABS_API_KEY="sk-test-123"\n')
    with patch("voice_bridge.state.get_env_file", return_value=env_file):
        assert read_env_key("ELEVENLABS_API_KEY") == "sk-test-123"


def test_read_env_key_unquoted(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ELEVENLABS_API_KEY=sk-test-123\n")
    with patch("voice_bridge.state.get_env_file", return_value=env_file):
        assert read_env_key("ELEVENLABS_API_KEY") == "sk-test-123"


def test_read_env_key_skips_comments(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# ELEVENLABS_API_KEY=old\nELEVENLABS_API_KEY=new\n")
    with patch("voice_bridge.state.get_env_file", return_value=env_file):
        assert read_env_key("ELEVENLABS_API_KEY") == "new"


def test_read_env_key_missing(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER_KEY=val\n")
    with patch("voice_bridge.state.get_env_file", return_value=env_file):
        assert read_env_key("MISSING", "fallback") == "fallback"
