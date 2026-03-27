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
```

In single-turn mode, start your message with "speak" to hear the response.

## Engines

| Engine | Cost | Setup |
|--------|------|-------|
| edge-tts | Free | Installed automatically |
| say | Free | macOS built-in |
| espeak | Free | Linux built-in |
| kokoro | Free | `pip install ai-voice-bridge[kokoro]` |
| elevenlabs | Paid | `pip install ai-voice-bridge[elevenlabs]` + API key |
