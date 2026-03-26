"""Tests for engine registry and discovery."""
import platform

from voice_bridge.engines import get_available_engines, resolve_engine_name
import pytest


def test_get_available_engines_returns_dict():
    available = get_available_engines()
    assert isinstance(available, dict)
    assert "say" in available
    assert "espeak" in available
    assert "edge-tts" in available
    assert "elevenlabs" in available
    assert "kokoro" in available


def test_say_available_on_macos():
    available = get_available_engines()
    if platform.system() == "Darwin":
        assert available["say"] is True
    else:
        assert available["say"] is False


def test_resolve_auto_picks_something_on_macos():
    """On macOS, auto should at least find 'say'."""
    if platform.system() != "Darwin":
        pytest.skip("macOS only")
    result = resolve_engine_name("auto")
    assert result in get_available_engines()


def test_resolve_unknown_engine_raises():
    with pytest.raises(ValueError, match="Unknown engine"):
        resolve_engine_name("nonexistent")


def test_resolve_unavailable_engine_raises():
    # kokoro is likely not installed in test env
    available = get_available_engines()
    for name, is_available in available.items():
        if not is_available:
            with pytest.raises(RuntimeError, match="not available"):
                resolve_engine_name(name)
            break
