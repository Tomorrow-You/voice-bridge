"""Configuration loading for Voice Bridge."""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from voice_bridge.paths import get_env_file, get_state_file, get_data_dir

# Load .env if it exists
_env_file = get_env_file()
if _env_file.exists():
    load_dotenv(_env_file)


def _read_state_value(key: str, default: str = "") -> str:
    """Read a single value from the .state file."""
    state_file = get_state_file()
    if state_file.exists():
        for line in state_file.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.strip().split("=", 1)[1]
    return default


class TTSConfig(BaseModel):
    engine: str = Field(
        default_factory=lambda: _read_state_value("VOICE_BRIDGE_ENGINE", "auto"),
        description="TTS engine: auto | edge-tts | elevenlabs | kokoro | say | espeak",
    )
    elevenlabs_api_key: str = Field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    elevenlabs_model: str = "eleven_flash_v2_5"
    elevenlabs_voice_id: str = Field(
        default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"),
        description="ElevenLabs voice ID",
    )
    elevenlabs_speed: float = Field(
        default_factory=lambda: float(_read_state_value("VOICE_BRIDGE_ELEVENLABS_SPEED", "1.0")),
        description="ElevenLabs speed: 0.7-1.2",
    )
    kokoro_speed: float = Field(
        default_factory=lambda: float(_read_state_value("VOICE_BRIDGE_KOKORO_SPEED", "1.4")),
        description="Kokoro speed (positive float)",
    )
    kokoro_voice: str = Field(
        default_factory=lambda: _read_state_value("VOICE_BRIDGE_KOKORO_VOICE", "bm_lewis"),
        description="Kokoro voice name",
    )
    edge_tts_voice: str = Field(
        default_factory=lambda: _read_state_value("VOICE_BRIDGE_EDGE_VOICE", "en-US-GuyNeural"),
        description="edge-tts voice name",
    )
    edge_tts_rate: str = Field(
        default_factory=lambda: _read_state_value("VOICE_BRIDGE_EDGE_RATE", "+0%"),
        description="edge-tts rate adjustment (e.g. +20%, -10%)",
    )
    sample_rate: int = 24000
    max_chars_per_request: int = 5000


class Config(BaseModel):
    tts: TTSConfig = Field(default_factory=TTSConfig)
    socket_path: str = Field(default_factory=lambda: str(get_data_dir() / "bridge.sock"))
    log_level: str = "INFO"


def load_config() -> Config:
    return Config()
