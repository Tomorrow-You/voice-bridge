"""Tests for configuration loading."""
from voice_bridge.config import TTSConfig, Config, load_config


def test_default_config():
    config = load_config()
    assert isinstance(config, Config)
    assert isinstance(config.tts, TTSConfig)


def test_tts_config_defaults():
    config = TTSConfig()
    assert config.sample_rate == 24000
    assert config.max_chars_per_request == 5000
    assert config.elevenlabs_model == "eleven_flash_v2_5"


def test_tts_config_override():
    config = TTSConfig(elevenlabs_api_key="test_key", sample_rate=16000)
    assert config.elevenlabs_api_key == "test_key"
    assert config.sample_rate == 16000
