"""Configuration loading for Voice Bridge."""

import os
from pydantic import BaseModel, Field

from voice_bridge.paths import get_env_file, get_data_dir
from voice_bridge.state import read_state_value

_dotenv_loaded = False


def _ensure_dotenv():
    """Load .env file lazily on first config access, not at import time."""
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True

    env_file = get_env_file()
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)


class TTSConfig(BaseModel):
    engine: str = Field(
        default_factory=lambda: read_state_value("VOICE_BRIDGE_ENGINE", "auto"),
        description="TTS engine: auto | edge-tts | elevenlabs | kokoro | say | espeak",
    )
    elevenlabs_api_key: str = Field(
        default_factory=lambda: (_ensure_dotenv(), os.getenv("ELEVENLABS_API_KEY", ""))[1]
    )
    elevenlabs_model: str = "eleven_flash_v2_5"
    elevenlabs_voice_id: str = Field(
        default_factory=lambda: (_ensure_dotenv(), os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"))[1],
        description="ElevenLabs voice ID",
    )
    elevenlabs_speed: float = Field(
        default_factory=lambda: float(read_state_value("VOICE_BRIDGE_ELEVENLABS_SPEED", "1.0")),
        description="ElevenLabs speed: 0.7-1.2",
    )
    kokoro_speed: float = Field(
        default_factory=lambda: float(read_state_value("VOICE_BRIDGE_KOKORO_SPEED", "1.4")),
        description="Kokoro speed (positive float)",
    )
    kokoro_voice: str = Field(
        default_factory=lambda: read_state_value("VOICE_BRIDGE_KOKORO_VOICE", "bm_lewis"),
        description="Kokoro voice name",
    )
    edge_tts_voice: str = Field(
        default_factory=lambda: read_state_value("VOICE_BRIDGE_EDGE_VOICE", "en-US-GuyNeural"),
        description="edge-tts voice name",
    )
    edge_tts_rate: str = Field(
        default_factory=lambda: read_state_value("VOICE_BRIDGE_EDGE_RATE", "+0%"),
        description="edge-tts rate adjustment (e.g. +20%, -10%)",
    )
    say_rate: int = Field(
        default_factory=lambda: int(read_state_value("VOICE_BRIDGE_SAY_RATE", "200")),
        description="macOS say words-per-minute (default 200)",
    )
    espeak_rate: int = Field(
        default_factory=lambda: int(read_state_value("VOICE_BRIDGE_ESPEAK_RATE", "175")),
        description="espeak-ng words-per-minute (default 175)",
    )
    sample_rate: int = 24000
    max_chars_per_request: int = 5000


class Config(BaseModel):
    tts: TTSConfig = Field(default_factory=TTSConfig)
    socket_path: str = Field(default_factory=lambda: str(get_data_dir() / "bridge.sock"))
    log_level: str = "INFO"


def load_config() -> Config:
    from voice_bridge import _setup_logging
    _setup_logging()
    return Config()
