# Voice Bridge

<!-- mcp-name: io.github.dwarmerdam/voice-bridge -->

[![PyPI](https://img.shields.io/pypi/v/ai-voice-bridge)](https://pypi.org/project/ai-voice-bridge/)
[![CI](https://github.com/Tomorrow-You/voice-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/Tomorrow-You/voice-bridge/actions)

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

## Prerequisites

Voice Bridge is a **Python package** that plays audio on your **local machine**. It requires:

| Requirement | Details |
|---|---|
| **Python 3.10+** | `python3 --version` to check |
| **pip** | Usually bundled with Python. On some Linux distros: `sudo apt install python3-pip` |
| **Audio output** | Speakers or headphones — audio plays locally, not over a network |
| **Audio player** (Linux/Windows) | **macOS**: built-in (`afplay`). **Linux**: `mpv` (preferred) or `ffplay`. **Windows**: `ffplay` (preferred) or `mpv` |

Audio player fallback order: macOS uses `afplay` (always available). Linux tries `mpv` then `ffplay`. Windows tries `ffplay` then `mpv`.

> **Not supported**: headless servers, Docker containers, SSH sessions, and CI runners typically lack audio output. Voice Bridge will install and run the MCP server, but `speak` commands will fail silently without an audio player and sound hardware.

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

The setup wizard walks you through: detecting installed engines, testing audio output, optionally entering an ElevenLabs API key (if the SDK is installed), writing default state, and showing Claude Code integration options.

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

### Option 1: Install as a Plugin (Recommended)

```bash
claude plugin marketplace add Tomorrow-You/voice-bridge
claude plugin install voice-bridge@voice-bridge
```

This installs the plugin with a Stop hook (auto-speaks responses), the `/speak` skill, and the MCP server. Auto-installs `ai-voice-bridge[edge,mcp]` on first session.

### Option 2: Manual Hook Setup

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

### Hook Details

The Stop hook runs in the background so it doesn't block Claude Code. It:

- Extracts text from `<speak>` tags (single-turn mode) or the full response (always-on mode)
- Truncates to 2,000 characters before speaking
- Uses a fallback chain: configured engine > espeak > say
- Logs to `~/.voice-bridge/voice-bridge.log` (auto-rotated at 1MB, keeps 2 backups)
- Runs `vb-speak --stream` for sentence-by-sentence playback

## Engines

| Engine | Cost | Quality | Setup | Platform | Default voice |
|--------|------|---------|-------|----------|---------------|
| **edge-tts** | Free | High (neural) | `pip install ai-voice-bridge[edge]` | All | `en-US-GuyNeural` |
| **ElevenLabs** | Paid | Highest | `pip install ai-voice-bridge[elevenlabs]` + API key | All | George (`JBFqnCBsd6RMkjVDRZzb`), model `eleven_flash_v2_5` |
| **Kokoro** | Free | Good | `pip install ai-voice-bridge[kokoro]` + model download | All (English only) | `bm_lewis` |
| **say** | Free | Basic | Built-in | macOS | `Samantha` |
| **espeak** | Free | Basic | `apt install espeak-ng` | Linux | `en` |

When engine is set to `auto` (default), Voice Bridge picks the first available in this order: edge-tts > say > espeak > kokoro > elevenlabs. ElevenLabs is only considered "available" if the SDK is installed AND a valid API key is configured -- it will never be auto-selected without credentials.

### Discovering Voices

```bash
voice-bridge voices              # List voices for current engine
voice-bridge voices edge-tts     # List voices for a specific engine

# Filter by gender and/or locale
voice-bridge voices edge-tts --gender Female --locale en-US

# Preview a specific voice
voice-bridge voices edge-tts --preview en-US-AriaNeural

# Interactively audition voices (next/select/quit after each)
voice-bridge voices edge-tts --gender Female --locale en-US --preview

# Random sample of 3 voices
voice-bridge voices edge-tts --sample 3 --preview
```

Filtering options: `--gender` (Male/Female) works with edge-tts and kokoro. `--locale` (e.g. en-US, en-GB) works with edge-tts and say. `--sample N` picks N random voices. All combine with `--preview` for interactive audition.

ElevenLabs preview uses free pre-recorded samples when available (no API credits consumed).

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
voice-bridge setup  # Prompts for your ElevenLabs API key
# Or manually: create ~/.voice-bridge/.env with ELEVENLABS_API_KEY=your-key
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

Voice Bridge stores configuration in `~/.voice-bridge/` (macOS), `~/.local/share/voice-bridge/` (Linux, respects `XDG_DATA_HOME`), or `%APPDATA%\voice-bridge\` (Windows).

Override with the `VOICE_BRIDGE_HOME` environment variable.

| File | Purpose |
|------|---------|
| `.env` | API keys (ElevenLabs) |
| `.state` | Runtime state (mode, engine, speed, voice) |
| `models/` | Kokoro ONNX model files |
| `voice-bridge.log` | Hook execution logs (auto-rotated at 1MB, 2 backups) |

### State Variables

The `.state` file is a shell-sourceable key-value file. All values are optional — defaults apply if unset.

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_BRIDGE_MODE` | `off` | Mode: `off` (single-turn) or `always` (always-on) |
| `VOICE_BRIDGE_ENGINE` | `auto` | Engine name or `auto` |
| `VOICE_BRIDGE_EDGE_VOICE` | `en-US-GuyNeural` | edge-tts voice |
| `VOICE_BRIDGE_EDGE_RATE` | `+0%` | edge-tts rate (e.g. `+30%`, `-10%`) |
| `VOICE_BRIDGE_ELEVENLABS_SPEED` | `1.0` | ElevenLabs speed (0.7–1.2) |
| `VOICE_BRIDGE_KOKORO_VOICE` | `bm_lewis` | Kokoro voice name |
| `VOICE_BRIDGE_KOKORO_SPEED` | `1.4` | Kokoro speed multiplier |
| `VOICE_BRIDGE_SAY_RATE` | `200` | macOS say words per minute |
| `VOICE_BRIDGE_ESPEAK_RATE` | `175` | espeak words per minute |

## Text Safety Filter

Before any text reaches the TTS engine, Voice Bridge strips:

- **Code blocks** (fenced ` ``` ` and inline `` ` ``)
- **Secrets**: OpenAI/Anthropic keys (`sk-...`), GitHub tokens (`ghp_`, `gho_`), AWS keys (`AKIA...`), PEM private keys, 64+ char hex strings
- **File paths**: Unix (`/Users/...`, `/home/...`) and Windows (`C:\Users\...`)
- **URLs**: `http://` and `https://`
- **Markdown**: headers, bold/italic markers, list bullets, table rows

Text is truncated to 4,000 characters at the nearest sentence boundary (`. `). The Claude hook applies a separate 2,000 character limit before passing text to `vb-speak`.

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
voice-bridge voice [id]      # Set voice for current engine
voice-bridge voices [engine] # List available voices
voice-bridge speed [val]     # Set engine speed (see below)

# Voice discovery
voice-bridge voices edge-tts --gender Female --locale en-US  # Filter
voice-bridge voices edge-tts --preview en-US-AriaNeural      # Preview one
voice-bridge voices edge-tts --gender Female --preview       # Interactive
voice-bridge voices edge-tts --sample 3 --preview            # Random sample

# Pipe to speech
echo "text" | vb-speak                    # Default engine
echo "text" | vb-speak --engine edge-tts  # Specific engine
echo "text" | vb-speak --voice Aria       # Override voice for this call
echo "text" | vb-speak --stream           # Stream sentence-by-sentence
echo "text" | vb-speak --dry-run          # Print filtered text only
```

**Streaming mode** (`--stream`): reads stdin, splits text at sentence boundaries (`. `, `! `, `? `), and speaks each sentence as it completes. For edge-tts, sentences are queued so the next one generates while the current one plays.

### Speed Control

Each engine accepts a different speed format:

| Engine | Format | Default | Example |
|--------|--------|---------|---------|
| **edge-tts** | Percentage string | `+0%` | `voice-bridge speed +30%` |
| **elevenlabs** | Float (0.7–1.2) | `1.0` | `voice-bridge speed 1.1` |
| **kokoro** | Positive float | `1.4` | `voice-bridge speed 1.8` |
| **say** | Words per minute | `200` | `voice-bridge speed 250` |
| **espeak** | Words per minute | `175` | `voice-bridge speed 220` |

Speed applies to whichever engine is currently active. Check with `voice-bridge speed` (no value).

## MCP Server

Voice Bridge includes an MCP (Model Context Protocol) server so any MCP-compatible tool can speak text aloud.

> **npm shim (`npx ai-voice-bridge`)**: The npm package is a thin wrapper that auto-installs the Python package. It requires Python 3.10+ and pip on your `PATH`. On startup it checks for audio players and warns if none are found. See [Prerequisites](#prerequisites) for full requirements.

### Setup with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "voice-bridge": {
      "command": "python3",
      "args": ["-m", "voice_bridge.mcp.server"]
    }
  }
}
```

Or after npm publish, use the npm shim:

```json
{
  "mcpServers": {
    "voice-bridge": {
      "command": "npx",
      "args": ["ai-voice-bridge"]
    }
  }
}
```

### Setup with Cursor / VS Code

Add the same MCP server config in your editor's MCP settings. The config format is the same as Claude Desktop.

### Setup with Claude Code

```bash
claude mcp add voice-bridge -- python3 -m voice_bridge.mcp.server
```

### MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `speak` | `text` (required), `engine` (optional) | Speak text aloud. Optionally override engine for this call. |
| `set_engine` | `name` (required) | Switch the default TTS engine (`auto`, `edge-tts`, `elevenlabs`, `kokoro`, `say`, `espeak`) |
| `get_status` | _(none)_ | Show current mode, engine, and available engines |
| `list_voices` | `engine` (optional) | List available voices. Defaults to current engine if omitted. |

### Install with MCP support

```bash
pip install ai-voice-bridge[mcp]
```

This installs the `voice-bridge-mcp` command as an alternative to `python3 -m voice_bridge.mcp.server`.

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
