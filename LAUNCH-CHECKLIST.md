# Voice Bridge Launch Checklist

Step-by-step instructions for publishing voice-bridge to the world. Everything below requires human action.

---

## 1. Make GitHub Repo Public

The plugin marketplace, npm shim, and MCP registry all reference `https://github.com/Tomorrow-You/voice-bridge`. This must be accessible.

1. Go to https://github.com/Tomorrow-You/voice-bridge/settings
2. Scroll to "Danger Zone"
3. Click "Change visibility" → Public
4. Confirm

**Blocked until this is done:** plugin marketplace install, npm shim README links, MCP registry submission.

---

## 2. Revoke Old PyPI Token, Verify New One

You already created a project-scoped token. Confirm the old "Entire account" token is revoked:

1. Go to https://pypi.org/manage/account/token/
2. Verify only the `ai-voice-bridge`-scoped token exists
3. Delete any "Entire account" tokens

---

## 3. Publish npm Shim Package

This lets users run `npx ai-voice-bridge` to start the MCP server.

```bash
cd npm-package
npm login
npm publish
```

**Verify:**
```bash
npx ai-voice-bridge --help
```

(If `ai-voice-bridge` is taken on npm, rename in `package.json` before publishing.)

---

## 4. Install Plugin Locally (Test)

Test the Claude Code plugin before submitting to any marketplace:

```bash
claude --plugin-dir claude-plugin
```

Then in Claude Code:
- Type "speak hello" — response should be spoken aloud
- Run `voice-bridge status` — should show mode and engine
- Check that the MCP `speak` tool appears in tool list

---

## 5. Add Self-Hosted Marketplace (GitHub)

Once the repo is public, users can install the plugin directly from GitHub:

```bash
# Users run these two commands:
claude plugin marketplace add Tomorrow-You/voice-bridge
claude plugin install voice-bridge@Tomorrow-You/voice-bridge
```

Test this yourself first after making the repo public.

---

## 6. Submit to Official Claude Code Plugin Marketplace

1. Go to https://clau.de/plugin-directory-submission
2. Fill in:
   - **Plugin name:** voice-bridge
   - **Repository:** https://github.com/Tomorrow-You/voice-bridge
   - **Plugin path:** claude-plugin
   - **Description:** Give Claude Code a voice -- multi-engine TTS that speaks responses aloud. Free, local-first, 5 engines.
   - **Category:** productivity
   - **Author:** Tomorrow You LLC
3. Submit and wait for review

---

## 7. Submit to MCP Registry

1. Go to https://registry.modelcontextprotocol.io (or current URL)
2. Submit the npm package `ai-voice-bridge` (after step 3)
3. Also link the Python package: `pip install ai-voice-bridge[mcp]`

Include setup instructions for:
- Claude Desktop: `python3 -m voice_bridge.mcp.server`
- Claude Code: `claude mcp add voice-bridge -- python3 -m voice_bridge.mcp.server`
- Cursor: same config as Claude Desktop

---

## 8. Test MCP with Claude Desktop

After npm publish (step 3), add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Restart Claude Desktop. Ask it to "speak hello" using the speak tool.

---

## 9. Test MCP with Cursor

In Cursor Settings → MCP, add:

```json
{
  "voice-bridge": {
    "command": "python3",
    "args": ["-m", "voice_bridge.mcp.server"]
  }
}
```

Verify the speak tool works.

---

## 10. Blog Post / Launch

Write "I gave Claude Code a voice" for LinkedIn/Substack:
- 60-second demo GIF (asciinema → SVG or screen recording)
- "Zero API key" hook: edge-tts works free out of the box
- Link to GitHub + `pip install ai-voice-bridge[edge]`
- Position as builder/consultant, not job seeker

---

## 11. Version Bump to 0.2.0

After all the above is verified:

1. Update version in `pyproject.toml`, `npm-package/package.json`, `claude-plugin/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
2. Rebuild: `python -m build`
3. Upload: `twine upload -u __token__ -p YOUR_TOKEN dist/*`
4. npm: `cd npm-package && npm publish`
5. Tag: `git tag v0.2.0 && git push --tags`

---

## Order of Operations

```
1. Make repo public          (unblocks everything)
2. Revoke old PyPI token     (security hygiene)
3. npm publish               (unblocks MCP registry + Claude Desktop)
4. Test plugin locally       (verify before submitting)
5. Test self-hosted marketplace
6. Submit to official marketplace
7. Submit to MCP registry
8-9. Test with Claude Desktop + Cursor
10. Blog post
11. Version bump
```
