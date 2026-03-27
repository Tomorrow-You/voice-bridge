# Voice Bridge Plugin for Claude Code

Give Claude Code a voice. Speaks responses aloud using multi-engine TTS.

## What it does

- **Stop hook**: Automatically speaks responses when you prefix messages with "speak" or enable always-on mode
- **MCP server**: Exposes `speak`, `set_engine`, `get_status`, and `list_voices` tools
- **Auto-install**: Installs `ai-voice-bridge` on first session if not present

## Install

```bash
claude plugin install voice-bridge@Tomorrow-You/voice-bridge
```

Or test locally:

```bash
claude --plugin-dir ./claude-plugin
```

## Usage

After installation:

```bash
voice-bridge test        # Verify audio works
voice-bridge on          # Always-on mode (every response spoken)
voice-bridge off         # Single-turn mode (default)
voice-bridge voices      # List available voices
voice-bridge engines     # Show all engines with install status
```

In single-turn mode, start your message with "speak" to hear the response.

### Speed control

```bash
voice-bridge speed           # Show current speed
voice-bridge speed +30%      # edge-tts: 30% faster
voice-bridge speed 250       # say/espeak: words per minute
voice-bridge speed 1.1       # elevenlabs/kokoro: multiplier
```

### Hook behavior

The Stop hook runs in the background and:
- Truncates responses to 2,000 characters before speaking
- Falls back through engines if the configured one fails (configured > espeak > say)
- Logs to `~/.voice-bridge/voice-bridge.log`

## Engines

Auto-detection priority: edge-tts > say > espeak > kokoro > elevenlabs.

| Engine | Cost | Setup |
|--------|------|-------|
| edge-tts | Free | Installed automatically |
| say | Free | macOS built-in |
| espeak | Free | Linux built-in |
| kokoro | Free (English only) | `pip install ai-voice-bridge[kokoro]` |
| elevenlabs | Paid | `pip install ai-voice-bridge[elevenlabs]` + API key |

Requires a local machine with audio output. Headless servers, containers, and SSH sessions cannot play audio.
