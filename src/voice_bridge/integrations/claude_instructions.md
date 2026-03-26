# Voice Bridge -- Claude Code Instructions

Add the following to your project's `CLAUDE.md` or system instructions to enable voice output.

## CLAUDE.md Snippet

```markdown
## Voice Bridge (TTS)
- **System:** Voice Bridge multi-engine TTS. Docs: https://github.com/Tomorrow-You/voice-bridge
- **Two modes:** Single-turn (`speak` keyword prefix) and always-on (`voice-bridge on`).
- **NEVER** use `<speak>` tags unless the user's message starts with the keyword `speak`, OR voice-bridge is in always-on mode.
- When the user starts their message with "speak", wrap your ENTIRE text response in `<speak>...</speak>` tags.
- Strip the `speak` keyword from the prompt before processing.
- Inside `<speak>` tags, write naturally. Avoid markdown formatting, code blocks, and file paths.
- For code-heavy responses, put a natural language summary inside `<speak>` and code outside it.
```

## How It Works

1. User types `speak what's my status?`
2. Claude strips "speak" keyword, processes the query
3. Claude wraps response in `<speak>Your status is...</speak>` tags
4. Stop hook fires, extracts text from tags, pipes to `vb-speak`
5. TTS engine speaks the text aloud

In always-on mode (`voice-bridge on`), every response is spoken automatically without needing tags.
