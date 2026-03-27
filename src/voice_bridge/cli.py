"""
voice-bridge: Control the voice bridge.

Usage:
    voice-bridge on           # Always-on mode (every response gets TTS)
    voice-bridge off          # Disable always-on (single-turn "speak" still works)
    voice-bridge status       # Show current mode, engine, available engines
    voice-bridge test         # Speak a test phrase
    voice-bridge engine [name]  # Get/set engine
    voice-bridge voice [id]   # Set voice for current engine
    voice-bridge speed [val]  # Set engine speed
    voice-bridge setup        # Interactive first-run setup
    voice-bridge engines      # List available engines
    voice-bridge voices [engine]                        # List available voices
    voice-bridge voices edge-tts --preview en-US-GuyNeural  # Preview one voice
    voice-bridge voices edge-tts --gender Female --preview  # Filter + interactive preview
    voice-bridge voices edge-tts --sample 3 --preview       # Random sample of 3

Modes:
    off      -- TTS only when user types "speak" keyword (single-turn)
    always   -- TTS on every Claude response
"""
import argparse
import sys

from voice_bridge.paths import get_env_file
from voice_bridge.state import read_state, write_state, read_env_key


def main():
    parser = argparse.ArgumentParser(
        description="Voice Bridge -- multi-engine TTS for AI coding assistants",
        epilog='Modes: "off" = single-turn only (type "speak" keyword), "always" = every response',
    )
    parser.add_argument(
        "command",
        choices=["on", "off", "status", "test", "voice", "voices", "engine", "engines", "speed", "setup"],
        help="Command to run",
    )
    parser.add_argument("value", nargs="?", help="Value for voice/engine/speed commands")
    parser.add_argument("--preview", nargs="?", const="__all__", default=None,
                        metavar="VOICE", help="Preview voices: --preview (interactive) or --preview VOICE_NAME (one voice)")
    parser.add_argument("--gender", help="Filter voices by gender (Male/Female)")
    parser.add_argument("--locale", help="Filter voices by locale (e.g. en-US, en-GB)")
    parser.add_argument("--sample", type=int, help="Preview N random voices")
    args = parser.parse_args()

    state = read_state()

    if args.command == "on":
        state["VOICE_BRIDGE_MODE"] = "always"
        write_state(state)
        print("Voice bridge: ALWAYS ON (every response will be spoken)")
        print('To speak a single response instead, type "speak" before your message.')

    elif args.command == "off":
        state["VOICE_BRIDGE_MODE"] = "off"
        write_state(state)
        print("Voice bridge: OFF (always-on disabled)")
        print('Single-turn mode still works -- type "speak" before any message.')

    elif args.command == "status":
        mode = state.get("VOICE_BRIDGE_MODE", "off")
        engine = state.get("VOICE_BRIDGE_ENGINE", "auto")
        mode_desc = {
            "off": 'OFF (single-turn only -- type "speak" to trigger)',
            "always": "ALWAYS ON (every response spoken)",
        }
        print(f"Voice bridge: {mode_desc.get(mode, mode)}")
        print(f"Engine: {engine}")

        from voice_bridge.engines import get_available_engines, resolve_engine_name
        available = get_available_engines()
        installed = [name for name, ok in available.items() if ok]
        print(f"Available engines: {', '.join(installed) if installed else 'none'}")

        if engine == "auto":
            try:
                resolved = resolve_engine_name("auto")
                print(f"Auto-selected: {resolved}")
            except RuntimeError:
                print("Auto-select: no engine available (run 'voice-bridge setup')")

        if engine == "edge-tts" or (engine == "auto" and "edge-tts" in installed):
            rate = state.get('VOICE_BRIDGE_EDGE_RATE', '+0%')
            if rate != '+0%':
                print(f"edge-tts rate: {rate}")
        if engine == "elevenlabs" or (engine == "auto" and "elevenlabs" in installed):
            print(f"ElevenLabs speed: {state.get('VOICE_BRIDGE_ELEVENLABS_SPEED', '1.0')}")
        if engine == "kokoro" or (engine == "auto" and "kokoro" in installed):
            print(f"Kokoro speed: {state.get('VOICE_BRIDGE_KOKORO_SPEED', '1.4')}")
        if engine == "say" or (engine == "auto" and "say" in installed):
            rate = state.get('VOICE_BRIDGE_SAY_RATE', '200')
            if rate != '200':
                print(f"say rate: {rate} words/min")
        if engine == "espeak" or (engine == "auto" and "espeak" in installed):
            rate = state.get('VOICE_BRIDGE_ESPEAK_RATE', '175')
            if rate != '175':
                print(f"espeak rate: {rate} words/min")

    elif args.command == "engines":
        from voice_bridge.engines import get_available_engines
        available = get_available_engines()
        print("Available TTS engines:\n")
        engine_info = {
            "edge-tts": ("Free, 400+ voices, cross-platform", "pip install ai-voice-bridge[edge]"),
            "elevenlabs": ("Cloud, highest quality, paid", "pip install ai-voice-bridge[elevenlabs]"),
            "kokoro": ("Local, free, offline (82M ONNX model)", "pip install ai-voice-bridge[kokoro]"),
            "say": ("macOS built-in, zero deps", "Built-in on macOS"),
            "espeak": ("Linux built-in, zero deps", "apt install espeak-ng"),
        }
        for name, (desc, install) in engine_info.items():
            status = "installed" if available.get(name) else "not installed"
            print(f"  {name:12s} [{status}]")
            print(f"    {desc}")
            if not available.get(name):
                print(f"    Install: {install}")
            print()

    elif args.command == "test":
        from voice_bridge.config import load_config
        from voice_bridge.engines import create_engine
        config = load_config()
        engine_name = state.get("VOICE_BRIDGE_ENGINE", "auto")
        try:
            engine = create_engine(engine_name, config.tts)
            print(f"Testing engine: {engine_name}...")
            engine.speak("Voice bridge is working. This is a test of the text to speech system.")
            print("Success!")
        except (RuntimeError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "voice":
        engine = state.get("VOICE_BRIDGE_ENGINE", "auto")
        # Resolve auto to show which engine the voice command applies to
        from voice_bridge.engines import resolve_engine_name
        try:
            resolved = resolve_engine_name(engine)
        except (RuntimeError, ValueError):
            resolved = engine

        if args.value:
            if resolved == "elevenlabs":
                env_file = get_env_file()
                lines = env_file.read_text().splitlines() if env_file.exists() else []
                found = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("ELEVENLABS_VOICE_ID="):
                        lines[i] = f"ELEVENLABS_VOICE_ID={args.value}"
                        found = True
                        break
                if not found:
                    lines.append(f"ELEVENLABS_VOICE_ID={args.value}")
                env_file.write_text("\n".join(lines) + "\n")
                print(f"ElevenLabs voice set to: {args.value}")
            elif resolved == "edge-tts":
                state["VOICE_BRIDGE_EDGE_VOICE"] = args.value
                write_state(state)
                print(f"edge-tts voice set to: {args.value}")
            elif resolved == "kokoro":
                state["VOICE_BRIDGE_KOKORO_VOICE"] = args.value
                write_state(state)
                print(f"Kokoro voice set to: {args.value}")
            else:
                print(f"Voice selection not available for engine: {resolved}")
                sys.exit(1)
        else:
            if resolved == "elevenlabs":
                voice = read_env_key("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
                print(f"Current ElevenLabs voice: {voice}")
                print("Browse voices at: https://elevenlabs.io/voice-library")
            elif resolved == "edge-tts":
                voice = state.get("VOICE_BRIDGE_EDGE_VOICE", "en-US-GuyNeural")
                print(f"Current edge-tts voice: {voice}")
                print("List voices: edge-tts --list-voices")
            elif resolved == "kokoro":
                voice = state.get("VOICE_BRIDGE_KOKORO_VOICE", "bm_lewis")
                print(f"Current Kokoro voice: {voice}")
            else:
                print(f"Voice selection not available for engine: {resolved}")

    elif args.command == "engine":
        from voice_bridge.engines import get_available_engines
        valid = list(get_available_engines().keys()) + ["auto"]
        if args.value:
            if args.value not in valid:
                print(f"Unknown engine: {args.value}")
                print(f"Options: {', '.join(valid)}")
                sys.exit(1)
            state["VOICE_BRIDGE_ENGINE"] = args.value
            write_state(state)
            print(f"Engine set to: {args.value}")
        else:
            current = state.get("VOICE_BRIDGE_ENGINE", "auto")
            print(f"Current engine: {current}")
            print(f"Options: {', '.join(valid)}")

    elif args.command == "speed":
        engine = state.get("VOICE_BRIDGE_ENGINE", "auto")
        # Resolve auto so speed works with the default engine
        from voice_bridge.engines import resolve_engine_name
        try:
            resolved = resolve_engine_name(engine)
        except (RuntimeError, ValueError):
            resolved = engine

        if args.value:
            if resolved == "edge-tts":
                # edge-tts accepts a percentage string like "+30%" or "-10%"
                import re
                if not re.match(r'^[+-]?\d+%$', args.value):
                    print(f"Invalid rate for edge-tts: {args.value} (use a percentage like +30% or -10%)")
                    sys.exit(1)
                state["VOICE_BRIDGE_EDGE_RATE"] = args.value
                write_state(state)
                print(f"Speed set to {args.value} for edge-tts")
            else:
                try:
                    speed = float(args.value)
                except ValueError:
                    print(f"Invalid speed: {args.value} (must be a number)")
                    sys.exit(1)
                if resolved == "elevenlabs":
                    if not (0.7 <= speed <= 1.2):
                        print(f"ElevenLabs speed must be 0.7-1.2 (got {speed})")
                        sys.exit(1)
                    state["VOICE_BRIDGE_ELEVENLABS_SPEED"] = str(speed)
                elif resolved == "kokoro":
                    if speed <= 0:
                        print(f"Kokoro speed must be positive (got {speed})")
                        sys.exit(1)
                    state["VOICE_BRIDGE_KOKORO_SPEED"] = str(speed)
                elif resolved in ("say", "espeak"):
                    if speed != int(speed):
                        print(f"{resolved} rate must be a whole number (words per minute), got {args.value}")
                        sys.exit(1)
                    wpm = int(speed)
                    if wpm < 1:
                        print(f"{resolved} rate must be positive (got {wpm})")
                        sys.exit(1)
                    state_key = "VOICE_BRIDGE_SAY_RATE" if resolved == "say" else "VOICE_BRIDGE_ESPEAK_RATE"
                    state[state_key] = str(wpm)
                else:
                    print(f"Speed control not available for engine: {resolved}")
                    sys.exit(1)
                write_state(state)
                print(f"Speed set to {int(speed) if resolved in ('say', 'espeak') else speed} for {resolved}")
        else:
            if resolved == "edge-tts":
                print(f"edge-tts rate: {state.get('VOICE_BRIDGE_EDGE_RATE', '+0%')} (e.g. +30%, -10%)")
            elif resolved == "elevenlabs":
                print(f"ElevenLabs speed: {state.get('VOICE_BRIDGE_ELEVENLABS_SPEED', '1.0')} (range: 0.7-1.2)")
            elif resolved == "kokoro":
                print(f"Kokoro speed: {state.get('VOICE_BRIDGE_KOKORO_SPEED', '1.4')}")
            elif resolved == "say":
                print(f"say rate: {state.get('VOICE_BRIDGE_SAY_RATE', '200')} words/min")
            elif resolved == "espeak":
                print(f"espeak rate: {state.get('VOICE_BRIDGE_ESPEAK_RATE', '175')} words/min")
            else:
                print(f"Speed control not available for engine: {resolved}")

    elif args.command == "voices":
        _list_voices(args.value, state, preview=args.preview,
                     gender=args.gender, locale=args.locale, sample=args.sample)

    elif args.command == "setup":
        from voice_bridge.setup_wizard import run_setup
        run_setup()


def _list_voices(engine_arg: str | None, state: dict[str, str],
                  preview=None, gender=None, locale=None, sample=None):
    """List available voices for an engine, with optional filtering and preview."""
    from voice_bridge.engines import resolve_engine_name

    engine_name = engine_arg or state.get("VOICE_BRIDGE_ENGINE", "auto")

    # For engines with fixed voice lists, show them even if the engine isn't installed
    if engine_name in ("kokoro",):
        resolved = engine_name
    else:
        try:
            resolved = resolve_engine_name(engine_name)
        except (RuntimeError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Single voice preview: --preview VOICE_NAME
    if preview and preview != "__all__":
        _preview_single_voice(resolved, preview)
        return

    do_preview = preview == "__all__"

    if resolved == "edge-tts":
        _list_edge_tts_voices(do_preview, gender, locale, sample)
    elif resolved == "elevenlabs":
        _list_elevenlabs_voices(do_preview, gender, sample)
    elif resolved == "kokoro":
        _list_kokoro_voices(do_preview, gender, sample)
    elif resolved == "say":
        _list_say_voices(do_preview, locale, sample)
    elif resolved == "espeak":
        _list_espeak_voices(do_preview)
    else:
        print(f"No voice listing for engine: {resolved}")


# --- Preview helpers ---

PREVIEW_PHRASE = "Hello, this is a preview of my voice."


def _preview_voice(engine_name: str, voice_name: str):
    """Speak a sample phrase with a specific voice."""
    from voice_bridge.config import TTSConfig
    config = TTSConfig()

    print(f"  >> Previewing {voice_name}...", end="", flush=True)
    try:
        if engine_name == "edge-tts":
            from voice_bridge.tts.edge_tts_engine import EdgeTTSEngine
            engine = EdgeTTSEngine(voice=voice_name, rate=config.edge_tts_rate)
        elif engine_name == "say":
            from voice_bridge.tts.macos_say import MacOSSayTTS
            engine = MacOSSayTTS(voice=voice_name, rate=config.say_rate)
        elif engine_name == "kokoro":
            from voice_bridge.tts.kokoro_engine import KokoroTTS
            engine = KokoroTTS(voice=voice_name, speed=config.kokoro_speed)
        else:
            from voice_bridge.engines import create_engine
            engine = create_engine(engine_name, config)
        engine.speak(PREVIEW_PHRASE)
        print(" done")
    except Exception as e:
        print(f" failed: {e}")


def _preview_single_voice(engine_name: str, voice_name: str):
    """Preview a single voice by name and exit."""
    _preview_voice(engine_name, voice_name)
    print(f"\nSet with: voice-bridge voice {voice_name}")


def _play_audio_file(path: str):
    """Play an audio file using the platform audio player."""
    import platform
    import shutil
    import subprocess

    system = platform.system()
    if system == "Darwin":
        cmd = ["afplay", path]
    elif system == "Linux":
        if shutil.which("mpv"):
            cmd = ["mpv", "--no-terminal", path]
        elif shutil.which("ffplay"):
            cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
        else:
            return
    elif system == "Windows":
        if shutil.which("ffplay"):
            cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
        elif shutil.which("mpv"):
            cmd = ["mpv", "--no-terminal", path]
        else:
            return
    else:
        return

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _interactive_preview(engine_name: str, voice_name: str) -> str:
    """Preview a voice and prompt for action. Returns 'next', 'select', or 'quit'."""
    _preview_voice(engine_name, voice_name)

    if not sys.stdin.isatty():
        return "next"

    try:
        choice = input("     [n]ext / [s]elect / [q]uit? ").strip().lower()
    except EOFError:
        return "quit"

    if choice in ("s", "select"):
        return "select"
    elif choice in ("q", "quit"):
        return "quit"
    return "next"


def _apply_sample(voices: list, sample: int | None) -> list:
    """Randomly sample N voices from a list."""
    if sample and sample < len(voices):
        import random
        return random.sample(voices, sample)
    return voices


def _preview_loop(engine_name: str, voices: list[tuple[str, str]], sample: int | None):
    """Run interactive preview over a list of (voice_name, display_label) tuples."""
    if not sys.stdin.isatty():
        print("\nPreview requires an interactive terminal.")
        return

    voices = _apply_sample(voices, sample)
    print(f"\nPreviewing {len(voices)} voice(s). Press Ctrl+C to cancel.\n")

    try:
        for voice_name, _ in voices:
            action = _interactive_preview(engine_name, voice_name)
            if action == "select":
                print(f"\n  Run: voice-bridge voice {voice_name}")
                return
            elif action == "quit":
                return
    except KeyboardInterrupt:
        print("\nPreview cancelled.")


# --- Engine-specific voice listing ---

def _list_edge_tts_voices(preview: bool = False, gender=None, locale=None, sample=None):
    """List edge-tts voices with optional filtering and preview."""
    try:
        import asyncio
        import edge_tts
    except ImportError:
        print("edge-tts not installed. Run: pip install ai-voice-bridge[edge]")
        return

    voices = asyncio.run(edge_tts.list_voices())
    en_voices = [v for v in voices if v["Locale"].startswith("en-")]

    # Apply filters
    if gender:
        en_voices = [v for v in en_voices if v["Gender"].lower() == gender.lower()]
    if locale:
        en_voices = [v for v in en_voices if v["Locale"].lower() == locale.lower()]

    en_voices.sort(key=lambda v: v["ShortName"])

    total = len(asyncio.run(edge_tts.list_voices()))
    filters = []
    if gender:
        filters.append(gender)
    if locale:
        filters.append(locale)
    filter_desc = f" ({', '.join(filters)})" if filters else " English"

    print(f"edge-tts{filter_desc} voices ({len(en_voices)} of {total} total):\n")
    for v in en_voices:
        print(f"  {v['ShortName']:40s} {v['Gender']}")
    print(f"\nSet with: voice-bridge voice <name>")

    if preview:
        voice_pairs = [(v["ShortName"], v["ShortName"]) for v in en_voices]
        _preview_loop("edge-tts", voice_pairs, sample)


def _list_elevenlabs_voices(preview: bool = False, gender=None, sample=None):
    """List ElevenLabs voices via API with optional preview using preview_url."""
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        print("ElevenLabs not installed. Run: pip install ai-voice-bridge[elevenlabs]")
        return

    import os
    from voice_bridge.state import read_env_key
    api_key = os.getenv("ELEVENLABS_API_KEY", "") or read_env_key("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("ElevenLabs API key not configured. Run: voice-bridge setup")
        return

    client = ElevenLabs(api_key=api_key)
    response = client.voices.get_all()
    voices = list(response.voices)

    if gender:
        voices = [v for v in voices
                  if hasattr(v, 'labels') and v.labels
                  and v.labels.get('gender', '').lower() == gender.lower()]

    print(f"ElevenLabs voices ({len(voices)}):\n")
    for v in voices:
        print(f"  {v.name:30s} ID: {v.voice_id}")
    print(f"\nSet with: voice-bridge voice <voice_id>")

    if preview:
        # Use preview_url if available (free, no API credits)
        if not sys.stdin.isatty():
            print("\nPreview requires an interactive terminal.")
            return

        voice_pairs = [(v.voice_id, v.name) for v in voices]
        voice_pairs = _apply_sample(voice_pairs, sample)
        voice_map = {v.voice_id: v for v in voices}

        print(f"\nPreviewing {len(voice_pairs)} voice(s). Press Ctrl+C to cancel.\n")
        try:
            for voice_id, display in voice_pairs:
                v = voice_map[voice_id]
                preview_url = getattr(v, 'preview_url', None)
                if preview_url:
                    _preview_elevenlabs_url(v.name, preview_url)
                else:
                    _preview_voice("elevenlabs", voice_id)

                if not sys.stdin.isatty():
                    continue
                try:
                    choice = input("     [n]ext / [s]elect / [q]uit? ").strip().lower()
                except EOFError:
                    break
                if choice in ("s", "select"):
                    print(f"\n  Run: voice-bridge voice {voice_id}")
                    return
                elif choice in ("q", "quit"):
                    return
        except KeyboardInterrupt:
            print("\nPreview cancelled.")


def _preview_elevenlabs_url(name: str, url: str):
    """Play an ElevenLabs voice preview from its pre-recorded sample URL."""
    import os
    import tempfile
    import urllib.request

    print(f"  >> Previewing {name}...", end="", flush=True)
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(tmp_fd)
        urllib.request.urlretrieve(url, tmp_path)
        _play_audio_file(tmp_path)
        print(" done")
    except Exception as e:
        print(f" failed: {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _list_kokoro_voices(preview: bool = False, gender=None, sample=None):
    """List bundled Kokoro voice names."""
    voices = [
        ("af_bella", "American Female"),
        ("af_nicole", "American Female"),
        ("af_sarah", "American Female"),
        ("af_sky", "American Female"),
        ("am_adam", "American Male"),
        ("am_michael", "American Male"),
        ("bf_emma", "British Female"),
        ("bf_isabella", "British Female"),
        ("bm_george", "British Male"),
        ("bm_lewis", "British Male"),
    ]

    if gender:
        g = gender.lower()
        voices = [(n, d) for n, d in voices if g in d.lower()]

    print("Kokoro voices:\n")
    for name, desc in voices:
        print(f"  {name:20s} {desc}")
    print(f"\nSet with: voice-bridge voice <name>")

    if preview:
        _preview_loop("kokoro", voices, sample)


def _list_say_voices(preview: bool = False, locale=None, sample=None):
    """List macOS say voices."""
    import subprocess
    try:
        result = subprocess.run(
            ["say", "-v", "?"], capture_output=True, text=True, timeout=5,
        )
    except Exception as e:
        print(f"Error listing voices: {e}")
        return

    all_voices = result.stdout.strip().splitlines()
    en_voices = [v for v in all_voices if "en_" in v or "en-" in v]

    if locale:
        # Normalize locale format: en-US -> en_US for matching
        loc = locale.replace("-", "_")
        en_voices = [v for v in en_voices if loc in v]

    parsed = []
    for v in en_voices:
        name = v.split()[0]
        rest = v[len(name):].strip()
        parsed.append((name, rest))

    print(f"macOS say English voices ({len(parsed)} of {len(all_voices)} total):\n")
    for name, rest in parsed:
        print(f"  {name:20s} {rest}")
    print(f"\nSet with: voice-bridge voice <name>")

    if preview:
        _preview_loop("say", parsed, sample)


def _list_espeak_voices(preview: bool = False):
    """List espeak-ng English voices."""
    import subprocess
    import shutil

    cmd = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
    try:
        result = subprocess.run(
            [cmd, "--voices=en"], capture_output=True, text=True, timeout=5,
        )
    except Exception as e:
        print(f"Error listing voices: {e}")
        return

    print("espeak English voices:\n")
    for line in result.stdout.strip().splitlines():
        print(f"  {line.strip()}")

    if preview:
        print()
        _preview_voice("espeak", "")
        print(f"\nSet with: voice-bridge voice <name>")


if __name__ == "__main__":
    main()
