"""Interactive first-run setup wizard for Voice Bridge."""

import platform
import shutil
import subprocess
import sys

from voice_bridge.paths import get_data_dir, get_env_file, get_state_file
from voice_bridge.engines import get_available_engines


def run_setup():
    """Interactive setup: detect platform, pick engine, test audio."""
    print("=" * 50)
    print("  Voice Bridge Setup")
    print("=" * 50)
    print()

    data_dir = get_data_dir()
    print(f"Data directory: {data_dir}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print()

    # Step 1: Show available engines
    available = get_available_engines()
    installed = {name: ok for name, ok in available.items() if ok}
    not_installed = {name: ok for name, ok in available.items() if not ok}

    print("Installed engines:")
    if installed:
        for name in installed:
            print(f"  + {name}")
    else:
        print("  (none)")
    print()

    if not_installed:
        print("Not installed (optional):")
        install_cmds = {
            "edge-tts": "pip install ai-voice-bridge[edge]",
            "elevenlabs": "pip install ai-voice-bridge[elevenlabs]",
            "kokoro": "pip install ai-voice-bridge[kokoro]",
            "say": "Only available on macOS",
            "espeak": "apt install espeak-ng (Linux) or brew install espeak (macOS)",
        }
        for name in not_installed:
            print(f"  - {name}: {install_cmds.get(name, '')}")
        print()

    # Step 2: Recommend an engine
    if not installed:
        print("No TTS engine available!")
        print()
        print("Recommended: Install edge-tts (free, 400+ voices, no API key):")
        print("  pip install ai-voice-bridge[edge]")
        print()
        print("Or install all engines:")
        print("  pip install ai-voice-bridge[all]")
        return

    # Pick default engine
    preference = ["edge-tts", "say", "espeak", "kokoro", "elevenlabs"]
    default_engine = next((e for e in preference if e in installed), list(installed.keys())[0])

    print(f"Recommended engine: {default_engine}")

    # Step 3: Test audio
    print()
    choice = input(f"Test audio with {default_engine}? [Y/n] ").strip().lower()
    if choice in ("", "y", "yes"):
        print(f"Speaking test phrase with {default_engine}...")
        try:
            from voice_bridge.engines import create_engine
            engine = create_engine(default_engine)
            engine.speak("Voice bridge is working. Setup complete.")
            print("Audio test passed!")
        except Exception as e:
            print(f"Audio test failed: {e}")
            print("You may need to check your audio output settings.")
    print()

    # Step 4: ElevenLabs API key (if installed)
    if "elevenlabs" in installed:
        env_file = get_env_file()
        has_key = False
        if env_file.exists():
            content = env_file.read_text()
            has_key = "ELEVENLABS_API_KEY=" in content and "your-api-key" not in content

        if not has_key:
            print("ElevenLabs detected. To use it, add your API key:")
            choice = input("Enter ElevenLabs API key (or press Enter to skip): ").strip()
            if choice:
                lines = env_file.read_text().splitlines() if env_file.exists() else []
                found = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("ELEVENLABS_API_KEY="):
                        lines[i] = f"ELEVENLABS_API_KEY={choice}"
                        found = True
                        break
                if not found:
                    lines.append(f"ELEVENLABS_API_KEY={choice}")
                env_file.write_text("\n".join(lines) + "\n")
                print("API key saved.")
            print()

    # Step 5: Write state
    state_file = get_state_file()
    state_lines = []
    if state_file.exists():
        state_lines = state_file.read_text().splitlines()

    # Set engine if not already set
    has_engine = any(l.startswith("VOICE_BRIDGE_ENGINE=") for l in state_lines)
    if not has_engine:
        state_lines.append(f"VOICE_BRIDGE_ENGINE={default_engine}")

    has_mode = any(l.startswith("VOICE_BRIDGE_MODE=") for l in state_lines)
    if not has_mode:
        state_lines.append("VOICE_BRIDGE_MODE=off")

    state_file.write_text("\n".join(state_lines) + "\n")

    # Step 6: Claude Code hook instructions
    print("=" * 50)
    print("  Setup Complete!")
    print("=" * 50)
    print()
    print(f"Engine: {default_engine}")
    print(f"Config: {data_dir}")
    print()
    print("Quick start:")
    print('  voice-bridge test      # Test audio')
    print('  voice-bridge on        # Always-on mode')
    print('  voice-bridge status    # Show status')
    print()
    print("Claude Code integration (pick one):")
    print()
    print("  Option 1 -- Plugin (recommended):")
    print("    claude plugin marketplace add Tomorrow-You/voice-bridge")
    print("    claude plugin install voice-bridge@voice-bridge")
    print()
    print("  Option 2 -- Manual hook:")
    print("    See https://github.com/Tomorrow-You/voice-bridge#option-2-manual-hook-setup")
    print()
    print("For full docs, see: https://github.com/Tomorrow-You/voice-bridge")
