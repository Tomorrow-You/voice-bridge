# Voice Bridge Roadmap

## Quick Reference

| Item | Value |
|------|-------|
| **PyPI name** | `ai-voice-bridge` |
| **npm name (future)** | `ai-voice-bridge` |
| **GitHub** | https://github.com/Tomorrow-You/voice-bridge |
| **Local clone** | `/Users/maxhome/TOMORROWME-REPOS/voice-bridge` |
| **Python import** | `voice_bridge` |
| **CLI commands** | `voice-bridge`, `vb-speak` |
| **License** | MIT (edge-tts optional extra is GPL-3.0) |
| **Python** | >=3.10 |
| **Current version** | 0.1.0 |
| **Tests** | 73 (69 pass, 4 skip) |
| **CI** | GitHub Actions, macOS + Ubuntu, Python 3.10-3.13 |

---

## Completed

### Phase 0+1: MVP (2026-03-26)

- [x] Restructured from private `~/.voice-bridge/` to clean open-source layout
- [x] Scrubbed all personal data
- [x] 5 TTS engines: edge-tts (free), ElevenLabs (paid), Kokoro (local), macOS say, espeak-ng
- [x] Engine auto-detection with graceful fallback
- [x] Shared sentence splitter (DRY across all engines)
- [x] Text safety filter (code, secrets, Unix/Windows paths, URLs, markdown)
- [x] Claude Code Stop hook integration
- [x] Interactive setup wizard
- [x] Lazy loading (no side effects on import)
- [x] Shell-safe state file with quoting
- [x] py.typed marker for type checkers
- [x] 73 tests, GitHub Actions CI
- [x] README, CONTRIBUTING, LICENSE
- [x] Full code review: all 23 issues (4 critical, 7 important, 12 suggestions) fixed

---

## Phase 2: PyPI Publish (do this first)

### Step 2.1: Create PyPI Account and API Token

1. Go to https://pypi.org/account/register/
2. Create account under the Tomorrow You org email (or personal)
3. Enable 2FA (required for new accounts)
4. Go to https://pypi.org/manage/account/token/
5. Create an API token scoped to the `ai-voice-bridge` project (or all projects for first upload)
6. Save the token -- it starts with `pypi-` and is shown only once

### Step 2.2: Test Build Locally

```bash
cd /Users/maxhome/TOMORROWME-REPOS/voice-bridge
source .venv/bin/activate
pip install build twine

# Build the wheel and sdist
python -m build

# Check the built packages for issues
twine check dist/*

# Verify the wheel contents look right
unzip -l dist/ai_voice_bridge-0.1.0-py3-none-any.whl
```

Expected wheel contents should include `voice_bridge/` package with all `.py` files, `py.typed`, and `integrations/claude_hook.sh`.

### Step 2.3: Upload to Test PyPI First

```bash
# Upload to test.pypi.org for a dry run
twine upload --repository testpypi dist/*
# Username: __token__
# Password: your-test-pypi-token

# Verify it works
pip install --index-url https://test.pypi.org/simple/ ai-voice-bridge
voice-bridge --help
```

### Step 2.4: Upload to Real PyPI

```bash
twine upload dist/*
# Username: __token__
# Password: pypi-your-real-token

# Verify
pip install ai-voice-bridge
voice-bridge --help
```

### Step 2.5: Verify End-to-End Install

On a clean machine or in a fresh venv:

```bash
python3 -m venv /tmp/vb-test && source /tmp/vb-test/bin/activate
pip install ai-voice-bridge[edge]
voice-bridge test       # Should speak aloud
voice-bridge engines    # Should show edge-tts as installed
voice-bridge setup      # Should walk through interactive config
```

### Step 2.6: Add PyPI Badge to README

After the first successful publish, add to the top of `README.md`:

```markdown
[![PyPI](https://img.shields.io/pypi/v/ai-voice-bridge)](https://pypi.org/project/ai-voice-bridge/)
[![CI](https://github.com/Tomorrow-You/voice-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/Tomorrow-You/voice-bridge/actions)
```

---

## Phase 3: Claude Code Plugin

### Background

Claude Code plugins bundle hooks, skills, and MCP servers into an installable package. The plugin marketplace is at `platform.claude.com/plugins/submit`. A plugin can also be hosted on a custom GitHub-based marketplace.

### Step 3.1: Research Current Plugin Format

The plugin format may have evolved. Before building:

```bash
# Check Claude Code docs for latest plugin format
claude /help plugins    # or check Anthropic docs

# Look at existing plugins for format reference
gh search repos "claude code plugin" --sort stars --limit 10
```

Key things to confirm:
- Is the format still `plugin.json` + hooks/ + skills/?
- Can plugins declare pip dependencies that auto-install?
- Is the marketplace at `platform.claude.com/plugins/submit` still active?

### Step 3.2: Create Plugin Package

Create `claude-plugin/` directory in the repo:

```
claude-plugin/
  plugin.json          # Plugin metadata, hook definitions
  hooks/
    stop.sh            # Symlink or copy of integrations/claude_hook.sh
  skills/
    voice-bridge.md    # SKILL.md with <speak> tag instructions for Claude
  setup.sh             # Post-install: pip install ai-voice-bridge && voice-bridge setup
```

`plugin.json` should declare:
- Name: "voice-bridge"
- Description: "Give Claude Code a voice -- multi-engine TTS"
- Author: "Tomorrow You LLC"
- A Stop hook that runs `claude_hook.sh`
- A dependency on `ai-voice-bridge` pip package

### Step 3.3: Test Locally

```bash
# Install from local directory
claude plugin install ./claude-plugin

# Verify hook fires
voice-bridge on
# Ask Claude something -- response should be spoken aloud
voice-bridge off
```

### Step 3.4: Submit to Marketplace

1. Go to `platform.claude.com/plugins/submit` (or current URL)
2. Fill in metadata, upload package
3. Wait for review/approval

### Step 3.5: Create GitHub-Hosted Marketplace (Backup)

If the official marketplace is slow or the format has changed, create a custom marketplace:

1. Create a `marketplace.json` at the repo root:
   ```json
   {
     "plugins": [{
       "name": "voice-bridge",
       "version": "0.1.0",
       "source": "github",
       "repository": "Tomorrow-You/voice-bridge",
       "path": "claude-plugin"
     }]
   }
   ```
2. Users install with: `claude plugin install voice-bridge@Tomorrow-You/voice-bridge`

---

## Phase 4: MCP Server

### Background

An MCP (Model Context Protocol) server lets any MCP-compatible tool (Claude Desktop, Cursor, VS Code Copilot, Windsurf) use voice-bridge. The server exposes `speak`, `set_engine`, `get_status`, and `list_voices` as MCP tools.

### Step 4.1: Add MCP Extra to pyproject.toml

```toml
[project.optional-dependencies]
mcp = ["mcp>=1.0.0"]
```

Also add to `[project.scripts]`:
```toml
voice-bridge-mcp = "voice_bridge.mcp.server:main"
```

### Step 4.2: Implement MCP Server

Create `src/voice_bridge/mcp/__init__.py` and `src/voice_bridge/mcp/server.py`.

The server should expose these MCP tools:
- `speak(text: str, engine?: str)` -- speak text aloud
- `set_engine(name: str)` -- switch TTS engine
- `get_status()` -- return current mode, engine, available engines
- `list_voices(engine?: str)` -- list available voices for an engine

Use the `mcp` Python SDK:
```python
from mcp.server import Server
from mcp.types import Tool, TextContent
```

The server reads from stdin and writes to stdout (stdio transport), which is the standard for MCP.

### Step 4.3: Create npm Shim Package

Create a small npm package that bootstraps the Python server:

```bash
mkdir npm-package && cd npm-package
npm init -y
# name: ai-voice-bridge
```

The `bin/ai-voice-bridge-mcp.js` script should:
1. Check for Python 3.10+ (`python3 --version`)
2. Check if `voice_bridge` is installed (`python3 -c "import voice_bridge"`)
3. If not, run `pip install ai-voice-bridge[mcp]`
4. Start `python3 -m voice_bridge.mcp.server` connected to stdio

### Step 4.4: Test with Claude Desktop

Add to Claude Desktop's `claude_desktop_config.json`:
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

Or after npm publish:
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

### Step 4.5: Test with Cursor

In Cursor settings, add the MCP server under the MCP section. Same config format as Claude Desktop.

### Step 4.6: Submit to MCP Registry

1. Go to https://registry.modelcontextprotocol.io (or current URL)
2. Submit the npm package or the Python package
3. Also submit to Anthropic's registry if separate: `api.anthropic.com/mcp-registry`

### Step 4.7: Publish npm Package

```bash
cd npm-package
npm login
npm publish
```

### Step 4.8: Update README

Add an "MCP Server" section to README with setup instructions for each tool (Claude Desktop, Cursor, VS Code).

---

## Phase 5: Polish

### Step 5.1: Voice Selection TUI

Add `voice-bridge voices [engine]` command that:
- Lists available voices with descriptions
- For edge-tts: runs `edge-tts --list-voices` and displays formatted output
- For elevenlabs: calls the voices API endpoint
- For kokoro: lists the bundled voice names
- Optionally: preview a voice with `voice-bridge voices --preview <name>`

### Step 5.2: Audio Queue

Add sentence queueing so that:
- Multiple sentences can be queued while the first plays
- `Ctrl+C` or `voice-bridge stop` cancels the queue
- A new `speak()` call cancels the current queue

### Step 5.3: Windows Testing

Set up a Windows CI runner (GitHub Actions `windows-latest`) and verify:
- edge-tts engine works with ffplay/mpv
- paths resolve to `%APPDATA%\voice-bridge\`
- espeak-ng works if installed via chocolatey
- Hook works in Windows terminals (PowerShell, cmd)

### Step 5.4: Blog Post / Launch

Write "I gave Claude Code a voice" for LinkedIn/Substack. Include:
- 60-second demo GIF (asciinema -> SVG or screen recording)
- "Zero API key" hook: edge-tts works free out of the box
- Link to GitHub + pip install command
- Position as builder/consultant, not job seeker

### Step 5.5: Version Bump

After all Phase 5 items, bump to v0.2.0 and publish updated package to PyPI.

---

## Future (v1.0)

These are stretch goals, not committed:

- STT (speech-to-text) via Whisper or Deepgram -- bidirectional voice conversations
- Unix socket daemon for persistent process (faster cold start)
- launchd/systemd service for always-on background daemon
- Custom engine plugins via Python entry points
- Rate limiting and usage tracking for cloud engines

---

## Architecture Decisions (Reference)

| Decision | Choice | Why |
|----------|--------|-----|
| Distribution | pip primary, plugin + MCP secondary | Core is Python. Plugin/MCP are thin wrappers. |
| Default engine | `auto` (edge-tts > say > espeak > kokoro > elevenlabs) | Free, zero-config out of box. |
| Hook vs MCP | Hook for Claude Code, MCP for others | Hook is automatic. MCP requires LLM to decide. |
| License | MIT core, edge-tts GPL opt-in | Max adoption. GPL is clearly opt-in. |
| State format | Shell-sourceable, double-quoted values | Hook `source`s the file directly. |
| Sentence splitting | Shared utility, all engines use it | DRY. Consistent behavior. |
| Import side effects | None (lazy logging, lazy dotenv) | Library-safe. No dirs created on import. |

## Competitive Landscape (Reference)

| Feature | Voice-Bridge | VoiceMode (918 stars) | AgentVibes (133 stars) |
|---------|-------------|----------------------|----------------------|
| Free engine (no API key) | edge-tts, Kokoro, say, espeak | No (requires OpenAI key) | No |
| Text safety filter | Yes (secrets, code, paths) | No | No |
| Claude Code native (Stop hook) | Yes | No (MCP only) | Partial |
| Multi-engine | 5 engines | 2 (OpenAI, Kokoro) | 1 (OpenAI) |
| Offline mode | Yes (Kokoro, say, espeak) | Partial (Kokoro) | No |
| Cross-platform | macOS + Linux + Windows | macOS + Linux | macOS |

**First-mover:** Zero TTS plugins exist in the Claude Code marketplace as of 2026-03-26.
