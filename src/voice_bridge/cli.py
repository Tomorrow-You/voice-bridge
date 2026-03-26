"""
voice-bridge: Control the voice bridge.

Usage:
    voice-bridge on           # Always-on mode (every response gets TTS)
    voice-bridge off          # Disable always-on (single-turn "speak" still works)
    voice-bridge status       # Show current mode, engine, available engines
    voice-bridge test         # Speak a test phrase
    voice-bridge engine [name]  # Get/set engine
    voice-bridge voice [id]   # Set ElevenLabs voice
    voice-bridge speed [val]  # Set engine speed
    voice-bridge setup        # Interactive first-run setup
    voice-bridge engines      # List available engines

Modes:
    off      -- TTS only when user types "speak" keyword (single-turn)
    always   -- TTS on every Claude response
"""
import argparse
import sys

from voice_bridge.paths import get_state_file, get_env_file


def _read_state() -> dict[str, str]:
    """Read shell-sourceable state file."""
    state = {}
    state_file = get_state_file()
    if state_file.exists():
        for line in state_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                state[key.strip()] = val.strip()
    return state


def _write_state(state: dict[str, str]) -> None:
    """Write shell-sourceable state file."""
    state_file = get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in sorted(state.items())]
    state_file.write_text("\n".join(lines) + "\n")


def _read_env_key(key: str, default: str = "") -> str:
    """Read a single key from .env without parsing the whole file."""
    env_file = get_env_file()
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip().startswith(f"{key}="):
                return line.strip().split("=", 1)[1]
    return default


def main():
    parser = argparse.ArgumentParser(
        description="Voice Bridge -- multi-engine TTS for AI coding assistants",
        epilog='Modes: "off" = single-turn only (type "speak" keyword), "always" = every response',
    )
    parser.add_argument(
        "command",
        choices=["on", "off", "status", "test", "voice", "engine", "engines", "speed", "setup"],
        help="Command to run",
    )
    parser.add_argument("value", nargs="?", help="Value for voice/engine/speed commands")
    args = parser.parse_args()

    state = _read_state()

    if args.command == "on":
        state["VOICE_BRIDGE_MODE"] = "always"
        _write_state(state)
        print("Voice bridge: ALWAYS ON (every response will be spoken)")
        print('To speak a single response instead, type "speak" before your message.')

    elif args.command == "off":
        state["VOICE_BRIDGE_MODE"] = "off"
        _write_state(state)
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

        if engine == "elevenlabs" or (engine == "auto" and "elevenlabs" in installed):
            print(f"ElevenLabs speed: {state.get('VOICE_BRIDGE_ELEVENLABS_SPEED', '1.0')}")
        if engine == "kokoro" or (engine == "auto" and "kokoro" in installed):
            print(f"Kokoro speed: {state.get('VOICE_BRIDGE_KOKORO_SPEED', '1.4')}")

    elif args.command == "engines":
        from voice_bridge.engines import get_available_engines
        available = get_available_engines()
        print("Available TTS engines:\n")
        engine_info = {
            "edge-tts": ("Free, 400+ voices, cross-platform", "pip install voice-bridge[edge]"),
            "elevenlabs": ("Cloud, highest quality, paid", "pip install voice-bridge[elevenlabs]"),
            "kokoro": ("Local, free, offline (82M ONNX model)", "pip install voice-bridge[kokoro]"),
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
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "voice":
        env_file = get_env_file()
        if args.value:
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
        else:
            voice = _read_env_key("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
            print(f"Current ElevenLabs voice: {voice}")
            print("Browse voices at: https://elevenlabs.io/voice-library")

    elif args.command == "engine":
        from voice_bridge.engines import get_available_engines
        valid = list(get_available_engines().keys()) + ["auto"]
        if args.value:
            if args.value not in valid:
                print(f"Unknown engine: {args.value}")
                print(f"Options: {', '.join(valid)}")
                sys.exit(1)
            state["VOICE_BRIDGE_ENGINE"] = args.value
            _write_state(state)
            print(f"Engine set to: {args.value}")
        else:
            current = state.get("VOICE_BRIDGE_ENGINE", "auto")
            print(f"Current engine: {current}")
            print(f"Options: {', '.join(valid)}")

    elif args.command == "speed":
        engine = state.get("VOICE_BRIDGE_ENGINE", "auto")
        if args.value:
            try:
                speed = float(args.value)
            except ValueError:
                print(f"Invalid speed: {args.value} (must be a number)")
                sys.exit(1)
            if engine == "elevenlabs":
                if not (0.7 <= speed <= 1.2):
                    print(f"ElevenLabs speed must be 0.7-1.2 (got {speed})")
                    sys.exit(1)
                state["VOICE_BRIDGE_ELEVENLABS_SPEED"] = str(speed)
            elif engine == "kokoro":
                if speed <= 0:
                    print(f"Kokoro speed must be positive (got {speed})")
                    sys.exit(1)
                state["VOICE_BRIDGE_KOKORO_SPEED"] = str(speed)
            else:
                print(f"Speed control not available for engine: {engine}")
                sys.exit(1)
            _write_state(state)
            print(f"Speed set to {speed} for {engine}")
        else:
            if engine == "elevenlabs":
                print(f"ElevenLabs speed: {state.get('VOICE_BRIDGE_ELEVENLABS_SPEED', '1.0')} (range: 0.7-1.2)")
            elif engine == "kokoro":
                print(f"Kokoro speed: {state.get('VOICE_BRIDGE_KOKORO_SPEED', '1.4')}")
            else:
                print(f"Speed control not available for engine: {engine}")

    elif args.command == "setup":
        from voice_bridge.setup_wizard import run_setup
        run_setup()


if __name__ == "__main__":
    main()
