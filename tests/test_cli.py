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


def test_voices_kokoro_filter_gender():
    """Test gender filtering for kokoro voices."""
    result = subprocess.run(
        [sys.executable, "-m", "voice_bridge.cli", "voices", "kokoro", "--gender", "Female"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "af_bella" in result.stdout
    assert "bf_emma" in result.stdout
    assert "am_adam" not in result.stdout
    assert "bm_lewis" not in result.stdout


def test_voices_edge_tts_filter_gender_locale():
    """Test gender + locale filtering for edge-tts voices."""
    result = subprocess.run(
        [sys.executable, "-m", "voice_bridge.cli", "voices", "edge-tts",
         "--gender", "Male", "--locale", "en-GB"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "en-GB-RyanNeural" in result.stdout
    # Should not contain US voices
    assert "en-US-GuyNeural" not in result.stdout


def test_voices_single_preview_arg():
    """Test that --preview with a voice name is accepted by argparse."""
    result = subprocess.run(
        [sys.executable, "-m", "voice_bridge.cli", "voices", "kokoro",
         "--preview", "bm_lewis"],
        capture_output=True, text=True,
        timeout=15,
    )
    # Should attempt to preview (may fail if kokoro not installed, but shouldn't crash argparse)
    assert result.returncode == 0 or "failed" in result.stdout
