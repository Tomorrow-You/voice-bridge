"""Tests for CLI commands."""
import subprocess
import sys


def test_voice_bridge_help():
    result = subprocess.run(
        [sys.executable, "-m", "voice_bridge.cli", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Voice Bridge" in result.stdout or "usage" in result.stdout.lower()


def test_vb_speak_help():
    result = subprocess.run(
        [sys.executable, "-m", "voice_bridge.speak", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Speak text" in result.stdout or "usage" in result.stdout.lower()


def test_vb_speak_dry_run():
    """Test that vb-speak --dry-run prints filtered text without speaking."""
    result = subprocess.run(
        [sys.executable, "-m", "voice_bridge.speak", "--dry-run", "Hello world"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Hello world" in result.stdout


def test_vb_speak_stdin_dry_run():
    """Test that vb-speak can read from stdin."""
    result = subprocess.run(
        [sys.executable, "-m", "voice_bridge.speak", "--dry-run"],
        input="Hello from stdin",
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Hello from stdin" in result.stdout


def test_voices_kokoro():
    """Test that voices command lists kokoro voices even when not installed."""
    result = subprocess.run(
        [sys.executable, "-m", "voice_bridge.cli", "voices", "kokoro"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Kokoro voices" in result.stdout
    assert "bm_lewis" in result.stdout
