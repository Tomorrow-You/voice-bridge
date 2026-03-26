"""Engine registry with graceful discovery of optional dependencies."""

import platform
import shutil
from typing import Optional

from voice_bridge.tts.base import TTSEngine

# Engine names in preference order for auto-detection
ENGINE_PREFERENCE = ["edge-tts", "say", "espeak", "kokoro", "elevenlabs"]


def get_available_engines() -> dict[str, bool]:
    """Return dict of engine_name -> is_available."""
    available = {}

    # edge-tts: needs pip install voice-bridge[edge]
    try:
        import edge_tts  # noqa: F401
        available["edge-tts"] = True
    except ImportError:
        available["edge-tts"] = False

    # elevenlabs: needs pip install voice-bridge[elevenlabs]
    try:
        import elevenlabs  # noqa: F401
        import sounddevice  # noqa: F401
        available["elevenlabs"] = True
    except ImportError:
        available["elevenlabs"] = False

    # kokoro: needs pip install voice-bridge[kokoro]
    try:
        import kokoro_onnx  # noqa: F401
        import sounddevice  # noqa: F401
        available["kokoro"] = True
    except ImportError:
        available["kokoro"] = False

    # macOS say: built-in on macOS
    available["say"] = platform.system() == "Darwin" and shutil.which("say") is not None

    # espeak-ng: built-in on most Linux distros
    available["espeak"] = shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None

    return available


def resolve_engine_name(requested: str) -> str:
    """Resolve 'auto' to the best available engine, or validate a specific name."""
    available = get_available_engines()

    if requested == "auto":
        for name in ENGINE_PREFERENCE:
            if available.get(name, False):
                return name
        raise RuntimeError(
            "No TTS engine available. Install one with:\n"
            "  pip install voice-bridge[edge]       # Free, cross-platform (recommended)\n"
            "  pip install voice-bridge[elevenlabs]  # Cloud, paid, highest quality\n"
            "  pip install voice-bridge[kokoro]      # Local, free, offline\n"
            "On macOS, the built-in 'say' command works without extras."
        )

    if requested not in available:
        raise ValueError(f"Unknown engine: {requested}. Options: {', '.join(available.keys())}")

    if not available[requested]:
        install_hints = {
            "edge-tts": "pip install voice-bridge[edge]",
            "elevenlabs": "pip install voice-bridge[elevenlabs]",
            "kokoro": "pip install voice-bridge[kokoro]",
            "say": "Only available on macOS",
            "espeak": "Install espeak-ng: apt install espeak-ng (Linux) or brew install espeak (macOS)",
        }
        hint = install_hints.get(requested, "Check the docs for installation instructions")
        raise RuntimeError(f"Engine '{requested}' is not available. {hint}")

    return requested


def create_engine(name: str, config: Optional["TTSConfig"] = None) -> TTSEngine:
    """Create a TTS engine instance by name."""
    from voice_bridge.config import TTSConfig
    if config is None:
        config = TTSConfig()

    resolved = resolve_engine_name(name)

    if resolved == "edge-tts":
        from voice_bridge.tts.edge_tts_engine import EdgeTTSEngine
        return EdgeTTSEngine(voice=config.edge_tts_voice, rate=config.edge_tts_rate)

    if resolved == "elevenlabs":
        from voice_bridge.tts.elevenlabs_engine import ElevenLabsTTS
        return ElevenLabsTTS(config)

    if resolved == "kokoro":
        from voice_bridge.tts.kokoro_engine import KokoroTTS
        return KokoroTTS(voice=config.kokoro_voice, speed=config.kokoro_speed)

    if resolved == "say":
        from voice_bridge.tts.macos_say import MacOSSayTTS
        return MacOSSayTTS()

    if resolved == "espeak":
        from voice_bridge.tts.espeak_engine import EspeakTTS
        return EspeakTTS()

    raise ValueError(f"No engine implementation for: {resolved}")
