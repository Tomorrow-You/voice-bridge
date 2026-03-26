# Voice Bridge

**Give your AI coding assistant a voice.** Multi-engine TTS that works with Claude Code, Cursor, and VS Code. Free, local-first, works in 60 seconds.

```bash
pip install ai-voice-bridge[edge]
voice-bridge test
```

That's it. Your terminal can talk now.

## Why Voice Bridge?

AI coding assistants generate walls of text. Voice Bridge speaks the important parts aloud so you can keep your eyes on the code.

- **Free by default** -- edge-tts uses Microsoft Neural voices, no API key needed
- **5 engines** -- edge-tts, ElevenLabs, Kokoro (local ONNX), macOS say, espeak-ng
- **Safe** -- strips code blocks, API keys, file paths, and markdown before speaking
- **Non-blocking** -- audio plays in the background, doesn't slow your workflow
- **Claude Code native** -- Stop hook integration speaks responses automatically

## Quick Start

### Install

```bash
# Recommended: edge-tts (free, 400+ voices)
pip install ai-voice-bridge[edge]

# Or with all engines
pip install ai-voice-bridge[all]

# Or minimal (macOS say / Linux espeak only)
pip install ai-voice-bridge
```

### Test

```bash
voice-bridge test          # Speak a test phrase
voice-bridge engines       # List available engines
voice-bridge setup         # Interactive setup wizard
```

### Use

```bash
# Pipe text to speech
echo "Hello world" | vb-speak

# Choose an engine
echo "Hello" | vb-speak --engine edge-tts
echo "Hello" | vb-speak --engine say

# Modes
voice-bridge on            # Always-on: every AI response spoken
voice-bridge off           # Off: use "speak" keyword for single responses
voice-bridge status        # Show current mode and engine
```

## Claude Code Integration

Voice Bridge integrates with Claude Code via a Stop hook that fires after every response.

### Option 1: Manual Hook Setup

Add to your `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'VB_HOOK=$(python3 -c \"import voice_bridge; import pathlib; print(pathlib.Path(voice_bridge.__file__).parent / \\\"integrations\\\" / \\\"claude_hook.sh\\\")\" 2>/dev/null) && [ -f \"$VB_HOOK\" ] && bash \"$VB_HOOK\"'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Then add to your `CLAUDE.md`:

```markdown
## Voice Bridge (TTS)
- **NEVER** use `<speak>` tags unless the user's message starts with "speak"
- When user starts with "speak", wrap your ENTIRE response in `<speak>...</speak>` tags
- Strip the "speak" keyword before processing
- Inside tags, write naturally -- no markdown, code blocks, or file paths
```

### Option 2: Always-On Mode

Skip the `<speak>` tag convention entirely:

```bash
voice-bridge on
```

Now every Claude response is spoken automatically. Toggle off with `voice-bridge off`.

## Engines

| Engine | Cost | Quality | Setup | Platform |
|--------|------|---------|-------|----------|
| **edge-tts** | Free | High (neural) | `pip install ai-voice-bridge[edge]` | All |
| **ElevenLabs** | Paid | Highest | `pip install ai-voice-bridge[elevenlabs]` + API key | All |
| **Kokoro** | Free | Good | `pip install ai-voice-bridge[kokoro]` + model download | All |
| **say** | Free | Basic | Built-in | macOS |
| **espeak** | Free | Basic | `apt install espeak-ng` | Linux |

### Switching Engines

```bash
voice-bridge engine edge-tts     # Free neural voices
voice-bridge engine elevenlabs   # Premium cloud
voice-bridge engine kokoro       # Local offline
voice-bridge engine say          # macOS built-in
voice-bridge engine espeak       # Linux built-in
voice-bridge engine auto         # Best available (default)
```

### ElevenLabs Setup

```bash
pip install ai-voice-bridge[elevenlabs]
cp $(python3 -c "import voice_bridge.paths; print(voice_bridge.paths.get_data_dir())")/.env.example \
   $(python3 -c "import voice_bridge.paths; print(voice_bridge.paths.get_data_dir())")/.env
# Edit .env with your API key from https://elevenlabs.io/app/settings/api-keys
voice-bridge engine elevenlabs
voice-bridge test
```

### Kokoro Setup (Offline)

```bash
pip install ai-voice-bridge[kokoro]
# Download model files (~200MB) from:
# https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
# Place in: ~/.voice-bridge/models/ (or $VOICE_BRIDGE_HOME/models/)
voice-bridge engine kokoro
voice-bridge test
```

## Configuration

Voice Bridge stores configuration in `~/.voice-bridge/` (macOS), `~/.local/share/voice-bridge/` (Linux), or `%APPDATA%\voice-bridge\` (Windows).

Override with the `VOICE_BRIDGE_HOME` environment variable.

| File | Purpose |
|------|---------|
| `.env` | API keys (ElevenLabs) |
| `.state` | Runtime state (mode, engine, speed) |
| `models/` | Kokoro ONNX model files |

## Text Safety Filter

Before any text reaches the TTS engine, Voice Bridge strips:

- Code blocks and inline code
- API keys and secrets (OpenAI, GitHub, AWS, PEM keys)
- File paths and URLs
- Markdown formatting (tables, headers, bold/italic, lists)

Text is truncated to 4,000 characters at a sentence boundary.

## CLI Reference

```bash
# Control
voice-bridge on              # Always-on mode
voice-bridge off             # Single-turn mode (default)
voice-bridge status          # Show mode, engine, config
voice-bridge test            # Test audio output
voice-bridge engines         # List all engines with install status
voice-bridge setup           # Interactive setup wizard

# Engine config
voice-bridge engine [name]   # Get/set engine
voice-bridge voice [id]      # Set ElevenLabs voice ID
voice-bridge speed [val]     # Set engine speed

# Pipe to speech
echo "text" | vb-speak                    # Default engine
echo "text" | vb-speak --engine edge-tts  # Specific engine
echo "text" | vb-speak --stream           # Stream sentence-by-sentence
echo "text" | vb-speak --dry-run          # Print filtered text only
```

## Development

```bash
git clone https://github.com/Tomorrow-You/voice-bridge.git
cd voice-bridge
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[all,dev]"
pytest
```

## License

MIT. See [LICENSE](LICENSE) for details.

The `edge-tts` optional dependency is licensed under GPL-3.0. It is not included in the base install.
