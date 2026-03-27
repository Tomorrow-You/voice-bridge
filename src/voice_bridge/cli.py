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
    voice-bridge voices [engine]  # List available voices for an engine

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
        _list_voices(args.value, state)

    elif args.command == "setup":
        from voice_bridge.setup_wizard import run_setup
        run_setup()


def _list_voices(engine_arg: str | None, state: dict[str, str]):
    """List available voices for an engine."""
    from voice_bridge.engines import resolve_engine_name, get_available_engines

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

    if resolved == "edge-tts":
        _list_edge_tts_voices()
    elif resolved == "elevenlabs":
        _list_elevenlabs_voices()
    elif resolved == "kokoro":
        _list_kokoro_voices()
    elif resolved == "say":
        _list_say_voices()
    elif resolved == "espeak":
        _list_espeak_voices()
    else:
        print(f"No voice listing for engine: {resolved}")


def _list_edge_tts_voices():
    """List edge-tts voices, English by default."""
    try:
        import asyncio
        import edge_tts
    except ImportError:
        print("edge-tts not installed. Run: pip install ai-voice-bridge[edge]")
        return

    voices = asyncio.run(edge_tts.list_voices())
    en_voices = [v for v in voices if v["Locale"].startswith("en-")]
    en_voices.sort(key=lambda v: v["ShortName"])

    print(f"edge-tts English voices ({len(en_voices)} of {len(voices)} total):\n")
    for v in en_voices:
        print(f"  {v['ShortName']:40s} {v['Gender']}")
    print(f"\nSet with: voice-bridge voice <name>")


def _list_elevenlabs_voices():
    """List ElevenLabs voices via API."""
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

    print(f"ElevenLabs voices ({len(response.voices)}):\n")
    for v in response.voices:
        print(f"  {v.name:30s} ID: {v.voice_id}")
    print(f"\nSet with: voice-bridge voice <voice_id>")


def _list_kokoro_voices():
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
    print("Kokoro voices:\n")
    for name, desc in voices:
        print(f"  {name:20s} {desc}")
    print(f"\nSet with: voice-bridge voice <name>")


def _list_say_voices():
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

    print(f"macOS say English voices ({len(en_voices)} of {len(all_voices)} total):\n")
    for v in en_voices:
        # Format: "Name  lang  # description"
        name = v.split()[0]
        rest = v[len(name):].strip()
        print(f"  {name:20s} {rest}")
    print(f"\nSet with: voice-bridge voice <name>")


def _list_espeak_voices():
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


if __name__ == "__main__":
    main()
