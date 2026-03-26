"""Tests for TTS engine implementations."""
import platform
import pytest

from voice_bridge.config import TTSConfig


def test_macos_say_engine_initializes():
    if platform.system() != "Darwin":
        pytest.skip("macOS only")
    from voice_bridge.tts.macos_say import MacOSSayTTS
    engine = MacOSSayTTS()
    assert engine is not None
    assert engine.voice == "Samantha"
    assert engine.rate == 200


def test_elevenlabs_engine_initializes():
    try:
        from voice_bridge.tts.elevenlabs_engine import ElevenLabsTTS
    except ImportError:
        pytest.skip("elevenlabs not installed")
    config = TTSConfig(elevenlabs_api_key="test_key")
    engine = ElevenLabsTTS(config)
    assert engine.model == "eleven_flash_v2_5"
    assert engine.voice_id is not None


def test_elevenlabs_chunks_long_text():
    try:
        from voice_bridge.tts.elevenlabs_engine import ElevenLabsTTS
    except ImportError:
        pytest.skip("elevenlabs not installed")
    config = TTSConfig(elevenlabs_api_key="test_key", max_chars_per_request=60)
    engine = ElevenLabsTTS(config)
    text = "First sentence is here now. Second sentence is also here. Third sentence follows right after that."
    chunks = engine._chunk_text(text)
    assert len(chunks) >= 2
    assert all(len(c) <= 60 for c in chunks)


def test_elevenlabs_hard_splits_long_text():
    try:
        from voice_bridge.tts.elevenlabs_engine import ElevenLabsTTS
    except ImportError:
        pytest.skip("elevenlabs not installed")
    config = TTSConfig(elevenlabs_api_key="test_key", max_chars_per_request=100)
    engine = ElevenLabsTTS(config)
    text = "A" * 250
    chunks = engine._chunk_text(text)
    assert len(chunks) == 3
    assert all(len(c) <= 100 for c in chunks)


def test_edge_tts_engine_initializes():
    try:
        from voice_bridge.tts.edge_tts_engine import EdgeTTSEngine
    except ImportError:
        pytest.skip("edge-tts not installed")
    engine = EdgeTTSEngine()
    assert engine.voice == "en-US-GuyNeural"
    assert engine.rate == "+0%"


def test_espeak_engine_initializes():
    import shutil
    if not (shutil.which("espeak-ng") or shutil.which("espeak")):
        pytest.skip("espeak-ng not installed")
    from voice_bridge.tts.espeak_engine import EspeakTTS
    engine = EspeakTTS()
    assert engine is not None
