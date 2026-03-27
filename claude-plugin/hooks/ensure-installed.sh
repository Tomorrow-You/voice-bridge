#!/usr/bin/env bash
# SessionStart hook: ensure voice-bridge is installed.
# Only installs on first run or if the package is missing.

set -euo pipefail

if python3 -c "import voice_bridge" 2>/dev/null; then
    exit 0
fi

# Install voice-bridge with edge-tts engine and MCP server support
echo '{"hookSpecificOutput":{"additionalContext":"[voice-bridge] Installing ai-voice-bridge[edge,mcp]..."}}' >&1
python3 -m pip install -q "ai-voice-bridge[edge,mcp]" 2>/dev/null || {
    echo '{"hookSpecificOutput":{"additionalContext":"[voice-bridge] Failed to install. Run: pip install ai-voice-bridge[edge,mcp]"}}' >&1
    exit 0
}
echo '{"hookSpecificOutput":{"additionalContext":"[voice-bridge] Installed successfully. Run `voice-bridge test` to verify audio."}}' >&1
