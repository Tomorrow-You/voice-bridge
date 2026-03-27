# ai-voice-bridge

npm shim for the [Voice Bridge](https://github.com/Tomorrow-You/voice-bridge) MCP server — multi-engine TTS for AI coding assistants.

## What this package does

This is a thin Node.js wrapper that bootstraps the Python-based Voice Bridge MCP server. When you run `npx ai-voice-bridge`, it:

1. Finds Python 3.10+ on your system
2. Installs the `ai-voice-bridge[mcp]` pip package if not already present
3. Launches the MCP server connected to stdio

## Requirements

- **Node.js 16+** (for npx)
- **Python 3.10+** with **pip**
- **Audio player**: macOS has `afplay` built-in. Linux needs `mpv` or `ffmpeg`. Windows needs `ffmpeg` or `mpv`.
- **Audio output hardware**: speakers or headphones on the local machine

**Not supported**: headless servers, Docker containers, SSH sessions, and CI runners lack audio output. The MCP server will start, but `speak` commands will fail silently.

## Usage

### Claude Desktop / Cursor

Add to your MCP config:

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

### Claude Code

```bash
claude mcp add voice-bridge -- npx ai-voice-bridge
```

## Troubleshooting

The shim prints diagnostic warnings to stderr on startup:

- **`ERROR: Python 3.10+ is required`** — Install Python with platform-specific instructions shown in the error
- **`ERROR: Found Python 3.x, but Python 3.10+ is required`** — Upgrade your Python installation
- **`ERROR: pip is not available`** — Install pip (e.g., `sudo apt install python3-pip` on Ubuntu)
- **`WARNING: No audio player detected`** — Install `mpv` or `ffmpeg` for audio playback
- **`WARNING: No display server or PulseAudio detected`** — You're likely in a headless environment where audio cannot play

## License

MIT. See the [main repository](https://github.com/Tomorrow-You/voice-bridge) for details.
