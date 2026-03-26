# Voice Bridge Roadmap

## Status

**Package:** `ai-voice-bridge` (PyPI) / `ai-voice-bridge` (npm, future)
**Repo:** https://github.com/Tomorrow-You/voice-bridge
**Local:** `/Users/maxhome/TOMORROWME-REPOS/voice-bridge`

---

## Architecture Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Distribution format | **pip package (primary) + Claude Code plugin + MCP server** | Core is Python. Plugin wraps it for Claude Code. MCP enables Cursor/Desktop/VS Code. |
| Default engine | **macOS `say` / Linux `espeak-ng` (zero-config) + edge-tts (recommended, free)** | Zero-config must produce sound without signup/keys. edge-tts requires user consent (GPL-3.0). |
| Hook vs MCP as primary | **Hook for Claude Code, MCP for other tools** | Hook is automatic (fires every response). MCP requires LLM to decide when to speak -- less reliable. |
| License | **MIT core.** edge-tts is optional extra (GPL-3.0). | MIT maximizes adoption. edge-tts is opt-in. |
| Python version | **>=3.10** (widen from original 3.12) | Adoption. Most systems have 3.10+. |

---

## Completed

### Phase 0: Scaffold + Phase 1: MVP (2026-03-26)
- [x] Restructured from `~/.voice-bridge/` private install to clean open-source layout
- [x] Scrubbed all personal data (voice IDs, paths, API keys)
- [x] Refactored `config.py` with `paths.py` for XDG-aware, cross-platform path resolution
- [x] Generalized `claude_hook.sh` to use dynamic Python import discovery
- [x] Implemented `edge_tts_engine.py` -- free Microsoft Neural TTS, 400+ voices, no API key
- [x] Implemented `espeak_engine.py` -- Linux fallback via espeak-ng
- [x] Implemented `engines.py` -- engine registry with graceful discovery of optional deps
- [x] Implemented `setup_wizard.py` -- interactive first-run config
- [x] 42 tests (38 pass, 4 skip for optional deps)
- [x] GitHub Actions CI on macOS + Ubuntu, Python 3.10-3.13
- [x] README with install instructions, engine comparison, Claude Code integration docs
- [x] Pushed to `Tomorrow-You/voice-bridge`
- [x] Renamed PyPI package to `ai-voice-bridge`

---

## Next Up

### Phase 2: Claude Code Plugin (target: ~1 week)
- [ ] Package `claude-plugin/` directory:
  - `plugin.json`: Stop hook definition, metadata
  - `SKILL.md`: `<speak>` tag instructions for Claude
  - `setup.sh`: `pip install ai-voice-bridge && voice-bridge setup`
- [ ] Test with `claude plugin install ./claude-plugin` locally
- [ ] Submit to Claude Code marketplace (platform.claude.com/plugins/submit)
- [ ] Also create GitHub-hosted marketplace for rapid iteration

### Phase 3: MCP Server (target: ~2 weeks)
- [ ] Implement `mcp/server.py`:
  - Tools: `speak(text, engine?)`, `set_engine(name)`, `get_status()`, `list_voices(engine?)`
  - Resources: current config, available engines
- [ ] Create npm shim: `npx ai-voice-bridge` (checks Python, pip installs, starts server)
- [ ] Test with Claude Desktop, Cursor, VS Code
- [ ] Submit to MCP registry
- [ ] Update README with MCP setup instructions for each tool

### Phase 4: Polish (target: ~1 month)
- [ ] Voice selection TUI (list voices with preview for each engine)
- [ ] Audio queue (skip current, cancel queue)
- [ ] Per-engine speed/pitch controls
- [ ] Windows testing and support
- [ ] Blog post: "I gave Claude Code a voice" (consulting visibility play)
- [ ] Publish to PyPI

### Future (v1.0)
- [ ] STT (speech-to-text) via Whisper/Deepgram
- [ ] Bidirectional voice conversations
- [ ] Unix socket daemon for persistent process
- [ ] launchd/systemd service registration
- [ ] Plugin ecosystem (custom engines via entry points)

---

## Competitive Landscape

| Feature | Voice-Bridge | VoiceMode (918 stars) | AgentVibes (133 stars) |
|---------|-------------|----------------------|----------------------|
| Free engine (no API key) | edge-tts, Kokoro, say, espeak | No (requires OpenAI key) | No |
| Text safety filter | Yes (secrets, code, paths) | No | No |
| Claude Code native (Stop hook) | Yes | No (MCP only) | Partial |
| Multi-engine | 5 engines | 2 (OpenAI, Kokoro) | 1 (OpenAI) |
| Offline mode | Yes (Kokoro, say, espeak) | Partial (Kokoro) | No |
| Cross-platform | macOS + Linux + Windows | macOS + Linux | macOS |
| Setup wizard | Yes | No | Partial |

**Positioning:** "Give your AI coding assistant a voice. Free, local-first, multi-engine TTS -- in 60 seconds."

**Key differentiator:** Zero TTS plugins exist in the Claude Code marketplace. First-mover advantage.
