# Voice Bridge -- Handoff Document

This document explains exactly what has been built, how it works, and what remains. Written for a developer (or Claude session) picking this up cold.

## What This Is

Voice Bridge is an open-source Python package that gives AI coding assistants (Claude Code, Cursor, VS Code) a voice. It speaks AI responses aloud using one of 5 TTS engines. The PyPI package name is `ai-voice-bridge`. The GitHub repo is `Tomorrow-You/voice-bridge`.

**Current state:** v0.1.0 is published on [PyPI](https://pypi.org/project/ai-voice-bridge/) and pushed to GitHub with passing CI. Includes MCP server support. Not yet published to any plugin marketplace.

---

## What Has Been Built (Phase 0 + Phase 1)

### Repository

- **GitHub:** https://github.com/Tomorrow-You/voice-bridge
- **6 commits** on `main`, CI green
- **39 tracked files**, ~2,100 lines of code
- **73 tests** (69 pass, 4 skip for optional deps)

### Package Architecture

```
ai-voice-bridge (PyPI name)
  voice_bridge (Python import name)
    paths.py          -- XDG-aware data dir resolution (macOS/Linux/Windows)
    state.py          -- Shared .state file reader/writer (shell-safe quoting)
    config.py         -- Pydantic config, lazy dotenv loading
    engines.py        -- Engine registry, auto-detection, graceful fallback
    cli.py            -- voice-bridge CLI (on/off/status/test/engine/voice/speed/setup/engines)
    speak.py          -- vb-speak pipe-to-speech CLI
    text_filter.py    -- Safety filter (code, secrets, paths, URLs, markdown)
    setup_wizard.py   -- Interactive first-run setup
    __init__.py       -- Version, lazy logging setup
    py.typed          -- PEP 561 type checking marker
    tts/
      base.py             -- TTSEngine ABC + TextSource type alias
      sentence_splitter.py -- Shared sentence boundary splitting (used by all engines)
      edge_tts_engine.py  -- Free Microsoft Neural TTS (400+ voices, no API key)
      elevenlabs_engine.py -- Cloud TTS (paid, highest quality)
      kokoro_engine.py    -- Local ONNX model (free, offline, 82M params)
      macos_say.py        -- macOS built-in (zero deps)
      espeak_engine.py    -- Linux built-in (espeak-ng)
    integrations/
      claude_hook.sh        -- Claude Code Stop hook (bash + inline Python)
      claude_instructions.md -- CLAUDE.md snippet for <speak> tag convention
```

### Key Design Decisions Already Made

1. **Base install is lightweight** -- only `pydantic` + `python-dotenv`. Heavy deps (`sounddevice`, `numpy`, `elevenlabs`, `kokoro-onnx`, `edge-tts`) are optional extras.
2. **Engine auto-detection** -- `auto` resolves to the best available engine. Preference order: edge-tts > say > espeak > kokoro > elevenlabs.
3. **ElevenLabs availability check** -- engine is only marked "available" if the SDK is installed AND an API key is configured. Prevents auto-select from choosing it and failing.
4. **No module-level side effects** -- `import voice_bridge` creates no files, opens no handles, loads no dotenv. Everything is lazy.
5. **Shell-safe state file** -- values are double-quoted so the bash hook can `source .state` safely.
6. **Sentence splitting is shared** -- `sentence_splitter.py` is used by all 5 engines. Consistent behavior, single place to fix bugs.
7. **Text via stdin** -- `say` and `espeak` receive text via stdin pipe, not CLI args, to avoid ARG_MAX overflow.
8. **asyncio.run() safety** -- edge-tts engine detects existing event loops (Jupyter, MCP) and runs in a separate thread.
9. **Temp file cleanup** -- edge-tts MP3 files are cleaned up in a `finally` block.

### What Works Right Now

```bash
# From the local clone:
cd voice-bridge
source .venv/bin/activate

# CLI tools
voice-bridge test          # Speaks test phrase with auto-detected engine
voice-bridge status        # Shows mode, engine, available engines
voice-bridge engines       # Lists all 5 engines with install status
voice-bridge engine edge-tts  # Switch engine
voice-bridge on            # Always-on mode
voice-bridge off           # Single-turn mode
voice-bridge voice         # Show/set voice for current engine
voice-bridge speed 1.1     # Set speed (elevenlabs/kokoro)
voice-bridge setup         # Interactive setup wizard

# Pipe to speech
echo "Hello world" | vb-speak
echo "Hello" | vb-speak --engine say
echo "Hello" | vb-speak --dry-run  # Print filtered text, no audio

# Tests
pytest -v                  # 73 tests
```

---

## What Has NOT Been Built Yet

### Phase 2: PyPI Publish + Claude Code Plugin

**PyPI publish** is the immediate next step. The package is ready to ship but has not been uploaded. This requires a PyPI account and API token for the Tomorrow-You org.

**Claude Code plugin** packaging requires understanding the current plugin format (`plugin.json`, hook definitions). Research indicated a marketplace at `platform.claude.com/plugins/submit`, but the exact format may have evolved.

### Phase 3: MCP Server

An MCP server would let Cursor, Claude Desktop, and VS Code use voice-bridge without hook setup. The `src/voice_bridge/mcp/` directory was removed during code review cleanup (it was an empty placeholder). It needs to be rebuilt with actual MCP tool implementations.

An npm shim package (`npx ai-voice-bridge`) would bootstrap Python installation for users in the npm ecosystem.

### Phase 4: Polish + Marketing

Voice selection TUI, audio queue, Windows testing, and a launch blog post.

---

## Competitive Context

- **VoiceMode** (918 GitHub stars) -- MCP-based, requires OpenAI API key. No free engine.
- **AgentVibes** (133 stars) -- npm-based, OpenAI only.
- **Claude Code marketplace** -- Zero TTS plugins exist as of 2026-03-26. First-mover opportunity.
- **Voice Bridge differentiators:** free engines (edge-tts, kokoro, say, espeak), text safety filter, Claude Code native hook, 5 engines, setup wizard.
