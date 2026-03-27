---
name: speak
description: Speak a response aloud using Voice Bridge TTS. Use when the user's message starts with "speak" or when they ask to hear something read aloud.
argument-hint: Optional text to speak
---

# Voice Bridge -- Speak Aloud

When the user's message starts with "speak" (case-insensitive), wrap your **entire response** in `<speak>...</speak>` tags.

## Rules

1. **ONLY** use `<speak>` tags when the user explicitly starts their message with "speak"
2. Strip the "speak" keyword before processing the actual request
3. Inside `<speak>` tags, write **naturally for listening**:
   - No markdown formatting (no `**bold**`, `# headers`, `- lists`)
   - No code blocks or inline code
   - No file paths or URLs
   - No tables
   - Spell out abbreviations on first use
4. Keep spoken responses concise -- under 2000 characters
5. If the user just says "speak" with no follow-up, speak a brief status or greeting

## Examples

User: "speak what does this function do?"
Response: `<speak>This function takes a user ID and returns their profile data from the database. It first checks the cache, and if there's a miss, it queries the users table and caches the result for five minutes.</speak>`

User: "speak summarize the changes"
Response: `<speak>The main changes are: first, I added a new authentication middleware that checks JWT tokens on every request. Second, I updated the user model to include an email verification field. And third, I added rate limiting to the login endpoint to prevent brute force attacks.</speak>`

User: "what does this function do?" (no "speak" prefix)
Response: Normal markdown response, NO `<speak>` tags.
