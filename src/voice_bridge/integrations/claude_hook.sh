#!/bin/bash
# Claude Code Stop hook: speaks Claude's response aloud.
# Two modes:
#   1. Single-turn: detects <speak>...</speak> tags in response
#   2. Always-on: VOICE_BRIDGE_MODE=always in .state file
#
# Install: Add to .claude/settings.json as a Stop hook.
# See: https://github.com/Tomorrow-You/voice-bridge

set -euo pipefail

# Find Voice Bridge data directory
VB_HOME="${VOICE_BRIDGE_HOME:-$HOME/.voice-bridge}"
LOG="$VB_HOME/voice-bridge.log"

# Ensure log directory exists
mkdir -p "$VB_HOME"

# Source state file for mode
source "$VB_HOME/.state" 2>/dev/null || true
MODE="${VOICE_BRIDGE_MODE:-off}"
ENGINE="${VOICE_BRIDGE_ENGINE:-auto}"

# Read hook input from stdin into a temp file
TMPINPUT=$(mktemp)
cat > "$TMPINPUT"

# Extract text to speak based on mode
TEXT=$(python3 - "$TMPINPUT" "$MODE" << 'PYEOF'
import sys, json, re

input_file = sys.argv[1]
mode = sys.argv[2]

with open(input_file) as f:
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        sys.exit(1)

msg = data.get('last_assistant_message', '')
if not msg:
    sys.exit(1)

# Mode 1: Single-turn -- check for <speak> tags
speak_match = re.search(r'<speak>(.*?)</speak>', msg, re.DOTALL)
if speak_match:
    print(speak_match.group(1).strip()[:2000])
    sys.exit(0)

# Mode 2: Always-on -- speak entire response
if mode == 'always':
    print(msg[:2000])
    sys.exit(0)

# Neither mode triggered
sys.exit(1)
PYEOF
) || true

rm -f "$TMPINPUT"

if [[ -z "$TEXT" ]]; then
    exit 0
fi

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [hook] mode=$MODE engine=$ENGINE text_len=${#TEXT}" >> "$LOG"

# Speak in background so we don't block Claude Code
(
    echo "$TEXT" | vb-speak --engine "$ENGINE" --stream 2>>"$LOG" || \
    echo "$TEXT" | vb-speak --engine say --stream 2>>"$LOG" || true
) &

exit 0
