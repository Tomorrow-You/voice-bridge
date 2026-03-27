"""Text filter for TTS safety and quality.

Strips code blocks, secrets, file paths, URLs, and markdown formatting
before text is spoken aloud. Prevents accidental disclosure of API keys
or unreadable content reaching the TTS engine.
"""
import re

# Patterns that should never be spoken aloud
SECRET_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',           # OpenAI/Anthropic API keys
    r'ghp_[a-zA-Z0-9]{36,}',          # GitHub personal access tokens
    r'gho_[a-zA-Z0-9]{36,}',          # GitHub OAuth tokens
    r'-----BEGIN\s+\w+\s+KEY-----',    # PEM private keys
    r'AKIA[0-9A-Z]{16}',              # AWS access key IDs
    r'[a-f0-9]{64}',                   # Hex secrets (64+ chars)
]

# Absolute file paths (Unix)
PATH_PATTERN = re.compile(r'/(?:Users|home|tmp|var|etc|opt|usr|Library|System)/\S+')

# Windows file paths (C:\Users\..., D:\Program Files\...)
WIN_PATH_PATTERN = re.compile(r'[A-Z]:\\(?:Users|Windows|Program Files|ProgramData|AppData)\S*', re.IGNORECASE)

# URLs
URL_PATTERN = re.compile(r'https?://\S+')

# Markdown table rows
TABLE_PATTERN = re.compile(r'^\s*\|.*\|\s*$', re.MULTILINE)
TABLE_DIVIDER = re.compile(r'^\s*\|[\s\-:|]+\|\s*$', re.MULTILINE)

MAX_TTS_CHARS = 4000


def filter_for_tts(text: str) -> str:
    """Filter text to remove content unsuitable for TTS."""
    # Strip markdown code blocks (```...```)
    text = re.sub(r'```[\s\S]*?```', '', text)

    # Strip inline code (`...`)
    text = re.sub(r'`[^`]+`', '', text)

    # Strip secret patterns
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, '[redacted]', text)

    # Strip URLs
    text = URL_PATTERN.sub('', text)

    # Strip absolute file paths (Unix and Windows)
    text = PATH_PATTERN.sub('', text)
    text = WIN_PATH_PATTERN.sub('', text)

    # Strip markdown tables
    text = TABLE_DIVIDER.sub('', text)
    text = TABLE_PATTERN.sub('', text)

    # Strip markdown headers (keep the text, remove #)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Strip markdown bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)

    # Clean up list markers (keep text, remove bullets)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Truncate at sentence boundary
    if len(text) > MAX_TTS_CHARS:
        truncated = text[:MAX_TTS_CHARS]
        last_period = truncated.rfind('. ')
        if last_period > MAX_TTS_CHARS // 2:
            text = truncated[:last_period + 1]
        else:
            text = truncated

    return text.strip()
