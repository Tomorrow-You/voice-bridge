#!/usr/bin/env bash
# Claude Code Stop hook: speaks Claude's response aloud via voice-bridge.
#
# Two modes:
#   1. Single-turn: detects <speak>...</speak> tags in response
#   2. Always-on: VOICE_BRIDGE_MODE=always in .state file
#
# Reads JSON from stdin (provided by Claude Code Stop hook).

set -euo pipefail

# Check voice-bridge is available
command -v vb-speak >/dev/null 2>&1 || exit 0

# Read state
VB_HOME="${VOICE_BRIDGE_HOME:-$HOME/.voice-bridge}"
if [ -f "$VB_HOME/.state" ]; then
    MODE=$(python3 -c "
from voice_bridge.state import read_state_value
print(read_state_value('VOICE_BRIDGE_MODE', 'off'))
" 2>/dev/null) || MODE="off"
    ENGINE=$(python3 -c "
from voice_bridge.state import read_state_value
print(read_state_value('VOICE_BRIDGE_ENGINE', 'auto'))
" 2>/dev/null) || ENGINE="auto"
else
    MODE="off"
    ENGINE="auto"
fi

# Read hook input from stdin
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

# Speak in background so we don't block Claude Code
(
    echo "$TEXT" | vb-speak --engine "$ENGINE" --stream 2>/dev/null || \
    echo "$TEXT" | vb-speak --engine say --stream 2>/dev/null || true
) &

exit 0
